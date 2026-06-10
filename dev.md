Here's the updated `dev.md` with all the future work added:

```markdown
# dev.md — Iranian Dating App

> **Purpose:** This file is the single source of truth for the project.  
> It is updated at the end of every session and passed to Claude at the start of the next one.  
> Claude should read this fully before doing anything in a new session.

---

## Project Status

- **Session:** 6 (Completed)
- **Current Phase:** Photo upload system fully implemented with admin review ✅
- **Next Phase:** Discover page + Swipe system (Like/Pass)

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

### Two Discovery Modes (Planned)

| Page | Purpose | Can see same user twice? |
|------|---------|-------------------------|
| **Discover (Swipe Page)** | Main swiping interface like Tinder | ❌ NO - once swiped (like/pass), gone forever |
| **Search Page** | Browse, filter, search for specific people | ✅ YES - can see again unless blocked |

### Matching Model

- Heterosexual only: males see females, females see males
- Swipe-based: like or pass
- Match = both users liked each other
- MVP algorithm: recency + distance only

### Daily Like Limits (Planned)

| User Type | Daily Likes |
|-----------|-------------|
| Free User | 50 likes per day |
| Premium User | Unlimited |
| Ad Reward | +5 bonus likes |

### Unmatched Chat Limits (Planned)

- Free users can send **2 messages** to any user without a match
- After 2 messages, recipient must accept the conversation
- Acceptance = explicit button tap ("Allow messages from this person")
- This prevents spam and harassment

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
- Implementation phase: after MVP core is stable

### 7. Unit Testing Strategy ✅ IMPLEMENTED

- Every feature must have unit tests before being considered done
- Test environment is fully isolated
- Using pytest + pytest-asyncio
- Using .env.test file for test config
- **66 tests written and passing** (33 auth + 20 users + 13 photos)

### 8. Review Reward System 🔲 Future

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
status        VARCHAR(20) DEFAULT 'pending'
reject_reason TEXT
face_verified BOOLEAN DEFAULT FALSE
created_at    TIMESTAMPTZ DEFAULT NOW()
```

### Table: `swipes` 🔲 Session 7

```sql
id          UUID PRIMARY KEY DEFAULT gen_random_uuid()
from_user   UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE
to_user     UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE
direction   VARCHAR(10) NOT NULL   -- 'like' | 'pass'
created_at  TIMESTAMPTZ DEFAULT NOW()
UNIQUE (from_user, to_user)
```

### Table: `matches` 🔲 Session 9

```sql
id          UUID PRIMARY KEY DEFAULT gen_random_uuid()
user1_id    UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE
user2_id    UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE
is_active   BOOLEAN DEFAULT TRUE
matched_at  TIMESTAMPTZ DEFAULT NOW()
UNIQUE (user1_id, user2_id)
```

### Table: `daily_limits` 🔲 Session 11

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

### Table: `blocks` 🔲 Session 8

```sql
id           UUID PRIMARY KEY DEFAULT gen_random_uuid()
blocker_id   UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE
blocked_id   UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE
created_at   TIMESTAMPTZ DEFAULT NOW()
UNIQUE (blocker_id, blocked_id)
```

### Table: `messages` 🔲 Session 10

```sql
id          UUID PRIMARY KEY DEFAULT gen_random_uuid()
match_id    UUID REFERENCES matches(id) ON DELETE CASCADE
sender_id   UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE
receiver_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE
content     TEXT NOT NULL
is_read     BOOLEAN DEFAULT FALSE
is_accepted BOOLEAN DEFAULT FALSE   -- for unmatched chats
sent_at     TIMESTAMPTZ DEFAULT NOW()
```

### Table: `subscriptions` 🔲 Session 11

```sql
id          UUID PRIMARY KEY DEFAULT gen_random_uuid()
user_id     UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE
status      VARCHAR(20) NOT NULL
plan        VARCHAR(50) NOT NULL
started_at  TIMESTAMPTZ NOT NULL
expires_at  TIMESTAMPTZ NOT NULL
source      VARCHAR(50)
```

### Table: `reports` 🔲 Session 8

```sql
id           UUID PRIMARY KEY DEFAULT gen_random_uuid()
reporter_id  UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE
reported_id  UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE
reason       TEXT NOT NULL
created_at   TIMESTAMPTZ DEFAULT NOW()
```

### Table: `review_rewards` 🔲 Future

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
│   │   ├── photos.py        ✅ done
│   │   ├── admin.py         ✅ done
│   │   ├── discover.py      🔲 Session 7
│   │   ├── swipes.py        🔲 Session 7
│   │   ├── search.py        🔲 Session 8
│   │   ├── blocks.py        🔲 Session 8
│   │   ├── matches.py       🔲 Session 9
│   │   ├── messages.py      🔲 Session 10
│   │   ├── subscriptions.py 🔲 Session 11
│   │   └── reports.py       🔲 Session 8
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
│   │   ├── swipe.py         🔲 Session 7
│   │   ├── match.py         🔲 Session 9
│   │   ├── daily_limit.py   🔲 Session 11
│   │   ├── block.py         🔲 Session 8
│   │   ├── message.py       🔲 Session 10
│   │   ├── subscription.py  🔲 Session 11
│   │   ├── report.py        🔲 Session 8
│   │   └── review_reward.py 🔲 Future
│   ├── schemas/
│   │   ├── auth.py          ✅ done
│   │   ├── user.py          ✅ done
│   │   ├── photo.py         ✅ done
│   │   ├── swipe.py         🔲 Session 7
│   │   ├── match.py         🔲 Session 9
│   │   └── message.py       🔲 Session 10
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
│   ├── test_discover.py     🔲 Session 7
│   ├── test_swipes.py       🔲 Session 7
│   ├── test_search.py       🔲 Session 8
│   ├── test_blocks.py       🔲 Session 8
│   ├── test_matches.py      🔲 Session 9
│   └── test_messages.py     🔲 Session 10
├── uploads/                 ✅ created
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

### Auth ✅ fully implemented

- `POST /api/v1/auth/register` ✅
- `POST /api/v1/auth/login` ✅
- `POST /api/v1/auth/google` ✅
- `POST /api/v1/auth/refresh` ✅
- `POST /api/v1/auth/logout` ✅
- `POST /api/v1/auth/complete-profile` ✅
- `POST /api/v1/auth/change-password` ✅
- `GET /api/v1/auth/health` ✅

### Users ✅ fully implemented

- `GET /api/v1/users/me` ✅
- `PUT /api/v1/users/me` ✅
- `DELETE /api/v1/users/me` ✅
- `POST /api/v1/users/me/location` ✅

### Photos ✅ fully implemented

- `POST /api/v1/users/me/photos` ✅
- `GET /api/v1/users/me/photos` ✅
- `DELETE /api/v1/users/me/photos/{id}` ✅
- `PUT /api/v1/users/me/photos/{id}/main` ✅

### Admin ✅ fully implemented

- `GET /api/v1/admin/photos/pending` ✅
- `POST /api/v1/admin/photos/{id}/approve` ✅
- `POST /api/v1/admin/photos/{id}/reject` ✅
- `GET /api/v1/admin/photos/stats` ✅
- `GET /api/v1/admin/photos/user/{user_id}` ✅

### Discover 🔲 Session 7

- `GET /api/v1/discover` — swipe feed (excludes swiped users)

### Swipes 🔲 Session 7

- `POST /api/v1/swipes` — like or pass on a user
- `GET /api/v1/swipes/stats` — get swipe stats

### Search 🔲 Session 8

- `GET /api/v1/search` — advanced search with filters

### Blocks 🔲 Session 8

- `POST /api/v1/users/{id}/block` — block a user
- `POST /api/v1/users/{id}/unblock` — unblock a user
- `GET /api/v1/blocks` — list blocked users

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

### Reports 🔲 Session 8

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
Stack decisions, monetization model, auth model, ERD design, Iranian market constraints.

### Session 2
Project bootstrapped, Docker Compose, all SQLAlchemy models, Alembic, FastAPI running.

### Session 3
Updated models, added daily_limit and review_reward, auth endpoints (register/login/google/refresh).

### Session 4
Auth system hardened: token versioning, jti, Redis retries, logging, pytest setup, 33 auth tests.

### Session 5
Users endpoints: GET/PUT/DELETE /users/me, POST /users/me/location. 20 users tests. Total 53 tests.

### Session 6 (COMPLETED)
Photo upload system: validation, local storage, admin moderation endpoints, 13 photo tests. Total 66 tests.

---

## Session 7 Goals (NEXT)

### Main Tasks

1. **Swipe Model** - create `app/models/swipe.py`
2. **Discover Endpoint** - `GET /api/v1/discover`
   - Only opposite gender
   - Age range filter (18-100)
   - Distance filter (default 50km)
   - Exclude already swiped users (like OR pass)
   - Exclude blocked users
   - Exclude deactivated users
   - Pagination (limit/offset)
   - Sort by distance + recency

3. **Swipe Endpoint** - `POST /api/v1/swipes`
   - Like or pass on a user
   - Prevent double swiping
   - Check daily like limit (free users: 50/day)
   - Create match record when both users like each other
   - Return match status

4. **Write tests** for discover and swipes

### Files Needed for Session 7

```
1. app/models/swipe.py (need to see if exists)
2. app/models/match.py (need to see if exists)
3. app/models/daily_limit.py (need to see if exists)
```

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
- Photos stored locally in `uploads/` folder
- Admin secret key must be set in `.env`
- Ready for Session 7: Discover + Swipe system

---

## Future Work (Backlog)

### Session 7
- [ ] Discover Page (GET /discover)
- [ ] Swipe System (POST /swipes)
- [ ] Basic match detection

### Session 8
- [ ] Search Page (GET /search with advanced filters)
- [ ] Block System (block/unblock users)
- [ ] Report System

### Session 9
- [ ] Match List (GET /matches)
- [ ] WebSocket Match Notifications

### Session 10
- [ ] Chat System (WebSocket + message history)
- [ ] Unmatched chat limit (2 messages per user)
- [ ] Chat acceptance flow

### Session 11
- [ ] Premium/Free user system
- [ ] Daily like limit (50/day for free users)
- [ ] Ad reward system (+5 likes, +1 chat per ad)
- [ ] Subscription management

### Session 12+
- [ ] Face verification (selfie match)
- [ ] Review reward system
- [ ] PostGIS for better location search
- [ ] Celery for background tasks
- [ ] Admin dashboard UI
- [ ] Push notifications
- [ ] Mobile app development (Flutter)
```

---

Now I'm ready for Session 7. Please send me:

```
1. app/models/swipe.py (if exists)
2. app/models/match.py (if exists)
3. app/models/daily_limit.py (if exists)
```

Once you send these, I'll start coding the Discover + Swipe system! 🚀