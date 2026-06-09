import os
import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession

# Load .env.test BEFORE importing anything from app
os.environ["ENV_FILE"] = ".env.test"
from dotenv import load_dotenv
load_dotenv(".env.test", override=True)

from app.main import app
from app.db.base import Base
from app.db.session import get_session
from app.core.redis import redis_client

# ---------------------------------------------------------------------------
# Engine pointed at test DB
# ---------------------------------------------------------------------------

TEST_DATABASE_URL = os.environ["DATABASE_URL"]

test_engine = create_async_engine(TEST_DATABASE_URL, echo=False)
TestSessionLocal = async_sessionmaker(
    test_engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


# ---------------------------------------------------------------------------
# Create all tables before the session, drop them after
# ---------------------------------------------------------------------------

@pytest_asyncio.fixture(scope="session", autouse=True)
async def setup_database():
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


# ---------------------------------------------------------------------------
# Per-test DB session — rolls back after each test (keeps tests isolated)
# ---------------------------------------------------------------------------

@pytest_asyncio.fixture
async def db_session():
    async with test_engine.connect() as conn:
        await conn.begin()
        session = AsyncSession(bind=conn, expire_on_commit=False)
        yield session
        await session.close()
        await conn.rollback()


# ---------------------------------------------------------------------------
# Override get_session so the app uses the test session
# ---------------------------------------------------------------------------

@pytest_asyncio.fixture
async def client(db_session: AsyncSession):
    async def override_get_session():
        yield db_session

    app.dependency_overrides[get_session] = override_get_session

    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as ac:
        yield ac

    app.dependency_overrides.clear()


# ---------------------------------------------------------------------------
# Flush Redis test DB before each test
# ---------------------------------------------------------------------------

@pytest_asyncio.fixture(autouse=True)
async def flush_redis():
    await redis_client.flushdb()
    yield
    await redis_client.flushdb()