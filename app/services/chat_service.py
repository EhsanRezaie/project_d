from datetime import date, datetime, timedelta
from uuid import UUID
from typing import Optional, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, or_, update

from app.core.config import settings
from app.services.reward_service import RewardService
from app.models.user import User
from app.models.match import Match
from app.models.message import Message
from app.models.daily_limit import DailyLimit
from app.core.logging import get_logger

logger = get_logger("chat_service")


async def get_or_create_daily_limit(
    session: AsyncSession,
    user_id: UUID,
    target_date: date
) -> DailyLimit:
    """Get or create daily limit record for a user"""
    result = await session.execute(
        select(DailyLimit).where(
            DailyLimit.user_id == user_id,
            DailyLimit.date == target_date
        )
    )
    daily_limit = result.scalar_one_or_none()

    if not daily_limit:
        daily_limit = DailyLimit(
            user_id=user_id,
            date=target_date,
            likes_used=0,
            chats_used=0,
            ad_likes_bonus=0,
            ad_chats_bonus=0,
        )
        session.add(daily_limit)
        await session.flush()

    return daily_limit


async def can_start_new_chat(
    session: AsyncSession,
    user_id: UUID,
    target_user_id: UUID,
    is_premium: bool
) -> Tuple[bool, Optional[str], Optional[DailyLimit]]:
    """
    Check if user can start a new chat with target user.
    Returns: (can_start, reason, daily_limit)
    """
    # Premium users have no limits
    if is_premium:
        return True, None, None

    # Check if they already have a chat (not a new chat)
    existing = await session.execute(
        select(Message).where(
            or_(
                and_(Message.sender_id == user_id, Message.receiver_id == target_user_id),
                and_(Message.sender_id == target_user_id, Message.receiver_id == user_id)
            )
        ).limit(1)
    )

    if existing.scalar_one_or_none():
        return True, None, None

    # This is a new chat - check daily limit using RewardService
    from app.models.user import User
    result = await session.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    
    if user:
        reward_service = RewardService(session)
        remaining = await reward_service.get_remaining_chats(user)
        
        if remaining <= 0:
            return False, f"Daily new chat limit reached ({settings.FREE_USER_DAILY_CHATS} per day). Watch an ad or upgrade to premium.", None

    return True, None, None


async def check_unmatched_message_limit(
    session: AsyncSession,
    sender_id: UUID,
    receiver_id: UUID,
    match_id: Optional[UUID]
) -> Tuple[bool, Optional[str], bool]:
    """
    Check if user can send message in unmatched chat.
    Returns: (can_send, reason, is_accepted)
    """
    if match_id:
        return True, None, True

    result = await session.execute(
        select(func.count(Message.id)).where(
            Message.sender_id == sender_id,
            Message.receiver_id == receiver_id,
            Message.match_id.is_(None),
            Message.is_deleted_for_all == False,
            Message.is_deleted_for_sender == False
        )
    )
    message_count = result.scalar() or 0

    result = await session.execute(
        select(Message.is_accepted).where(
            Message.sender_id == receiver_id,
            Message.receiver_id == sender_id,
            Message.match_id.is_(None),
            Message.is_accepted == True
        ).limit(1)
    )
    is_accepted_by_receiver = result.scalar_one_or_none() or False

    result = await session.execute(
        select(Message.is_accepted).where(
            Message.sender_id == sender_id,
            Message.receiver_id == receiver_id,
            Message.match_id.is_(None),
            Message.is_accepted == True
        ).limit(1)
    )
    is_accepted_by_sender = result.scalar_one_or_none() or False

    is_accepted = is_accepted_by_receiver or is_accepted_by_sender

    if is_accepted:
        return True, None, True

    if message_count >= 2:
        return False, "Recipient must accept the conversation before sending more messages. They have received 2 messages already.", False

    return True, None, False


async def accept_unmatched_chat(
    session: AsyncSession,
    match_id: Optional[UUID],
    other_user_id: UUID,
    current_user_id: UUID
) -> bool:
    """Accept an unmatched chat - updates ALL messages between the two users"""
    
    if match_id:
        await session.execute(
            update(Message)
            .where(Message.match_id == match_id)
            .values(is_accepted=True)
        )
    else:
        await session.execute(
            update(Message)
            .where(
                or_(
                    and_(
                        Message.sender_id == current_user_id,
                        Message.receiver_id == other_user_id
                    ),
                    and_(
                        Message.sender_id == other_user_id,
                        Message.receiver_id == current_user_id
                    )
                ),
                Message.match_id.is_(None)
            )
            .values(is_accepted=True)
        )

    await session.commit()
    return True


async def increment_new_chat_count(
    session: AsyncSession,
    user_id: UUID
) -> None:
    """Increment the new chats counter for a user using RewardService"""
    from app.models.user import User
    result = await session.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    
    if user:
        reward_service = RewardService(session)
        await reward_service.consume_chat(user)


async def mark_messages_as_delivered(
    session: AsyncSession,
    message_ids: list[UUID],
    user_id: UUID
) -> None:
    """Mark messages as delivered"""
    await session.execute(
        update(Message)
        .where(
            Message.id.in_(message_ids),
            Message.receiver_id == user_id,
            Message.is_delivered == False
        )
        .values(is_delivered=True, delivered_at=datetime.utcnow())
    )
    await session.commit()


async def mark_messages_as_read(
    session: AsyncSession,
    message_ids: list[UUID],
    user_id: UUID
) -> None:
    """Mark messages as read"""
    await session.execute(
        update(Message)
        .where(
            Message.id.in_(message_ids),
            Message.receiver_id == user_id,
            Message.is_read == False
        )
        .values(is_read=True, read_at=datetime.utcnow())
    )
    await session.commit()


async def delete_message(
    session: AsyncSession,
    message_id: UUID,
    user_id: UUID,
    delete_for: str
) -> Tuple[bool, Optional[str]]:
    """Delete a message. Returns: (success, error_message)"""
    result = await session.execute(
        select(Message).where(Message.id == message_id)
    )
    message = result.scalar_one_or_none()

    if not message:
        return False, "Message not found"

    if message.sender_id != user_id and message.receiver_id != user_id:
        return False, "Not authorized to delete this message"

    if delete_for == "everyone":
        if message.sender_id != user_id:
            return False, "Only the sender can delete for everyone"

        one_hour_ago = datetime.utcnow() - timedelta(hours=1)
        if message.sent_at < one_hour_ago:
            return False, "Cannot delete for everyone after 1 hour. Use delete for me instead."

        message.is_deleted_for_all = True
        message.deleted_at = datetime.utcnow()
        message.content = "[Message deleted]"
    else:
        if message.sender_id == user_id:
            message.is_deleted_for_sender = True
        else:
            message.is_deleted_for_receiver = True

    await session.commit()
    return True, None


async def forward_message(
    session: AsyncSession,
    message_id: UUID,
    target_match_id: UUID,
    user_id: UUID
) -> Tuple[Optional[Message], Optional[str]]:
    """Forward a message to another chat. Returns: (new_message, error_message)"""
    result = await session.execute(
        select(Message).where(Message.id == message_id)
    )
    original = result.scalar_one_or_none()

    if not original:
        return None, "Message not found"

    if original.sender_id != user_id and original.receiver_id != user_id:
        return None, "Not authorized to forward this message"

    result = await session.execute(
        select(Match).where(Match.id == target_match_id, Match.is_active == True)
    )
    target_match = result.scalar_one_or_none()

    if not target_match:
        return None, "Target match not found"

    if target_match.user1_id != user_id and target_match.user2_id != user_id:
        return None, "Not part of target match"

    receiver_id = target_match.user2_id if target_match.user1_id == user_id else target_match.user1_id

    forwarded_content = f"📨 Forwarded: {original.content}" if original.content else "📨 Forwarded message"

    new_message = Message(
        match_id=target_match_id,
        sender_id=user_id,
        receiver_id=receiver_id,
        message_type=original.message_type,
        content=forwarded_content,
        media_url=original.media_url,
        media_duration=original.media_duration,
        is_sent=True,
        is_accepted=True,
    )

    session.add(new_message)
    await session.flush()

    return new_message, None