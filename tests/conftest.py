import os
import sys
import asyncio
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.pool import NullPool
import redis.asyncio as aioredis

from dotenv import load_dotenv
load_dotenv(".env.test", override=True)

# Windows: asyncpg needs SelectorEventLoop
if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

from app.main import app
from app.db.base import Base
from app.db.session import get_session
import app.core.redis as redis_module

TEST_DATABASE_URL = os.environ["DATABASE_URL"]
TEST_REDIS_URL = os.environ["REDIS_URL"]


def make_engine():
    return create_async_engine(TEST_DATABASE_URL, poolclass=NullPool, echo=False)


def make_redis():
    return aioredis.from_url(TEST_REDIS_URL, encoding="utf-8", decode_responses=True)


# ---------------------------------------------------------------------------
# Create tables once at session start, drop at session end
# ---------------------------------------------------------------------------

@pytest_asyncio.fixture(scope="session", autouse=True)
async def setup_database():
    engine = make_engine()
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
    await engine.dispose()
    yield
    engine = make_engine()
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()


# ---------------------------------------------------------------------------
# Per-test: truncate all tables + flush Redis
# ---------------------------------------------------------------------------

@pytest_asyncio.fixture(autouse=True)
async def reset_state():
    yield
    # Clean DB
    engine = make_engine()
    async with engine.begin() as conn:
        for table in reversed(Base.metadata.sorted_tables):
            await conn.execute(table.delete())
    await engine.dispose()
    # Clean Redis
    r = make_redis()
    await r.flushdb()
    await r.aclose()


# ---------------------------------------------------------------------------
# Per-test DB session
# ---------------------------------------------------------------------------

@pytest_asyncio.fixture
async def db_session() -> AsyncSession:
    engine = make_engine()
    session_factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with session_factory() as session:
        yield session
    await engine.dispose()


# ---------------------------------------------------------------------------
# Per-test Redis — patches the app's redis_client for this test
# ---------------------------------------------------------------------------

@pytest_asyncio.fixture(autouse=True)
async def patch_redis():
    r = make_redis()
    await r.flushdb()
    # Patch the module-level client so the app uses our fresh instance
    original = redis_module.redis_client
    redis_module.redis_client = r
    yield r
    redis_module.redis_client = original
    await r.aclose()


# ---------------------------------------------------------------------------
# HTTP client
# ---------------------------------------------------------------------------

@pytest_asyncio.fixture
async def client(db_session: AsyncSession) -> AsyncClient:
    async def override_get_session():
        yield db_session

    app.dependency_overrides[get_session] = override_get_session

    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as ac:
        yield ac

    app.dependency_overrides.clear()