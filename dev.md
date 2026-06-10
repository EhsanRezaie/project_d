Here's the updated `dev.md` for Session 8 completion:

```markdown
# dev.md — Iranian Dating App

> **Purpose:** This file is the single source of truth for the project.  
> It is updated at the end of every session and passed to Claude at the start of the next one.  
> Claude should read this fully before doing anything in a new session.

---

## Project Status

- **Session:** 8 (Completed)
- **Current Phase:** Search page + Block system fully implemented ✅
- **Next Phase:** Match list + WebSocket notifications

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
  - GET /discover → 60/min
  - POST /swipes → 30/min
  - GET /swipes/stats → 30/min
  - GET /search → 60/min
  - POST /blocks/{id}/block → 20/min
  - POST /blocks/{id}/unblock → 20/min
  - GET /blocks → 30/min
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

### Two Discovery Modes ✅ FULLY IMPLEMENTED

| Page | Purpose | Can see same user twice? | Filters |
|------|---------|-------------------------|---------|
| **Discover (Swipe Page)** | Main swiping interface | ❌ NO - once swiped, gone forever | Age, Distance |
| **Search Page** | Browse with advanced filters | ✅ YES - unless blocked | Age, Distance, Gender, Height, Weight, Verified, Has Photos |

### Matching Model

- Heterosexual only: males see females, females see males
- Swipe-based: like or pass
- Match = both users liked each other
- Match detected instantly when mutual like occurs
- Match record created with user1_id and user2_id

### Daily Like Limits (Planned - Session 11)

| User Type | Daily Likes |
|-----------|-------------|
| Free User | 50 likes per day |
| Premium User | Unlimited |
| Ad Reward | +5 bonus likes |

### Unmatched Chat Limits (Planned - Session 10)

- Free users can send **2 messages** to any user without a match
- After 2 messages, recipient must accept the conversation
- Acceptance = explicit button tap ("Allow messages from this person")
- Prevents spam and harassment

### Block System ✅ FULLY IMPLEMENTED

- Users can block other users
- Blocked users don't appear in Discover or Search
- Blocks are permanent until unblocked
- Block list endpoint to see all blocked users

### Monetization

- All core features free for all users
- Ad shown every 10 minutes (full-screen interstitial)
- Premium subscription = no ads + unlimited likes + unlimited chats
- Ad reward system: watch ad → +5 likes, +1 new chat
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

### 1. Daily Like Limit (Free Users) 🔲 Session 11

- Free users can send **50 likes per day**
- Resets at midnight (Tehran time)
- Premium users: unlimited likes
- Tracked in `daily_limits` table

### 2. Daily Chat Limit Without Match (Free Users) 🔲 Session 10

- Free users can **start 10 chats per day without being matched**
- Resets at midnight (Tehran time)
- Premium users: unlimited

### 3. Ad Reward System 🔲 Session 11

- When a free user hits their daily like or chat limit, they can watch a rewarded ad
- Each rewarded ad gives: **+5 likes** and **+1 new chat**
- Implemented via AdMob Rewarded Ads (or Iranian equivalent)
- Must be tracked server-side to prevent abuse (not just client-side)

### 4. Unmatched Chat Limit 🔲 Session 10

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

### 6. Face Verification (Selfie Match) 🔲 Future

- To verify that profile photos actually show the user (not someone else)
- Flow: user takes a live selfie in-app → compared against their uploaded photos using face similarity
- Use AWS Rekognition Face Comparison or similar
- Verified users get a "Photo Verified" badge (different from phone verified badge)
- Not mandatory for signup, but encouraged with UI nudges

### 7. Unit Testing Strategy ✅ IMPLEMENTED

- Every feature must have unit tests before being considered done
- Test environment is fully isolated
- Using pytest + pytest-asyncio
- Using .env.test file for test config
- Rate limiting disabled during tests
- **Tests written and passing for all implemented features**

### 8. Review Reward System 🔲 Future

- If a user leaves a review on Google Play, Cafe Bazaar, or Myket → they receive **3 days of free premium**
- Implementation: user submits proof (screenshot or in-app deep link callback)
- Manual verification for MVP, automated later
- One reward per user, per platform (max 3 platforms = max 9 days)

---

## Database Design

### Table: `users` ✅

```sql
id                   UUID PRIMARY KEY
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

### Table: `photos` ✅

```sql
id            UUID PRIMARY KEY
user_id       UUID REFERENCES users(id) ON DELETE CASCADE
url           TEXT NOT NULL
order         SMALLINT DEFAULT 0
is_main       BOOLEAN DEFAULT FALSE
status        VARCHAR(20) DEFAULT 'pending'
reject_reason TEXT
face_verified BOOLEAN DEFAULT FALSE
created_at    TIMESTAMPTZ DEFAULT NOW()
```

### Table: `swipes` ✅

```sql
id          UUID PRIMARY KEY
from_user   UUID REFERENCES users(id) ON DELETE CASCADE
to_user     UUID REFERENCES users(id) ON DELETE CASCADE
direction   VARCHAR(10) NOT NULL
created_at  TIMESTAMPTZ DEFAULT NOW()
UNIQUE (from_user, to_user)
```

### Table: `matches` ✅

```sql
id          UUID PRIMARY KEY
user1_id    UUID REFERENCES users(id) ON DELETE CASCADE
user2_id    UUID REFERENCES users(id) ON DELETE CASCADE
is_active   BOOLEAN DEFAULT TRUE
matched_at  TIMESTAMPTZ DEFAULT NOW()
UNIQUE (user1_id, user2_id)
```

### Table: `daily_limits` ✅

```sql
id              UUID PRIMARY KEY
user_id         UUID REFERENCES users(id) ON DELETE CASCADE
date            DATE NOT NULL
likes_used      SMALLINT DEFAULT 0
chats_used      SMALLINT DEFAULT 0
ad_likes_bonus  SMALLINT DEFAULT 0
ad_chats_bonus  SMALLINT DEFAULT 0
UNIQUE (user_id, date)
```

### Table: `blocks` ✅

```sql
id           UUID PRIMARY KEY
blocker_id   UUID REFERENCES users(id) ON DELETE CASCADE
blocked_id   UUID REFERENCES users(id) ON DELETE CASCADE
created_at   TIMESTAMPTZ DEFAULT NOW()
UNIQUE (blocker_id, blocked_id)
```

### Table: `messages` 🔲 Session 10

```sql
id          UUID PRIMARY KEY
match_id    UUID REFERENCES matches(id) ON DELETE CASCADE
sender_id   UUID REFERENCES users(id) ON DELETE CASCADE
receiver_id UUID REFERENCES users(id) ON DELETE CASCADE
content     TEXT NOT NULL
is_read     BOOLEAN DEFAULT FALSE
is_accepted BOOLEAN DEFAULT FALSE
sent_at     TIMESTAMPTZ DEFAULT NOW()
```

### Table: `subscriptions` 🔲 Session 11

```sql
id          UUID PRIMARY KEY
user_id     UUID REFERENCES users(id) ON DELETE CASCADE
status      VARCHAR(20) NOT NULL
plan        VARCHAR(50) NOT NULL
started_at  TIMESTAMPTZ NOT NULL
expires_at  TIMESTAMPTZ NOT NULL
source      VARCHAR(50)
```

### Table: `reports` 🔲 Future

```sql
id           UUID PRIMARY KEY
reporter_id  UUID REFERENCES users(id) ON DELETE CASCADE
reported_id  UUID REFERENCES users(id) ON DELETE CASCADE
reason       TEXT NOT NULL
created_at   TIMESTAMPTZ DEFAULT NOW()
```

### Table: `review_rewards` 🔲 Future

```sql
id           UUID PRIMARY KEY
user_id      UUID REFERENCES users(id) ON DELETE CASCADE
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
│   │   ├── photos.py        ✅ done
│   │   ├── admin.py         ✅ done
│   │   ├── discover.py      ✅ done
│   │   ├── swipes.py        ✅ done
│   │   ├── search.py        ✅ done
│   │   ├── blocks.py        ✅ done
│   │   ├── matches.py       🔲 Session 9
│   │   ├── messages.py      🔲 Session 10
│   │   ├── subscriptions.py 🔲 Session 11
│   │   └── reports.py       🔲 Future
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
│   │   ├── daily_limit.py   ✅ done
│   │   ├── block.py         ✅ done
│   │   ├── message.py       🔲 Session 10
│   │   ├── subscription.py  🔲 Session 11
│   │   ├── report.py        🔲 Future
│   │   └── review_reward.py 🔲 Future
│   ├── schemas/
│   │   ├── auth.py          ✅ done
│   │   ├── user.py          ✅ done
│   │   ├── photo.py         ✅ done
│   │   ├── discover.py      ✅ done
│   │   └── search.py        ✅ done
│   ├── services/
│   │   ├── photo_service.py ✅ done
│   │   └── moderation_service.py (placeholder)
│   ├── tasks/
│   └── main.py              ✅ done
├── alembic/                 ✅ done
├── tests/
│   ├── conftest.py          ✅ done
│   ├── test_auth.py         ✅ done (33 tests)
│   ├── test_users.py        ✅ done (20 tests)
│   ├── test_photos.py       ✅ done (13 tests)
│   ├── test_discover.py     ✅ done
│   ├── test_swipes.py       ✅ done
│   ├── test_search.py       ✅ done
│   └── test_blocks.py       ✅ done
├── uploads/                 ✅ done
├── logs/                    ✅ done
├── docker-compose.yml       ✅ done
├── .env                     ✅ done
├── .env.test                ✅ done
├── .env.example             ✅ done
├── .gitignore               ✅ done
├── requirements.txt         ✅ done
├── dev.md                   ✅ this file
└── README.md                ✅ done
```

---

## API Endpoints Plan

### Auth ✅

- `POST /api/v1/auth/register` ✅
- `POST /api/v1/auth/login` ✅
- `POST /api/v1/auth/google` ✅
- `POST /api/v1/auth/refresh` ✅
- `POST /api/v1/auth/logout` ✅
- `POST /api/v1/auth/complete-profile` ✅
- `POST /api/v1/auth/change-password` ✅
- `GET /api/v1/auth/health` ✅

### Users ✅

- `GET /api/v1/users/me` ✅
- `PUT /api/v1/users/me` ✅
- `DELETE /api/v1/users/me` ✅
- `POST /api/v1/users/me/location` ✅

### Photos ✅

- `POST /api/v1/users/me/photos` ✅
- `GET /api/v1/users/me/photos` ✅
- `DELETE /api/v1/users/me/photos/{id}` ✅
- `PUT /api/v1/users/me/photos/{id}/main` ✅

### Admin ✅

- `GET /api/v1/admin/photos/pending` ✅
- `POST /api/v1/admin/photos/{id}/approve` ✅
- `POST /api/v1/admin/photos/{id}/reject` ✅
- `GET /api/v1/admin/photos/stats` ✅
- `GET /api/v1/admin/photos/user/{user_id}` ✅

### Discover ✅

- `GET /api/v1/discover` — swipe feed (excludes swiped users) ✅

### Swipes ✅

- `POST /api/v1/swipes` — like or pass ✅
- `GET /api/v1/swipes/stats` — swipe statistics ✅

### Search ✅

- `GET /api/v1/search` — advanced search with filters ✅

### Blocks ✅

- `POST /api/v1/blocks/{user_id}/block` — block user ✅
- `POST /api/v1/blocks/{user_id}/unblock` — unblock user ✅
- `GET /api/v1/blocks` — list blocked users ✅

### Matches 🔲 Session 9

- `GET /api/v1/matches` — list my matches
- `GET /api/v1/matches/{id}` — get match details
- `WS /ws/matches` — realtime match notifications

### Messages 🔲 Session 10

- `GET /api/v1/messages/{match_id}` — get chat history
- `POST /api/v1/messages/{match_id}` — send message
- `POST /api/v1/messages/{match_id}/accept` — accept unmatched chat
- `WS /ws/chat/{match_id}` — realtime WebSocket chat

### Subscriptions 🔲 Session 11

- `POST /api/v1/subscriptions` — initiate purchase
- `POST /api/v1/subscriptions/verify` — verify payment
- `GET /api/v1/subscriptions/me` — get my subscription

### Rewards 🔲 Session 11

- `POST /api/v1/rewards/ad-watched` — claim ad reward
- `POST /api/v1/rewards/review` — submit store review proof

---

## Session Log

### Session 1
Stack decisions, monetization model, auth model, ERD design, Iranian market constraints.

### Session 2
Project bootstrapped, Docker Compose, all SQLAlchemy models, Alembic, FastAPI running.

### Session 3
Updated models, added daily_limit and review_reward, auth endpoints (register/login/google/refresh).

### Session 4
Auth system hardened: token versioning, jti, Redis retries, logging, pytest setup, 33 auth tests.

### Session 5
Users endpoints: GET/PUT/DELETE /users/me, POST /users/me/location. 20 users tests.

### Session 6
Photo upload system: validation, local storage, admin moderation endpoints, 13 photo tests.

### Session 7
Discover page + Swipe system: GET /discover, POST /swipes, match detection, daily like limits.

### Session 8 (COMPLETED)

**Completed:**
- `app/models/block.py` — Block model for user blocking
- `app/schemas/search.py` — Search filters and response schemas
- `app/api/v1/endpoints/search.py` — Advanced search with all filters
- `app/api/v1/endpoints/blocks.py` — Block/unblock endpoints
- `tests/test_search.py` — Search page tests
- `tests/test_blocks.py` — Block system tests
- Rate limiting disabled in test environment

**Search Filters Available:**
- Age range (18-100)
- Distance (1-500 km, optional)
- Gender (male/female, optional)
- Height range (50-250 cm, optional)
- Weight range (30-300 kg, optional)
- Has photos (yes/no, optional)
- Phone verified (yes/no, optional)
- Sorting (recent, distance, age, name)

**Block System Features:**
- Block users (prevents appearing in discover/search)
- Unblock users
- List all blocked users
- Blocks are permanent until unblocked

---

## Next Session Goals (Session 9)

1. **Match List Endpoint**
   - `GET /api/v1/matches` — list all active matches
   - Include last message preview
   - Sort by most recent message

2. **Match Details Endpoint**
   - `GET /api/v1/matches/{id}` — get match details with user profiles

3. **WebSocket Match Notifications**
   - `WS /ws/matches` — realtime notification when new match occurs
   - Send match event to both users

4. **Write tests** for matches endpoints and WebSocket

---

## Useful Commands

### Run tests
```bash
pytest tests/ -v
pytest tests/test_auth.py -v
pytest tests/test_users.py -v
pytest tests/test_photos.py -v
pytest tests/test_discover.py tests/test_swipes.py -v
pytest tests/test_search.py tests/test_blocks.py -v
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

- All implemented features have passing tests
- Rate limiting disabled in test environment
- Blocked users excluded from both Discover and Search
- Search supports all profile fields with optional filters
- Ready for Session 9: Match list + WebSocket notifications
```