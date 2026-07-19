# AGENTS.md

## MinIO naming constraint
MinIO service names **must** use hyphens (`minio-test`), never underscores (`minio_test`). MinIO's S3 hostname validation rejects underscores with "Invalid Request (invalid hostname)". This applies to both `docker-compose.yml` and `docker-compose.test.yml`.

## Compose filename
The test compose file is `docker-compose.test.yml` (dot), not `docker-compose_test.yml` (underscore) as README states.

## Welcome premium bonus
`auth.py:301-302` grants `settings.WELCOME_BONUS_DAYS` (7, via `.env`) of premium to every new user when they complete onboarding. This means `likes_remaining_today` is `null` (unlimited) for all freshly-registered test users.

## Test fixtures

| Fixture | Behavior |
|---------|----------|
| `setup_database` (session) | Drops all tables, recreates them, seeds interests from `app/db/seed_data/interests.json`, creates admin user `admin@test.com`/`admin123` with `onboarding_complete` and `is_verified=true` |
| `reset_state` (per-test) | Deletes non-admin users + their profiles/settings, truncates all other tables, re-seeds interests, flushes Redis |
| `patch_redis` (per-test) | Swaps `app.core.redis.redis_client` with a test instance, restores original |
| `disable_rate_limiting` | Sets `limiter._enabled = False` |
| `mock_websocket_manager` | Patches `app.api.v1.endpoints.swipes.websocket_manager` |
| `mock_email_service` | Patches `app.services.email_service.send_verification_code` |

## Encryption
Message keys derived on-the-fly from `match_id + ENCRYPTION_SECRET` (PBKDF2, 100K iterations). Keys are **never stored**. SQLAlchemy `message.content` property auto-encrypts on set, auto-decrypts on get.

## Photo storage
`Photo.url` stores only the object key (e.g. `users/{id}/{photo_id}.jpg`). `PhotoService.get_photo_url()` resolves the full URL at read time based on moderation status.

## pytest
`pytest.ini` sets only `asyncio_mode = auto`. No `@pytest.mark.asyncio` decorators needed.

## Imports
Most `app/` package `__init__.py` files are empty — no barrel imports.

## Face verification
`face_verification_service.py` is a singleton using InsightFace buffalo_l model. Model is lazy-loaded on first request (thread-safe via `threading.Lock`). All CPU-bound work (OpenCV decode, InsightFace inference) runs in `asyncio.run_in_executor` to avoid blocking the event loop.

Challenge state lives in Redis (`verify_challenge:{user_id}`, 10-min TTL). Cooldowns (`verify_cooldown:{user_id}`, 24h TTL) and daily attempt counters (`verify_attempts:{user_id}:{date}`, 24h TTL) are also Redis-only.

`_AUTO_FACE_VERIFY = False` in admin_photos.py — the temporary bypass is disabled. Photo uploads no longer auto-set `face_verified=True`.

Test endpoint: `POST /admin/face-verification/test` accepts a video + user_id, runs the full pipeline, returns per-step debug JSON without modifying any DB records.

## Face verification tests
`tests/done/test_face_verification.py` has 28 tests covering challenge generation, verification status, video submission (with mocked face service), and pure unit tests for the service layer. All InsightFace/OpenCV calls are mocked in endpoint tests; only the service unit tests run real numpy/cosine comparisons.
