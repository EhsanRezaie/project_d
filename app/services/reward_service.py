from datetime import date, datetime, timedelta
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.config import settings
from app.models.user import User
from app.models.daily_limit import DailyLimit
from app.models.subscription import Subscription


class RewardService:
    """Handles daily limits, ad rewards, and premium bonuses."""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def get_or_create_daily_limit(self, user_id: UUID, target_date: date) -> DailyLimit:
        """Get or create daily limit record for a user."""
        result = await self.db.execute(
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
            self.db.add(daily_limit)
            await self.db.flush()
        
        return daily_limit
    
    async def get_remaining_likes(self, user: User) -> int:
        """Get remaining likes for today. Returns -1 for unlimited."""
        if user.is_premium:
            return -1
        
        today = date.today()
        daily_limit = await self.get_or_create_daily_limit(user.id, today)
        
        available = settings.FREE_USER_DAILY_LIKES + daily_limit.ad_likes_bonus - daily_limit.likes_used
        return max(0, available)
    
    async def get_remaining_chats(self, user: User) -> int:
        """Get remaining new chats for today. Returns -1 for unlimited."""
        if user.is_premium:
            return -1
        
        today = date.today()
        daily_limit = await self.get_or_create_daily_limit(user.id, today)
        
        available = settings.FREE_USER_DAILY_CHATS + daily_limit.ad_chats_bonus - daily_limit.chats_used
        return max(0, available)
    
    async def consume_like(self, user: User) -> bool:
        """Consume one like. Returns True if successful."""
        if user.is_premium:
            return True
        
        remaining = await self.get_remaining_likes(user)
        if remaining <= 0:
            return False
        
        today = date.today()
        daily_limit = await self.get_or_create_daily_limit(user.id, today)
        daily_limit.likes_used += 1
        await self.db.commit()
        
        return True
    
    async def consume_chat(self, user: User) -> bool:
        """Consume one new chat. Returns True if successful."""
        if user.is_premium:
            return True
        
        remaining = await self.get_remaining_chats(user)
        if remaining <= 0:
            return False
        
        today = date.today()
        daily_limit = await self.get_or_create_daily_limit(user.id, today)
        daily_limit.chats_used += 1
        await self.db.commit()
        
        return True
    
    async def claim_ad_reward(self, user: User) -> dict:
        """
        Claim reward for watching an ad.
        Returns: {'success': bool, 'likes_added': int, 'chats_added': int, 'message': str}
        """
        today = date.today()
        daily_limit = await self.get_or_create_daily_limit(user.id, today)
        
        # Calculate how many ads already watched today
        current_ad_count = daily_limit.ad_likes_bonus // settings.AD_REWARD_LIKES_BONUS
        
        if current_ad_count >= settings.MAX_AD_REWARDS_PER_DAY:
            return {
                'success': False,
                'likes_added': 0,
                'chats_added': 0,
                'message': f'Daily ad limit reached ({settings.MAX_AD_REWARDS_PER_DAY} ads per day)',
                'ads_watched_today': current_ad_count,
                'max_ads_per_day': settings.MAX_AD_REWARDS_PER_DAY
            }
        
        # Add bonuses
        daily_limit.ad_likes_bonus += settings.AD_REWARD_LIKES_BONUS
        daily_limit.ad_chats_bonus += settings.AD_REWARD_CHATS_BONUS
        await self.db.commit()
        
        return {
            'success': True,
            'likes_added': settings.AD_REWARD_LIKES_BONUS,
            'chats_added': settings.AD_REWARD_CHATS_BONUS,
            'message': f'You gained +{settings.AD_REWARD_LIKES_BONUS} likes and +{settings.AD_REWARD_CHATS_BONUS} new chats for today!',
            'ads_watched_today': current_ad_count + 1,
            'max_ads_per_day': settings.MAX_AD_REWARDS_PER_DAY
        }
    
    async def get_daily_stats(self, user: User) -> dict:
        """Get complete daily stats for user."""
        today = date.today()
        daily_limit = await self.get_or_create_daily_limit(user.id, today)
        
        if user.is_premium:
            return {
                'is_premium': True,
                'premium_expires_at': user.premium_until.isoformat() if user.premium_until else None,
                'likes_used_today': daily_limit.likes_used,
                'likes_remaining_today': -1,
                'chats_used_today': daily_limit.chats_used,
                'chats_remaining_today': -1,
                'ads_watched_today': daily_limit.ad_likes_bonus // settings.AD_REWARD_LIKES_BONUS,
                'max_ads_per_day': settings.MAX_AD_REWARDS_PER_DAY,
                'daily_likes_limit': -1,
                'daily_chats_limit': -1,
                'ad_reward_likes_bonus': settings.AD_REWARD_LIKES_BONUS,  # ADD THIS
                'ad_reward_chats_bonus': settings.AD_REWARD_CHATS_BONUS,  # ADD THIS
            }
        
        likes_limit = settings.FREE_USER_DAILY_LIKES + daily_limit.ad_likes_bonus
        chats_limit = settings.FREE_USER_DAILY_CHATS + daily_limit.ad_chats_bonus
        
        return {
            'is_premium': False,
            'premium_expires_at': None,
            'likes_used_today': daily_limit.likes_used,
            'likes_remaining_today': max(0, likes_limit - daily_limit.likes_used),
            'chats_used_today': daily_limit.chats_used,
            'chats_remaining_today': max(0, chats_limit - daily_limit.chats_used),
            'ads_watched_today': daily_limit.ad_likes_bonus // settings.AD_REWARD_LIKES_BONUS,
            'max_ads_per_day': settings.MAX_AD_REWARDS_PER_DAY,
            'daily_likes_limit': likes_limit,
            'daily_chats_limit': chats_limit,
            'ad_reward_likes_bonus': settings.AD_REWARD_LIKES_BONUS,  # ADD THIS
            'ad_reward_chats_bonus': settings.AD_REWARD_CHATS_BONUS,  # ADD THIS
        }
    
    async def grant_premium_days(self, user: User, days: int, source: str, payment_id: str = None):
        """Grant premium days to user and create subscription record."""
        now = datetime.utcnow()
        
        # Calculate new expiry
        if user.premium_until is None or user.premium_until < now:
            user.premium_until = now + timedelta(days=days)
        else:
            user.premium_until = user.premium_until + timedelta(days=days)
        
        # Create subscription record
        subscription = Subscription(
            user_id=user.id,
            plan=f"{days}_days",
            status="active",
            started_at=now,
            expires_at=user.premium_until,
            source=source,
            payment_id=payment_id,
        )
        self.db.add(subscription)
        await self.db.commit()
        
        return user.premium_until