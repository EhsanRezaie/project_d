Here's the updated `dev.md` for Session 6 completion:

```markdown
# dev.md — Iranian Dating App

> **Purpose:** This file is the single source of truth for the project.  
> It is updated at the end of every session and passed to Claude at the start of the next one.  
> Claude should read this fully before doing anything in a new session.

---

## Project Status

- **Session:** 6 (Completed)
- **Current Phase:** Photo upload system fully implemented with admin review ✅
- **Next Phase:** Discover endpoint + Swipe system

---

## Project Overview

A Persian-language dating app for the **Iranian market**, similar to Badoo.
- Heterosexual only (male/female matching)
- All core features are free
- Monetized via ads shown every 10 minutes
- Premium subscription removes ads
- Target platforms: Android first, iOS later (same Flutter codebase)

---

## Team

- **Developer:** Solo (project owner) — Ehsan
- **Backend expertise:** Senior — FastAPI & Django (FastAPI chosen)
- **Mobile:** Learning Flutter from scratch
- **Daily availability:** 2–3 hours/day
- **Estimated MVP timeline:** 3–4 months (with Claude assistance)
- **Collaboration model:** Claude as pair programmer every session. Pass this file at the start of each session.

---

## Final Tech Stack

### Backend

| Tool | Role |
|------|------|
| FastAPI | Main framework — async-native, WebSocket support built-in |
| PostgreSQL + PostGIS | Primary database + geospatial queries |
| Redis | Realtime chat pub/sub + session store + online presence + rate limit storage + refresh token store |
| WebSocket (FastAPI native) | Realtime chat and notifications |
| Celery + Redis | Async task queue (match detection, push notifications) |
| SQLAlchemy (async) | ORM |
| Alembic | Database migrations |

### Mobile

| Tool | Role |
|------|------|
| Flutter + Dart | Cross-platform mobile (Android + iOS from one codebase) |

### Infrastructure

| Tool | Role |
|------|------|
| Docker + Docker Compose | Containerization for all services |
| Hetzner VPS | Primary hosting |
| ArvanCloud / Liara | Iranian cloud alternative if needed |

### Ads & Payments

| Tool | Role | Status |
|------|------|--------|
| AdMob | In-app ads every 10 min | ⚠️ Needs foreign account for payouts |
| Yektanet / MediaAd | Iranian ad network fallback | TBD |
| ZarinPal / PayPing | Iranian payment gateway for subscriptions | To be integrated |
| Cafe Bazaar + Myket | Primary app distribution | To be integrated |

---

## Key Decisions & Reasoning

### Authentication ✅ FULLY IMPLEMENTED

- Login method: Email or Google OAuth (required)
- Phone number: Optional — used only for identity verification badge
- No mandatory phone login — reduces signup friction
- Verified badge: Users who verify phone get a "Verified" badge
- **JWT:** access token (7 days) + refresh token (30 days)
- **Token type field** in JWT payload to distinguish access vs refresh
- **Unique jti (JWT ID)** in every token — ensures each token is unique
- **Token versioning** (`token_version` in User model + JWT) — enables instant revocation
- Refresh tokens stored in Redis with 30-day TTL — enables instant revocation
- **Refresh token rotation:** every /refresh call revokes old token and issues a new one
- **Password change:** increments token_version, revokes ALL user tokens instantly
- Logout: refresh token immediately revoked in Redis
- **All Redis operations have timeouts, retries, and error handling**
- **Health check endpoint** (`GET /api/v1/auth/health`) monitors Redis connectivity
- **Structured logging** with file rotation (logs/ directory)

### Rate Limiting

- Implemented via slowapi + Redis backend (shared across workers)
- Limits per IP per minute:
  - POST /register → 5/min
  - POST /login → 10/min
  - POST /google → 10/min
  - POST /refresh → 20/min
  - POST /logout → 20/min
  - POST /complete-profile → 10/min
  - POST /change-password → 5/min
  - GET /users/me → 100/min
  - PUT /users/me → 30/min
  - DELETE /users/me → 5/min
  - POST /users/me/location → 60/min
  - POST /users/me/photos → 10/min
  - GET /users/me/photos → 30/min
  - DELETE /users/me/photos/{id} → 20/min
  - PUT /users/me/photos/{id}/main → 20/min
- 429 response includes Retry-After header

### Google OAuth — Profile Completion Flow

- Google does not return age or gender
- On first Google login, user created with is_profile_complete=False, age=18 (placeholder), gender='male' (placeholder)
- Frontend checks is_profile_complete in TokenResponse.user
- If false → redirect to profile completion screen
- User calls POST /api/v1/auth/complete-profile with real age + gender
- is_profile_complete set to True, fresh token pair returned
- Existing email users who link Google get is_profile_complete=True (their data is already real)

### User Profile Fields

- Name, age, gender (male/female), bio
- Height (cm) — optional
- Weight (kg) — optional
- Profile photos (multiple, max 6)
- Location (lat/lng — updated on app open)

### Photo System ✅ FULLY IMPLEMENTED

- Users can upload up to 6 photos
- Photos saved locally in `uploads/users/{user_id}/{photo_id}.jpg`
- Auto-validation: file size (max 5MB), dimensions (200-5000px), format (JPEG/PNG/WEBP)
- Photos start with status='pending' (not visible to other users)
- Admin reviews photos via admin endpoints
- Admin can approve/reject with reason
- First uploaded photo becomes main profile photo
- Users can reorder, delete, and change main photo
- Only approved photos visible to other users

### Matching Model

- Heterosexual only: males see females, females see males
- Swipe-based: like or pass
- Match = both users liked each other
- MVP algorithm: recency + distance only

### Monetization

- All features free for all users
- Ad shown every 10 minutes (full-screen interstitial)
- Premium subscription = no ads + unlimited likes/chats
- Subscription managed via Iranian payment gateway (not Google Play Billing)

### Iranian Market Constraints

| Challenge | Status | Solution |
|-----------|--------|----------|
| AdMob payouts | ⚠️ Blocked for Iranian accounts | Use foreign partner account |
| Google Play Billing | ❌ Not available | Use ZarinPal/PayPing directly |
| Play Store publishing | ⚠️ Restricted | Publish on Cafe Bazaar + Myket |
| Server latency | ⚠️ Must be fast | Hetzner EU or ArvanCloud |

---

## Business Rules & Policies

> These must be implemented as features develop. Do not forget them.

### 1. Daily Like Limit (Free Users)

- Free users can send **50 likes per day**
- Resets at midnight (Tehran time)
- Premium users: unlimited likes

### 2. Daily Chat Limit Without Match (Free Users)

- Free users can **start 10 chats per day without being matched**
- Resets at midnight (Tehran time)
- Premium users: unlimited

### 3. Ad Reward System

- When a free user hits their daily like or chat limit, they can watch a rewarded ad
- Each rewarded ad gives: **+5 likes** and **+1 new chat**
- Implemented via AdMob Rewarded Ads (or Iranian equivalent)
- Must be tracked server-side to prevent abuse (not just client-side)

### 4. Unmatched Chat Limit

- Without a match, a user can send max **2 messages** to another user
- After 2 messages, the recipient must accept the conversation to continue
- This prevents spam and harassment
- Acceptance = explicit button tap ("Allow messages from this person")

### 5. Photo Moderation System ✅ IMPLEMENTED

- All uploaded photos go through admin review before appearing to others
- Photos start with status='pending'
- Admin endpoints to approve/reject photos
- Rejected photos include reason visible to user
- Max 6 photos per user
- First photo automatically becomes main profile photo
- Users can reorder and change main photo (after approval)

### 6. Face Verification (Selfie Match)

- To verify that profile photos actually show the user (not someone else)
- Flow: user takes a live selfie in-app → compared against their uploaded photos using face similarity
- Use AWS Rekognition Face Comparison or similar
- Verified users get a "Photo Verified" badge (different from phone verified badge)
- Not mandatory for signup, but encouraged with UI nudges
- Implementation phase: after MVP core is stable

### 7. Unit Testing Strategy ✅ IMPLEMENTED

- Every feature must have unit tests before being considered done
- Test environment is fully isolated:
  - Separate test database (spun up fresh for each test run)
  - Seed data loaded automatically
  - All tables dropped and recreated after test run
- Using pytest + pytest-asyncio
- Using .env.test file for test config
- Test DB uses Docker PostgreSQL container
- No mocking of the database — tests run against real DB
- Structure: tests/ folder mirrors app/ structure
- **66 tests written and passing** (33 auth + 20 users + 13 photos)

### 8. Review Reward System

- If a user leaves a review on Google Play, Cafe Bazaar, or Myket → they receive **3 days of free premium**
- Implementation: user submits proof (screenshot or in-app deep link callback)
- Manual verification for MVP, automated later
- One reward per user, per platform (max 3 platforms = max 9 days)
- Anti-abuse: reward only given after review is confirmed live on store
- Track in a `review_rewards` table

---

## Database Design

### Table: `users` ✅ with token_version

```sql
id                   UUID PRIMARY KEY DEFAULT gen_random_uuid()
email                VARCHAR(255) UNIQUE NOT NULL
password_hash        VARCHAR(255)
google_id            VARCHAR(255) UNIQUE
phone                VARCHAR(20)
phone_verified       BOOLEAN DEFAULT FALSE
name                 VARCHAR(100) NOT NULL
age                  SMALLINT NOT NULL
gender               VARCHAR(10) NOT NULL
bio                  TEXT
height               SMALLINT
weight               SMALLINT
lat                  DOUBLE PRECISION
lng                  DOUBLE PRECISION
is_premium           BOOLEAN DEFAULT FALSE
is_active            BOOLEAN DEFAULT TRUE
token_version        INTEGER DEFAULT 1 NOT NULL
is_profile_complete  BOOLEAN DEFAULT TRUE
created_at           TIMESTAMPTZ DEFAULT NOW()
last_seen_at         TIMESTAMPTZ
```

### Table: `photos` ✅ with moderation

```sql
id            UUID PRIMARY KEY DEFAULT gen_random_uuid()
user_id       UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE
url           TEXT NOT NULL
order         SMALLINT NOT NULL DEFAULT 0
is_main       BOOLEAN DEFAULT FALSE
status        VARCHAR(20) DEFAULT 'pending'   -- 'pending' | 'approved' | 'rejected'
reject_reason TEXT
face_verified BOOLEAN DEFAULT FALSE
created_at    TIMESTAMPTZ DEFAULT NOW()
```

### Table: `swipes`

```sql
id          UUID PRIMARY KEY DEFAULT gen_random_uuid()
from_user   UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE
to_user     UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE
direction   VARCHAR(10) NOT NULL
created_at  TIMESTAMPTZ DEFAULT NOW()
UNIQUE (from_user, to_user)
```

### Table: `matches`

```sql
id          UUID PRIMARY KEY DEFAULT gen_random_uuid()
user1_id    UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE
user2_id    UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE
is_active   BOOLEAN DEFAULT TRUE
matched_at  TIMESTAMPTZ DEFAULT NOW()
UNIQUE (user1_id, user2_id)
```

### Table: `messages`

```sql
id          UUID PRIMARY KEY DEFAULT gen_random_uuid()
match_id    UUID REFERENCES matches(id) ON DELETE CASCADE
sender_id   UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE
receiver_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE
content     TEXT NOT NULL
is_read     BOOLEAN DEFAULT FALSE
is_accepted BOOLEAN DEFAULT FALSE
sent_at     TIMESTAMPTZ DEFAULT NOW()
```

### Table: `subscriptions`

```sql
id          UUID PRIMARY KEY DEFAULT gen_random_uuid()
user_id     UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE
status      VARCHAR(20) NOT NULL
plan        VARCHAR(50) NOT NULL
started_at  TIMESTAMPTZ NOT NULL
expires_at  TIMESTAMPTZ NOT NULL
source      VARCHAR(50)
```

### Table: `daily_limits`

```sql
id              UUID PRIMARY KEY DEFAULT gen_random_uuid()
user_id         UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE
date            DATE NOT NULL
likes_used      SMALLINT DEFAULT 0
chats_used      SMALLINT DEFAULT 0
ad_likes_bonus  SMALLINT DEFAULT 0
ad_chats_bonus  SMALLINT DEFAULT 0
UNIQUE (user_id, date)
```

### Table: `reports`

```sql
id           UUID PRIMARY KEY DEFAULT gen_random_uuid()
reporter_id  UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE
reported_id  UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE
reason       TEXT NOT NULL
created_at   TIMESTAMPTZ DEFAULT NOW()
```

### Table: `review_rewards`

```sql
id           UUID PRIMARY KEY DEFAULT gen_random_uuid()
user_id      UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE
platform     VARCHAR(20) NOT NULL
submitted_at TIMESTAMPTZ DEFAULT NOW()
verified_at  TIMESTAMPTZ
status       VARCHAR(20) DEFAULT 'pending'
days_granted SMALLINT DEFAULT 3
UNIQUE (user_id, platform)
```

### Redis Keys

```
refresh_token:{token}  →  user_id string (TTL: 30 days)
```

### File Storage

```
uploads/
└── users/
    └── {user_id}/
        └── {photo_id}.jpg
```

### Logging

- Logs stored in `logs/app.log` with rotation
- Redis operations logged for debugging
- Auth events logged
- Admin actions logged

---

## Project Structure (as built)

```
dating-app/
├── app/
│   ├── api/v1/endpoints/
│   │   ├── auth.py          ✅ done
│   │   ├── users.py         ✅ done
│   │   ├── photos.py        ✅ done (upload, list, delete, set main)
│   │   ├── admin.py         ✅ done (approve/reject photos)
│   │   ├── discover.py
│   │   ├── swipes.py
│   │   ├── matches.py
│   │   ├── messages.py
│   │   ├── subscriptions.py
│   │   └── reports.py
│   ├── core/
│   │   ├── config.py        ✅ done
│   │   ├── security.py      ✅ done
│   │   ├── redis.py         ✅ done
│   │   ├── limiter.py       ✅ done
│   │   ├── logging.py       ✅ done
│   │   └── deps.py          ✅ done
│   ├── db/
│   │   ├── base.py          ✅ done
│   │   └── session.py       ✅ done
│   ├── models/
│   │   ├── __init__.py      ✅ done
│   │   ├── user.py          ✅ done
│   │   ├── photo.py         ✅ done
│   │   ├── swipe.py         ✅ done
│   │   ├── match.py         ✅ done
│   │   ├── message.py       ✅ done
│   │   ├── subscription.py  ✅ done
│   │   ├── report.py        ✅ done
│   │   ├── daily_limit.py   ✅ done
│   │   └── review_reward.py ✅ done
│   ├── schemas/
│   │   ├── auth.py          ✅ done
│   │   ├── user.py          ✅ done
│   │   └── photo.py         ✅ done
│   ├── services/
│   │   ├── photo_service.py ✅ done (validation, storage)
│   │   └── moderation_service.py (placeholder)
│   ├── tasks/
│   └── main.py              ✅ done (with static files serving)
├── alembic/                 ✅ done
├── tests/
│   ├── conftest.py          ✅ done
│   ├── test_auth.py         ✅ done (33 tests)
│   ├── test_users.py        ✅ done (20 tests)
│   └── test_photos.py       ✅ done (13 tests)
├── uploads/                 ✅ created
│   └── users/
├── logs/                    ✅ done
├── docker-compose.yml       ✅ done
├── .env                     ✅ done
├── .env.test                ✅ done
├── .env.example             ✅ done
├── .gitignore               ✅ done
├── requirements.txt         ✅ done (Pillow added)
├── dev.md                   ✅ this file
└── README.md                ✅ done
```

---

## API Endpoints Plan

### Auth ✅ fully implemented

- `POST /api/v1/auth/register` — email + password → JWT ✅
- `POST /api/v1/auth/login` — email + password → JWT ✅
- `POST /api/v1/auth/google` — Google OAuth ID token → JWT ✅
- `POST /api/v1/auth/refresh` — refresh token → new JWT pair (rotation) ✅
- `POST /api/v1/auth/logout` — revoke refresh token ✅
- `POST /api/v1/auth/complete-profile` — Google users set real age + gender ✅
- `POST /api/v1/auth/change-password` — change password + revoke all tokens ✅
- `GET /api/v1/auth/health` — health check (Redis status) ✅

### Users ✅ fully implemented

- `GET /api/v1/users/me` — get my profile ✅
- `PUT /api/v1/users/me` — update my profile ✅
- `DELETE /api/v1/users/me` — soft delete account ✅
- `POST /api/v1/users/me/location` — update lat/lng ✅

### Photos ✅ fully implemented

- `POST /api/v1/users/me/photos` — upload photo (pending review) ✅
- `GET /api/v1/users/me/photos` — list my photos ✅
- `DELETE /api/v1/users/me/photos/{id}` — delete photo ✅
- `PUT /api/v1/users/me/photos/{id}/main` — set main photo ✅

### Admin ✅ fully implemented

- `GET /api/v1/admin/photos/pending` — list pending photos ✅
- `POST /api/v1/admin/photos/{id}/approve` — approve photo ✅
- `POST /api/v1/admin/photos/{id}/reject` — reject photo with reason ✅
- `GET /api/v1/admin/photos/stats` — moderation statistics ✅
- `GET /api/v1/admin/photos/user/{user_id}` — view user's photos ✅

### Discover (next session)

- `GET /api/v1/discover` — get candidate profiles

### Swipes

- `POST /api/v1/swipes` — send like or pass

### Matches

- `GET /api/v1/matches` — list my matches

### Messages

- `GET /api/v1/messages/{match_id}` — get chat history
- `WS /ws/chat/{match_id}` — realtime WebSocket chat

### Subscriptions

- `POST /api/v1/subscriptions` — initiate purchase
- `POST /api/v1/subscriptions/verify` — verify payment

### Reports

- `POST /api/v1/reports` — report a user

---

## Installed Packages

```
fastapi==0.136.3
uvicorn==0.49.0
sqlalchemy==2.0.50
asyncpg==0.31.0
alembic==1.18.4
pydantic-settings==2.14.1
pydantic[email]==2.13.4
python-jose[cryptography]==3.5.0
passlib[bcrypt]==1.7.4
bcrypt==4.0.1
google-auth==2.53.0
redis==8.0.0
slowapi==0.1.9
python-dotenv==1.2.2
httpx==0.28.1
pytest==9.0.3
pytest-asyncio==1.4.0
pytest-cov==6.0.0
Pillow==12.2.0
```

---

## Session Log

### Session 1

Decisions made: Stack, monetization model, auth model, ERD design, Iranian market constraints identified.

### Session 2

Full project bootstrapped on Ubuntu/Linux. Python venv, all dependencies installed. Docker Compose with PostGIS + Redis. All SQLAlchemy models written. Alembic configured and initial migration applied. FastAPI app running with /health and /docs.

### Session 3

Updated models: photo.py, message.py. Added models: daily_limit.py, review_reward.py. security.py, schemas/auth.py, endpoints/auth.py (register/login/google/refresh). session.py renamed to get_session, main.py updated.

### Session 4

Auth system hardened with token versioning, jti, Redis retries, logging, pytest setup, 33 auth tests passing.

### Session 5

Users endpoints implemented: GET/PUT/DELETE /users/me, POST /users/me/location. 20 users tests passing. Total 53 tests.

### Session 6 (COMPLETED)

**Completed:**
- `app/schemas/photo.py` — PhotoResponse schema
- `app/services/photo_service.py` — Image validation, compression, local storage
- `app/api/v1/endpoints/photos.py` — Upload, list, delete, set main photo
- `app/api/v1/endpoints/admin.py` — Admin endpoints for photo moderation
- `app/main.py` — Added static file serving for uploads
- `app/core/config.py` — Added ADMIN_SECRET_KEY
- `app/models/photo.py` — Added created_at field
- `tests/test_photos.py` — 13 comprehensive photo tests
- Added Pillow dependency for image processing
- **Total tests: 66 passing** (33 auth + 20 users + 13 photos)

---

## Next Session Goals (Session 7)

1. **Discover Endpoint**
   - `GET /api/v1/discover` — get candidate profiles
   - Filter by opposite gender only
   - Filter by age range (18-100)
   - Filter by distance (default 50km, user configurable)
   - Exclude already swiped users
   - Exclude deactivated users
   - Pagination (limit/offset)
   - Sort by recency (newest first) + distance

2. **Swipe System**
   - `POST /api/v1/swipes` — like or pass on a user
   - Check daily like limit for free users
   - Create match record when both users like each other
   - Send notification (WebSocket) when match happens

3. **Write tests** for discover and swipes

---

## Useful Commands

### Run tests
```bash
pytest tests/ -v
pytest tests/test_auth.py -v
pytest tests/test_users.py -v
pytest tests/test_photos.py -v
pytest tests/ -v --cov=app --cov-report=html
```

### Run migrations
```bash
alembic revision --autogenerate -m "description"
alembic upgrade head
```

### Docker
```bash
docker-compose up -d
docker-compose down
docker-compose logs -f
```

### Run app
```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Admin endpoints (with Postman)
```
Headers: X-Admin-Key: your-secret-key

GET    /api/v1/admin/photos/pending
POST   /api/v1/admin/photos/{id}/approve
POST   /api/v1/admin/photos/{id}/reject?reason=... 
GET    /api/v1/admin/photos/stats
GET    /api/v1/admin/photos/user/{user_id}
```

---

## Notes

- All 66 tests are passing ✅
- Coverage available via `pytest tests/ -v --cov=app --cov-report=html`
- Photos stored locally in `uploads/` folder
- Admin secret key must be set in `.env`
- Photos require admin approval before visible to other users
- Ready for Session 7: Discover + Swipe system

---