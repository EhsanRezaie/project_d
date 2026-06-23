"""
Tests for GET /api/v1/interests

Public endpoint, no auth required. Interests are seeded reference data —
each test that needs rows inserts them directly via db_session (since
conftest.reset_state wipes the interests table after every test).
"""
import uuid
import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.interest import Interest

INTERESTS_URL = "/api/v1/interests"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

async def seed_interests(db_session: AsyncSession, rows: list[dict]) -> list[Interest]:
    """Insert interest rows directly and return the created objects."""
    interests = [
        Interest(
            id=uuid.uuid4(),
            name=row["name"],
            category=row.get("category"),
            icon=row.get("icon"),
        )
        for row in rows
    ]
    db_session.add_all(interests)
    await db_session.commit()
    return interests


SAMPLE_INTERESTS = [
    {"name": "football", "category": "sports_fitness", "icon": "⚽"},
    {"name": "coffee", "category": "food_drink", "icon": "☕"},
    {"name": "painting", "category": "arts_creative", "icon": "🎨"},
    {"name": "yoga", "category": "sports_fitness", "icon": "🧘"},
    {"name": "cooking", "category": "food_drink", "icon": "🍳"},
]


# ---------------------------------------------------------------------------
# Basic response shape
# ---------------------------------------------------------------------------

class TestInterestsResponseShape:

    async def test_returns_200(self, client: AsyncClient, db_session: AsyncSession):
        await seed_interests(db_session, SAMPLE_INTERESTS)
        res = await client.get(INTERESTS_URL)
        assert res.status_code == 200

    async def test_returns_json_array(self, client: AsyncClient, db_session: AsyncSession):
        await seed_interests(db_session, SAMPLE_INTERESTS)
        res = await client.get(INTERESTS_URL)
        assert isinstance(res.json(), list)

    async def test_empty_when_no_interests_seeded(self, client: AsyncClient):
        """When no interests exist in the DB at all, should return an empty
        list, not a 404 or error."""
        res = await client.get(INTERESTS_URL)
        assert res.status_code == 200
        assert res.json() == []

    async def test_each_item_has_required_fields(self, client: AsyncClient, db_session: AsyncSession):
        await seed_interests(db_session, SAMPLE_INTERESTS[:1])
        item = (await client.get(INTERESTS_URL)).json()[0]
        assert "id" in item
        assert "name" in item

    async def test_each_item_has_category_field(self, client: AsyncClient, db_session: AsyncSession):
        await seed_interests(db_session, SAMPLE_INTERESTS[:1])
        item = (await client.get(INTERESTS_URL)).json()[0]
        assert "category" in item

    async def test_each_item_has_icon_field(self, client: AsyncClient, db_session: AsyncSession):
        await seed_interests(db_session, SAMPLE_INTERESTS[:1])
        item = (await client.get(INTERESTS_URL)).json()[0]
        assert "icon" in item

    async def test_id_is_valid_uuid(self, client: AsyncClient, db_session: AsyncSession):
        await seed_interests(db_session, SAMPLE_INTERESTS[:1])
        item = (await client.get(INTERESTS_URL)).json()[0]
        # Should not raise
        uuid.UUID(item["id"])

    async def test_name_is_stable_english_key(self, client: AsyncClient, db_session: AsyncSession):
        """name must be the stable English key (e.g. 'football'), not a
        localized display string — Flutter resolves it client-side."""
        await seed_interests(db_session, [{"name": "football", "category": "sports_fitness", "icon": "⚽"}])
        item = (await client.get(INTERESTS_URL)).json()[0]
        assert item["name"] == "football"

    async def test_icon_is_emoji_string(self, client: AsyncClient, db_session: AsyncSession):
        await seed_interests(db_session, [{"name": "football", "category": "sports_fitness", "icon": "⚽"}])
        item = (await client.get(INTERESTS_URL)).json()[0]
        assert item["icon"] == "⚽"


# ---------------------------------------------------------------------------
# Count and content
# ---------------------------------------------------------------------------

class TestInterestsCount:

    async def test_returns_all_seeded_interests(self, client: AsyncClient, db_session: AsyncSession):
        await seed_interests(db_session, SAMPLE_INTERESTS)
        res = await client.get(INTERESTS_URL)
        assert len(res.json()) == len(SAMPLE_INTERESTS)

    async def test_returns_correct_names(self, client: AsyncClient, db_session: AsyncSession):
        await seed_interests(db_session, SAMPLE_INTERESTS)
        names = {item["name"] for item in (await client.get(INTERESTS_URL)).json()}
        expected = {r["name"] for r in SAMPLE_INTERESTS}
        assert names == expected

    async def test_returns_correct_categories(self, client: AsyncClient, db_session: AsyncSession):
        await seed_interests(db_session, SAMPLE_INTERESTS)
        categories = {item["category"] for item in (await client.get(INTERESTS_URL)).json()}
        assert "sports_fitness" in categories
        assert "food_drink" in categories
        assert "arts_creative" in categories

    async def test_single_interest_returned_correctly(
        self, client: AsyncClient, db_session: AsyncSession
    ):
        await seed_interests(db_session, [{"name": "yoga", "category": "sports_fitness", "icon": "🧘"}])
        items = (await client.get(INTERESTS_URL)).json()
        assert len(items) == 1
        assert items[0]["name"] == "yoga"
        assert items[0]["category"] == "sports_fitness"
        assert items[0]["icon"] == "🧘"


# ---------------------------------------------------------------------------
# Ordering
# ---------------------------------------------------------------------------

class TestInterestsOrdering:

    async def test_ordered_by_category_then_name(
        self, client: AsyncClient, db_session: AsyncSession
    ):
        """Results must come back sorted by category then name — the endpoint
        uses ORDER BY category, name so Flutter can group them predictably
        without a client-side sort."""
        await seed_interests(db_session, SAMPLE_INTERESTS)
        items = (await client.get(INTERESTS_URL)).json()
        names_in_order = [i["name"] for i in items]
        expected = sorted(SAMPLE_INTERESTS, key=lambda r: (r["category"], r["name"]))
        assert names_in_order == [r["name"] for r in expected]


# ---------------------------------------------------------------------------
# Nullable fields
# ---------------------------------------------------------------------------

class TestInterestsNullableFields:

    async def test_category_can_be_null(self, client: AsyncClient, db_session: AsyncSession):
        """category is nullable in the model — should serialize to null, not
        raise a validation error."""
        await seed_interests(db_session, [{"name": "mystery", "category": None, "icon": "❓"}])
        item = (await client.get(INTERESTS_URL)).json()[0]
        assert item["category"] is None

    async def test_icon_can_be_null(self, client: AsyncClient, db_session: AsyncSession):
        """icon is nullable — should serialize to null, not raise."""
        await seed_interests(db_session, [{"name": "noicon", "category": "lifestyle", "icon": None}])
        item = (await client.get(INTERESTS_URL)).json()[0]
        assert item["icon"] is None

    async def test_both_optional_fields_null(self, client: AsyncClient, db_session: AsyncSession):
        await seed_interests(db_session, [{"name": "bare", "category": None, "icon": None}])
        item = (await client.get(INTERESTS_URL)).json()[0]
        assert item["name"] == "bare"
        assert item["category"] is None
        assert item["icon"] is None


# ---------------------------------------------------------------------------
# Access control — public endpoint
# ---------------------------------------------------------------------------

class TestInterestsAccessControl:

    async def test_no_auth_header_required(self, client: AsyncClient, db_session: AsyncSession):
        """Interests must be accessible without any Authorization header —
        they're needed on the onboarding screen before a user has a token."""
        await seed_interests(db_session, SAMPLE_INTERESTS[:1])
        res = await client.get(INTERESTS_URL)
        assert res.status_code == 200

    async def test_garbage_auth_header_still_works(
        self, client: AsyncClient, db_session: AsyncSession
    ):
        """A malformed or invalid auth header should not cause a 401 —
        the endpoint doesn't check auth at all."""
        await seed_interests(db_session, SAMPLE_INTERESTS[:1])
        res = await client.get(
            INTERESTS_URL,
            headers={"Authorization": "Bearer garbage-token"},
        )
        assert res.status_code == 200

    async def test_no_query_params_accepted(self, client: AsyncClient, db_session: AsyncSession):
        """The interests endpoint takes no query params — unknown params
        should be silently ignored, not cause a 422."""
        await seed_interests(db_session, SAMPLE_INTERESTS[:1])
        res = await client.get(INTERESTS_URL, params={"language": "fa", "page": 1})
        assert res.status_code == 200


# ---------------------------------------------------------------------------
# Scale — mimics the real 158-interest seed
# ---------------------------------------------------------------------------

class TestInterestsScale:

    async def test_handles_full_production_count(
        self, client: AsyncClient, db_session: AsyncSession
    ):
        """Endpoint must handle the full 158-interest production data set
        cleanly in a single response — no pagination, no truncation."""
        categories = [
            "sports_fitness", "music", "food_drink", "arts_creative",
            "lifestyle", "gaming_tech", "movies_tv", "outdoors_nature",
            "learning", "travel", "fashion_beauty", "social_causes", "pets_animals",
        ]
        rows = [
            {"name": f"interest_{i}", "category": categories[i % len(categories)], "icon": "⭐"}
            for i in range(158)
        ]
        await seed_interests(db_session, rows)
        res = await client.get(INTERESTS_URL)
        assert res.status_code == 200
        assert len(res.json()) == 158

    async def test_all_13_categories_present_in_response(
        self, client: AsyncClient, db_session: AsyncSession
    ):
        categories = [
            "sports_fitness", "music", "food_drink", "arts_creative",
            "lifestyle", "gaming_tech", "movies_tv", "outdoors_nature",
            "learning", "travel", "fashion_beauty", "social_causes", "pets_animals",
        ]
        rows = [
            {"name": f"item_{cat}_{i}", "category": cat, "icon": "⭐"}
            for cat in categories
            for i in range(3)
        ]
        await seed_interests(db_session, rows)
        res = await client.get(INTERESTS_URL)
        returned_cats = {item["category"] for item in res.json()}
        assert returned_cats == set(categories)