"""
Seed 1000 dummy users from app/db/seed_data/dummy_users.json.

Usage:
    python -m app.db.scripts.seed_dummy_users

Re-run safe — existing test%@test.com users are deleted first.
Password for all dummies is ``12345678`` (hashed at runtime).
"""

import asyncio
import json
import logging
import uuid as uuid_lib
from pathlib import Path

from datetime import date
from sqlalchemy import delete, select

from app.core.security import hash_password
from app.db.session import AsyncSessionLocal
from app.models.photo import Photo
from app.models.user import User
from app.models.user_interest import UserInterest
from app.models.user_profile import UserProfile
from app.models.user_settings import UserSettings

logger = logging.getLogger(__name__)

SEED_FILE = Path(__file__).parent.parent / "seed_data" / "dummy_users.json"

PASSWORD = "12345678"


def load_seed_data() -> dict:
    if not SEED_FILE.exists():
        raise FileNotFoundError(f"Seed file not found: {SEED_FILE}")
    with open(SEED_FILE, encoding="utf-8") as f:
        data = json.load(f)
    for key in ("users", "profiles", "settings", "photos"):
        if key not in data:
            raise ValueError(f"Missing required key '{key}' in {SEED_FILE}")
    return data


async def seed_dummy_users() -> None:
    data = load_seed_data()
    users_data = data["users"]
    profiles_data = data["profiles"]
    settings_data = data["settings"]
    photos_data = data["photos"]

    print(f"📦  Loaded {len(users_data)} dummy users from seed file\n")

    password_hash = hash_password(PASSWORD)

    async with AsyncSessionLocal() as session:
        existing_ids = (
            await session.execute(
                select(User.id).where(User.email.like("%@test.com"))
            )
        ).scalars().all()
        if existing_ids:
            print(f"🧹  Removing {len(existing_ids)} existing test@test.com users …")
            await session.execute(delete(Photo).where(Photo.user_id.in_(existing_ids)))
            await session.execute(delete(UserInterest).where(UserInterest.user_id.in_(existing_ids)))
            await session.execute(delete(UserSettings).where(UserSettings.user_id.in_(existing_ids)))
            await session.execute(delete(UserProfile).where(UserProfile.user_id.in_(existing_ids)))
            await session.execute(delete(User).where(User.id.in_(existing_ids)))
            await session.commit()

        batch_size = 100

        for i, u in enumerate(users_data):
            user = User(
                id=uuid_lib.UUID(u["id"]),
                email=u["email"],
                password_hash=password_hash,
                is_active=True,
                phone_verified=False,
                registration_status="completed",
            )
            session.add(user)
            if (i + 1) % batch_size == 0:
                await session.commit()

        await session.commit()
        print(f"   ✅  {len(users_data)} users inserted")

        for p in profiles_data:
            profile = UserProfile(
                user_id=uuid_lib.UUID(p["user_id"]),
                name=p["name"],
                birth_date=date.fromisoformat(p["birth_date"]),
                gender=p["gender"],
                sexual_orientation=p["sexual_orientation"],
                bio=p["bio"],
                height=p["height"],
                weight=p["weight"],
                body_type=p["body_type"],
                relationship_status=p["relationship_status"],
                living_situation=p["living_situation"],
                children_status=p["children_status"],
                smoking=p["smoking"],
                drinking=p["drinking"],
                languages=p["languages"],
                education=p["education"],
                workplace=p["workplace"],
                religion=p["religion"],
                ethnicity=p["ethnicity"],
                political_orientation=p["political_orientation"],
                lat=p["lat"],
                lng=p["lng"],
                country=p["country"],
                province=p["province"],
                city=p["city"],
                is_verified=p["is_verified"],
                premium_until=p["premium_until"],
            )
            session.add(profile)

        await session.commit()
        print(f"   ✅  {len(profiles_data)} profiles inserted")

        for s in settings_data:
            settings = UserSettings(
                user_id=uuid_lib.UUID(s["user_id"]),
                hide_last_seen=s["hide_last_seen"],
                hide_online_status=s["hide_online_status"],
                push_enabled=s["push_enabled"],
                like_notifications=s["like_notifications"],
                match_notifications=s["match_notifications"],
                message_notifications=s["message_notifications"],
                language=s["language"],
                dark_mode=s["dark_mode"],
            )
            session.add(settings)

        await session.commit()
        print(f"   ✅  {len(settings_data)} settings inserted")

        for ph in photos_data:
            photo = Photo(
                user_id=uuid_lib.UUID(ph["user_id"]),
                url=ph["url"],
                order=ph["order"],
                is_main=ph["is_main"],
                status=ph["status"],
                reject_reason=ph["reject_reason"],
                face_verified=ph["face_verified"],
                crop=None,
            )
            session.add(photo)

        await session.commit()
        print(f"   ✅  {len(photos_data)} photos inserted")

    print(f"\n🎉  Done! {len(users_data)} dummy users in the database.")
    print(f"    Email range:  test1@test.com … test{len(users_data)}@test.com")
    print(f"    Password:     {PASSWORD}")


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    asyncio.run(seed_dummy_users())


if __name__ == "__main__":
    main()
