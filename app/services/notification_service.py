from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.notification import Notification
from app.models.user import User


class NotificationService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(
        self,
        user_id: UUID,
        type: str,
        title: str,
        body: str = None,
        data: dict = None
    ) -> Notification:
        """Create a notification for a user"""
        notification = Notification(
            user_id=user_id,
            type=type,
            title=title,
            body=body,
            data=data,
            is_read=False,
        )
        self.db.add(notification)
        await self.db.flush()
        return notification

    async def notify_like(
        self,
        liker_id: UUID,
        liked_user_id: UUID,
        liker_name: str,
        liker_age: int
    ):
        """Send like notification (only if recipient is premium)"""
        from sqlalchemy import select
        from app.models.user import User

        result = await self.db.execute(select(User).where(User.id == liked_user_id))
        liked_user = result.scalar_one_or_none()

        """Send like notification to the recipient (all users get like notifications)"""

        await self.create(
            user_id=liked_user_id,
            type="like",
            title="Someone liked you!",
            body=f"{liker_name} (age {liker_age}) liked your profile",
            data={"user_id": str(liker_id)}
        )

    async def notify_match(self, user1_id: UUID, user2_id: UUID, match_id: UUID):
        """Send match notification to both users"""
        # Get both users
        from sqlalchemy import select
        from app.models.user import User

        result1 = await self.db.execute(select(User).where(User.id == user1_id))
        user1 = result1.scalar_one_or_none()
        result2 = await self.db.execute(select(User).where(User.id == user2_id))
        user2 = result2.scalar_one_or_none()

        if user1:
            await self.create(
                user_id=user1_id,
                type="match",
                title="It's a match!",
                body=f"You matched with {user2.name}! Start chatting now.",
                data={"match_id": str(match_id), "user_id": str(user2_id)}
            )

        if user2:
            await self.create(
                user_id=user2_id,
                type="match",
                title="It's a match!",
                body=f"You matched with {user1.name}! Start chatting now.",
                data={"match_id": str(match_id), "user_id": str(user1_id)}
            )

    async def notify_message(self, receiver_id: UUID, sender_name: str, match_id: UUID):
        """Send message notification when recipient is offline"""
        await self.create(
            user_id=receiver_id,
            type="message",
            title="New message",
            body=f"{sender_name} sent you a message",
            data={"match_id": str(match_id)}
        )