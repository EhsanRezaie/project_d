# dev.md — Iranian Dating App (Badoo-style)

> **Purpose:** Single source of truth for the entire project.  
> Updated at the end of every session. Pass this file to Claude at the start of every new session.  
> Claude must read this file fully before taking any action.

---

## Table of Contents

1. [Project Overview](#1-project-overview)
2. [Team & Timeline](#2-team--timeline)
3. [Tech Stack](#3-tech-stack)
4. [Repository Structure](#4-repository-structure)
5. [Environment & Configuration](#5-environment--configuration)
6. [Database Schema (Full)](#6-database-schema-full)
7. [API Reference (All Endpoints)](#7-api-reference-all-endpoints)
8. [Architecture Decisions & Patterns](#8-architecture-decisions--patterns)
9. [Business Rules](#9-business-rules)
10. [Session Progress & Roadmap](#10-session-progress--roadmap)
11. [Upcoming Session Plans (11–15)](#11-upcoming-session-plans-1115)
12. [Testing Strategy](#12-testing-strategy)
13. [Deployment Notes](#13-deployment-notes)

---

## 1. Project Overview

A **Persian-language dating app** for the Iranian market (similar to Badoo).

| Attribute | Detail |
|-----------|--------|
| Language | Persian (Farsi) UI, backend API in English |
| Target market | Iranian users worldwide (payment Iran-only) |
| Orientation | Heterosexual only (male ↔ female) |
| Monetization | Premium subscriptions + rewarded ads (NO forced interstitial ads) |
| Primary platform | Android first, iOS later (same Flutter codebase) |

---

## 2. Team & Timeline

| Field | Detail |
|-------|--------|
| Developer | Ehsan (solo) |
| Backend expertise | Senior — FastAPI & Django (FastAPI chosen) |
| Mobile | Learning Flutter from scratch |
| Daily availability | 2–3 hours/day |
| Estimated MVP | 3–4 months with Claude assistance |
| Session cadence | 1 session per working day; each session = 2–3 hrs focused work |

---

## 3. Tech Stack

| Layer | Tool | Reason |
|-------|------|--------|
| API framework | FastAPI (async) | High performance, native async, OpenAPI docs |
| Database | PostgreSQL 15 + PostGIS | Relational + geospatial queries |
| ORM | SQLAlchemy 2.x (async) | Async support, type safety |
| Migrations | Alembic | Schema versioning |
| Cache / Pub-Sub | Redis 7 | Rate limiting, refresh tokens, WS pub/sub, daily counters |
| Realtime | WebSocket (native FastAPI) | Chat + match + notification events |
| File storage | Local disk (MVP), S3-compatible later | User photos, voice messages |
| Containerization | Docker + Docker Compose | Dev parity, easy deployment |
| Mobile | Flutter (Dart) | Android/iOS single codebase |
| Payment | ZarinPal | Iran-only payment gateway |
| Push notifications | Firebase Cloud Messaging (FCM) | Session 15 |

---

## 4. Repository Structure

```
iranian-dating-app/
├── backend/
│   ├── app/
│   │   ├── main.py                        # FastAPI app factory, lifespan, routers
│   │   ├── config.py                      # Settings via pydantic-settings (.env)
│   │   ├── database.py                    # Async SQLAlchemy engine + session
│   │   ├── redis_client.py                # Redis connection pool
│   │   │
│   │   ├── models/                        # SQLAlchemy ORM models
│   │   │   ├── __init__.py                # Re-exports all models (required for Alembic)
│   │   │   ├── user.py                    # User ✅
│   │   │   ├── photo.py                   # Photo ✅
│   │   │   ├── swipe.py                   # Swipe ✅
│   │   │   ├── match.py                   # Match ✅
│   │   │   ├── block.py                   # Block ✅
│   │   │   ├── message.py                 # Message ✅
│   │   │   ├── subscription.py            # Subscription 🔲 Session 11
│   │   │   ├── referral_reward.py         # ReferralReward 🔲 Session 11
│   │   │   ├── notification.py            # Notification 🔲 Session 12
│   │   │   ├── report.py                  # Report 🔲 Session 12
│   │   │   └── ticket.py                  # Ticket 🔲 Session 13
│   │   │
│   │   ├── schemas/                       # Pydantic request/response schemas
│   │   │   ├── auth.py                    # ✅
│   │   │   ├── user.py                    # ✅
│   │   │   ├── photo.py                   # ✅
│   │   │   ├── swipe.py                   # ✅
│   │   │   ├── match.py                   # ✅
│   │   │   ├── message.py                 # ✅
│   │   │   ├── subscription.py            # 🔲 Session 11
│   │   │   ├── referral.py                # 🔲 Session 11
│   │   │   ├── notification.py            # 🔲 Session 12
│   │   │   ├── report.py                  # 🔲 Session 12
│   │   │   └── ticket.py                  # 🔲 Session 13
│   │   │
│   │   ├── api/
│   │   │   └── v1/
│   │   │       ├── router.py              # Aggregates all endpoint routers
│   │   │       └── endpoints/
│   │   │           ├── auth.py            # ✅ Login, register, refresh, revoke
│   │   │           ├── users.py           # ✅ Profile CRUD, me, update location
│   │   │           ├── photos.py          # ✅ Upload, delete, reorder
│   │   │           ├── admin_photos.py    # ✅ Approve/reject photo moderation
│   │   │           ├── discover.py        # ✅ Card stack discovery
│   │   │           ├── swipes.py          # ✅ Like/pass + daily limit check
│   │   │           ├── search.py          # ✅ Advanced filters
│   │   │           ├── matches.py         # ✅ Match list + details + WS
│   │   │           ├── blocks.py          # ✅ Block/unblock/list
│   │   │           ├── messages.py        # ✅ Chat REST endpoints
│   │   │           ├── ws_chat.py         # ✅ WebSocket /ws/chat/{match_id}
│   │   │           ├── subscriptions.py   # 🔲 Session 11
│   │   │           ├── rewards.py         # 🔲 Session 11
│   │   │           ├── referrals.py       # 🔲 Session 11 + 14
│   │   │           ├── notifications.py   # 🔲 Session 12
│   │   │           ├── reports.py         # 🔲 Session 12
│   │   │           ├── privacy.py         # 🔲 Session 12
│   │   │           ├── tickets.py         # 🔲 Session 13 (user-facing)
│   │   │           ├── admin_tickets.py   # 🔲 Session 13
│   │   │           ├── admin_reports.py   # 🔲 Session 13
│   │   │           └── admin_users.py     # 🔲 Session 13
│   │   │
│   │   ├── services/                      # Business logic (no DB access directly)
│   │   │   ├── auth_service.py            # ✅ Token logic, password hashing
│   │   │   ├── user_service.py            # ✅ Profile logic
│   │   │   ├── photo_service.py           # ✅ File validation, save, delete
│   │   │   ├── match_service.py           # ✅ Match creation logic
│   │   │   ├── chat_service.py            # ✅ Message delivery logic
│   │   │   ├── payment_service.py         # 🔲 Session 11 — ZarinPal integration
│   │   │   ├── reward_service.py          # 🔲 Session 11 — Ad reward logic
│   │   │   ├── notification_service.py    # 🔲 Session 12 — DB notifications
│   │   │   ├── push_service.py            # 🔲 Session 15 — FCM push
│   │   │   └── location_service.py        # 🔲 Session 14 — City/province utils
│   │   │
│   │   ├── core/
│   │   │   ├── security.py                # ✅ JWT encode/decode, password hash
│   │   │   ├── dependencies.py            # ✅ get_current_user, get_db, is_premium
│   │   │   ├── rate_limit.py              # ✅ slowapi setup + Redis limiter
│   │   │   ├── exceptions.py              # ✅ Custom HTTP exceptions
│   │   │   └── websocket_manager.py       # ✅ WS connection manager (chat + matches)
│   │   │
│   │   └── utils/
│   │       ├── geo.py                     # ✅ PostGIS distance helpers
│   │       ├── pagination.py              # ✅ Cursor-based pagination helper
│   │       └── iran_ip.py                 # 🔲 Session 11 — IP range check for payments
│   │
│   ├── alembic/
│   │   ├── env.py
│   │   ├── script.py.mako
│   │   └── versions/                      # Migration files
│   │
│   ├── tests/
│   │   ├── conftest.py                    # ✅ Fixtures: test DB, test client, users
│   │   ├── test_auth.py                   # ✅
│   │   ├── test_users.py                  # ✅
│   │   ├── test_photos.py                 # ✅
│   │   ├── test_swipes.py                 # ✅
│   │   ├── test_matches.py                # ✅
│   │   ├── test_messages.py               # ✅
│   │   ├── test_subscriptions.py          # 🔲 Session 11
│   │   ├── test_rewards.py                # 🔲 Session 11
│   │   ├── test_notifications.py          # 🔲 Session 12
│   │   ├── test_reports.py                # 🔲 Session 12
│   │   ├── test_tickets.py                # 🔲 Session 13
│   │   ├── test_admin.py                  # 🔲 Session 13
│   │   ├── test_referrals.py              # 🔲 Session 14
│   │   └── test_location.py               # 🔲 Session 14
│   │
│   ├── uploads/                           # Runtime file storage (gitignored)
│   │   └── users/{user_id}/{photo_id}.jpg
│   │
│   ├── .env                               # Local env vars (gitignored)
│   ├── .env.example                       # Template for new devs
│   ├── requirements.txt
│   ├── Dockerfile
│   └── docker-compose.yml
│
└── mobile/                                # Flutter app (Session 16+)
    └── ...
```

---

## 5. Environment & Configuration

### `.env` Variables

```env
# App
APP_ENV=development
SECRET_KEY=your-super-secret-key-here
ACCESS_TOKEN_EXPIRE_MINUTES=10080       # 7 days
REFRESH_TOKEN_EXPIRE_DAYS=30

# Database
DATABASE_URL=postgresql+asyncpg://user:pass@localhost:5432/dating_db

# Redis
REDIS_URL=redis://localhost:6379/0

# File Storage
UPLOADS_DIR=uploads
MAX_PHOTO_SIZE_MB=5
MAX_PHOTOS_PER_USER=6

# Payment (ZarinPal)
ZARINPAL_MERCHANT_ID=your-merchant-id
ZARINPAL_SANDBOX=true

# Firebase (Session 15)
FCM_SERVER_KEY=your-fcm-key

# Admin
ADMIN_SECRET_KEY=admin-bootstrap-token
```

### `config.py` Pattern

```python
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    app_env: str = "development"
    secret_key: str
    database_url: str
    redis_url: str
    access_token_expire_minutes: int = 10080
    refresh_token_expire_days: int = 30
    uploads_dir: str = "uploads"
    max_photo_size_mb: int = 5
    max_photos_per_user: int = 6
    zarinpal_merchant_id: str = ""
    zarinpal_sandbox: bool = True

    class Config:
        env_file = ".env"

settings = Settings()
```

---

## 6. Database Schema (Full)

### Existing Tables (Sessions 1–10) ✅

#### `users`
```sql
id                  UUID PRIMARY KEY DEFAULT gen_random_uuid()
email               VARCHAR(255) UNIQUE NOT NULL
hashed_password     VARCHAR(255)                          -- NULL for OAuth users
full_name           VARCHAR(100) NOT NULL
gender              VARCHAR(10) NOT NULL                  -- male / female
birth_date          DATE NOT NULL
bio                 TEXT
token_version       INTEGER DEFAULT 0                     -- for instant token revocation
is_active           BOOLEAN DEFAULT TRUE
is_verified         BOOLEAN DEFAULT FALSE
is_admin            BOOLEAN DEFAULT FALSE
is_profile_complete BOOLEAN DEFAULT FALSE                 -- FALSE for new OAuth users
google_id           VARCHAR(255) UNIQUE
last_seen           TIMESTAMPTZ
created_at          TIMESTAMPTZ DEFAULT NOW()
updated_at          TIMESTAMPTZ

-- Location (PostGIS)
location            GEOGRAPHY(POINT, 4326)                -- lat/lng for distance queries
location_updated_at TIMESTAMPTZ

-- To be added in Session 11/14:
-- premium_until, referral_code, referred_by, country, province, city, location_manual
-- hide_last_seen, hide_online_status
```

#### `photos`
```sql
id          UUID PRIMARY KEY DEFAULT gen_random_uuid()
user_id     UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE
file_path   VARCHAR(500) NOT NULL
is_main     BOOLEAN DEFAULT FALSE
status      VARCHAR(20) DEFAULT 'pending'   -- pending | approved | rejected
order_index SMALLINT DEFAULT 0
created_at  TIMESTAMPTZ DEFAULT NOW()
```

#### `swipes`
```sql
id          UUID PRIMARY KEY DEFAULT gen_random_uuid()
swiper_id   UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE
swiped_id   UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE
direction   VARCHAR(10) NOT NULL             -- like | pass
created_at  TIMESTAMPTZ DEFAULT NOW()
UNIQUE (swiper_id, swiped_id)
```

#### `matches`
```sql
id              UUID PRIMARY KEY DEFAULT gen_random_uuid()
user1_id        UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE
user2_id        UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE
chat_accepted   BOOLEAN DEFAULT FALSE        -- TRUE when both sides accept chat
created_at      TIMESTAMPTZ DEFAULT NOW()
UNIQUE (user1_id, user2_id)
```

#### `blocks`
```sql
id          UUID PRIMARY KEY DEFAULT gen_random_uuid()
blocker_id  UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE
blocked_id  UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE
created_at  TIMESTAMPTZ DEFAULT NOW()
UNIQUE (blocker_id, blocked_id)
```

#### `messages`
```sql
id              UUID PRIMARY KEY DEFAULT gen_random_uuid()
match_id        UUID NOT NULL REFERENCES matches(id) ON DELETE CASCADE
sender_id       UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE
message_type    VARCHAR(20) NOT NULL          -- text | photo | voice
content         TEXT                          -- text body OR file path
is_deleted      BOOLEAN DEFAULT FALSE
is_delivered    BOOLEAN DEFAULT FALSE
is_read         BOOLEAN DEFAULT FALSE
delivered_at    TIMESTAMPTZ
read_at         TIMESTAMPTZ
created_at      TIMESTAMPTZ DEFAULT NOW()
```

---

### Planned Tables (Sessions 11–14) 🔲

#### `subscriptions` (Session 11)
```sql
id              UUID PRIMARY KEY DEFAULT gen_random_uuid()
user_id         UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE
plan            VARCHAR(20) NOT NULL          -- monthly | quarterly | yearly
status          VARCHAR(20) NOT NULL          -- active | expired | cancelled
started_at      TIMESTAMPTZ NOT NULL
expires_at      TIMESTAMPTZ NOT NULL
source          VARCHAR(30) NOT NULL          -- purchase | referral | welcome_bonus | admin_grant
payment_id      VARCHAR(100)                  -- ZarinPal transaction ref
created_at      TIMESTAMPTZ DEFAULT NOW()
```

#### `referral_rewards` (Session 11 / 14)
```sql
id              UUID PRIMARY KEY DEFAULT gen_random_uuid()
inviter_id      UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE
invited_id      UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE
inviter_days    SMALLINT DEFAULT 3
invited_days    SMALLINT DEFAULT 3
created_at      TIMESTAMPTZ DEFAULT NOW()
UNIQUE (invited_id)                           -- each user can only be referred once
```

#### `notifications` (Session 12)
```sql
id          UUID PRIMARY KEY DEFAULT gen_random_uuid()
user_id     UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE
type        VARCHAR(50) NOT NULL              -- like | match | message | system
title       VARCHAR(200) NOT NULL
body        TEXT
data        JSONB                             -- e.g. {"match_id": "...", "user_id": "..."}
is_read     BOOLEAN DEFAULT FALSE
created_at  TIMESTAMPTZ DEFAULT NOW()
```

#### `reports` (Session 12)
```sql
id              UUID PRIMARY KEY DEFAULT gen_random_uuid()
reporter_id     UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE
reported_id     UUID NOT NULL REFERENCES users(id) ON DELETE SET NULL
reason          TEXT NOT NULL
status          VARCHAR(20) DEFAULT 'pending' -- pending | reviewed | action_taken
admin_note      TEXT
created_at      TIMESTAMPTZ DEFAULT NOW()
resolved_at     TIMESTAMPTZ
```

#### `tickets` (Session 13)
```sql
id              UUID PRIMARY KEY DEFAULT gen_random_uuid()
user_id         UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE
subject         VARCHAR(200) NOT NULL
message         TEXT NOT NULL
status          VARCHAR(20) DEFAULT 'open'    -- open | in_progress | closed
admin_response  TEXT
created_at      TIMESTAMPTZ DEFAULT NOW()
updated_at      TIMESTAMPTZ
```

---

### `users` Table Additions by Session

#### Session 11 additions
```sql
premium_until   TIMESTAMPTZ                   -- NULL = free user
referral_code   VARCHAR(20) UNIQUE            -- generated on registration
referred_by     UUID REFERENCES users(id) ON DELETE SET NULL
```

#### Session 12 additions
```sql
hide_last_seen      BOOLEAN DEFAULT FALSE
hide_online_status  BOOLEAN DEFAULT FALSE
```

#### Session 14 additions
```sql
country             VARCHAR(100)              -- Iran, Germany, USA, etc.
province            VARCHAR(100)              -- Tehran, Isfahan, etc.
city                VARCHAR(100)              -- Tehran, Shiraz, etc.
location_manual     BOOLEAN DEFAULT FALSE     -- TRUE when user set location manually
```

---

### Key Indexes

```sql
-- Performance indexes (add during relevant sessions)
CREATE INDEX idx_users_location ON users USING GIST(location);
CREATE INDEX idx_users_gender ON users(gender) WHERE is_active = TRUE;
CREATE INDEX idx_users_premium_until ON users(premium_until);
CREATE INDEX idx_swipes_swiper ON swipes(swiper_id);
CREATE INDEX idx_swipes_swiped ON swipes(swiped_id);
CREATE INDEX idx_messages_match ON messages(match_id, created_at DESC);
CREATE INDEX idx_notifications_user ON notifications(user_id, is_read, created_at DESC);
CREATE INDEX idx_reports_status ON reports(status);
```

---

## 7. API Reference (All Endpoints)

### Auth — `/api/v1/auth` ✅

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| POST | `/register` | No | Register with email/password + optional referral_code |
| POST | `/login` | No | Login → returns access + refresh tokens |
| POST | `/google` | No | Google OAuth login/register |
| POST | `/refresh` | No (refresh token in body) | Rotate refresh token |
| POST | `/logout` | Yes | Revoke current refresh token |
| POST | `/logout-all` | Yes | Increment token_version (revoke all sessions) |
| GET | `/health` | No | Redis health check |

### Users — `/api/v1/users` ✅

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| GET | `/me` | Yes | Current user profile |
| PATCH | `/me` | Yes | Update profile (name, bio, birth_date, etc.) |
| DELETE | `/me` | Yes | Soft-delete own account |
| GET | `/{user_id}` | Yes | Public profile of another user |
| PATCH | `/me/location` | Yes | Update lat/lng location |
| PATCH | `/me/location-text` | Yes | Update country/province/city (Session 14) |

### Photos — `/api/v1/photos` ✅

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| POST | `/` | Yes | Upload photo (max 6, pending review) |
| DELETE | `/{photo_id}` | Yes | Delete own photo |
| PATCH | `/reorder` | Yes | Change photo order |
| GET | `/admin/pending` | Admin | List pending photos |
| POST | `/admin/{photo_id}/approve` | Admin | Approve photo |
| POST | `/admin/{photo_id}/reject` | Admin | Reject photo |
| GET | `/admin/stats` | Admin | Photo moderation stats |

### Discover — `/api/v1/discover` ✅

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| GET | `/` | Yes | Card stack — excludes already-swiped users, filters by age + distance |

### Swipes — `/api/v1/swipes` ✅

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| POST | `/` | Yes | Like or pass a user. Checks daily limit. Creates match if mutual. |

### Search — `/api/v1/search` ✅

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| GET | `/` | Yes | Advanced search (age, distance, country, province, city, height, weight, verified, has_photos, online_status) |

### Matches — `/api/v1/matches` ✅

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| GET | `/` | Yes | List all matches with last message preview |
| GET | `/{match_id}` | Yes | Match detail with both user profiles |
| WS | `/ws/matches` | Yes (token param) | Real-time match + like notifications |

### Blocks — `/api/v1/blocks` ✅

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| POST | `/{user_id}/block` | Yes | Block a user |
| POST | `/{user_id}/unblock` | Yes | Unblock a user |
| GET | `/` | Yes | List blocked users |

### Messages — `/api/v1/messages` ✅

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| GET | `/{match_id}` | Yes | Paginated chat history |
| POST | `/{match_id}/text` | Yes | Send text message (checks chat limit) |
| POST | `/{match_id}/photo` | Yes | Send photo message |
| POST | `/{match_id}/voice` | Yes | Send voice message |
| POST | `/{match_id}/accept` | Yes | Accept chat request |
| POST | `/delivered` | Yes | Bulk mark messages as delivered |
| POST | `/read` | Yes | Bulk mark messages as read |
| DELETE | `/{message_id}` | Yes | Soft-delete own message |
| POST | `/{message_id}/forward` | Yes | Forward message to another match |
| GET | `/{message_id}/status` | Yes | Get delivery/read status |
| WS | `/ws/chat/{match_id}` | Yes (token param) | Real-time chat WebSocket |

### Subscriptions — `/api/v1/subscriptions` 🔲 Session 11

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| GET | `/plans` | No | List available subscription plans + prices |
| POST | `/purchase` | Yes | Initiate ZarinPal payment (Iran IP only) |
| POST | `/verify` | Yes | Verify ZarinPal callback + activate subscription |
| GET | `/my` | Yes | Current subscription status |
| POST | `/cancel` | Yes | Cancel auto-renewal |

### Rewards — `/api/v1/rewards` 🔲 Session 11

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| POST | `/ad-watched` | Yes | Claim ad reward (+5 likes, +3 chats). Max 2x/day. |
| GET | `/my-limits` | Yes | Current daily limits remaining |

### Referrals — `/api/v1/referrals` 🔲 Session 11 / 14

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| GET | `/my-code` | Yes | Get own referral code |
| POST | `/claim` | Yes | Claim referral code (after registration) |
| GET | `/stats` | Yes | How many referrals made + rewards earned |

### Notifications — `/api/v1/notifications` 🔲 Session 12

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| GET | `/` | Yes | List notifications (paginated) |
| POST | `/read` | Yes | Mark notification(s) as read |
| DELETE | `/{notification_id}` | Yes | Delete a notification |
| POST | `/device-token` | Yes | Register FCM device token (Session 15) |

### Reports — `/api/v1/reports` 🔲 Session 12

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| POST | `/{user_id}` | Yes | Report a user (reason required) |
| GET | `/my` | Yes | List own submitted reports |

### Privacy — `/api/v1/privacy` 🔲 Session 12

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| PATCH | `/settings` | Yes | Update hide_last_seen, hide_online_status |
| GET | `/settings` | Yes | Get current privacy settings |

### Tickets — `/api/v1/tickets` 🔲 Session 13

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| POST | `/` | Yes | Submit support ticket |
| GET | `/` | Yes | List own tickets |
| GET | `/{ticket_id}` | Yes | Ticket detail |

### Admin — `/api/v1/admin` 🔲 Session 13

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| GET | `/tickets` | Admin | All tickets (filter by status) |
| PATCH | `/tickets/{id}` | Admin | Respond and update ticket status |
| GET | `/reports` | Admin | All reports (filter by status) |
| PATCH | `/reports/{id}` | Admin | Review + take action on report |
| GET | `/users` | Admin | User list with filters |
| PATCH | `/users/{id}` | Admin | Activate / deactivate user |
| DELETE | `/users/{id}` | Admin | Permanently delete user (hard delete) |
| POST | `/users/{id}/grant-premium` | Admin | Manually grant premium days |

---

## 8. Architecture Decisions & Patterns

### 8.1 Authentication Flow

```
Register/Login → access_token (JWT, 7d) + refresh_token (opaque, stored in Redis 30d)
         ↓
API call → Bearer {access_token} in Authorization header
         ↓
access_token expires → POST /auth/refresh with refresh_token body
         ↓
New access_token + new refresh_token (old refresh_token deleted from Redis — rotation)
         ↓
Logout → delete refresh_token from Redis
Logout-all → increment user.token_version (invalidates all existing JWTs immediately)
```

- **Redis key for refresh tokens:** `refresh:{token_hash}` → `user_id` with TTL 30 days
- **Token versioning:** JWT payload contains `token_version`. If `user.token_version > jwt.token_version` → token is revoked.
- **Google OAuth:** Creates user with `is_profile_complete=False`; frontend forces profile completion before accessing app.

### 8.2 Rate Limiting

- Library: `slowapi` with Redis backend
- Applied per-endpoint at the decorator level
- Test environment: rate limiting disabled via `TESTING=true` env var
- Redis key pattern: `ratelimit:{endpoint}:{user_ip_or_id}`

### 8.3 Daily Limits (Redis Counters)

Free user daily actions tracked in Redis with midnight TTL:

```
Key: daily_likes:{user_id}:{YYYY-MM-DD}    TTL: until midnight (Iran time, UTC+3:30)
Key: daily_chats:{user_id}:{YYYY-MM-DD}    TTL: until midnight
Key: daily_ad_rewards:{user_id}:{YYYY-MM-DD}  TTL: until midnight (max 2)
```

- Check in swipe endpoint: `GET daily_likes → if >= 20 and not premium → 429`
- Check in message endpoint: `GET daily_chats → if >= 10 and not premium → 429`
- Premium check: `user.premium_until > now()` → skip limit check
- Ad reward: increment both `daily_likes += 5` and `daily_chats += 3`; check `daily_ad_rewards < 2`

### 8.4 Photo System

```
Upload → validate (size ≤ 5MB, dimensions ≥ 200x200, JPEG/PNG/WEBP)
       → save to uploads/users/{user_id}/{uuid}.jpg
       → create Photo record with status=pending
       → admin reviews → approve or reject
       → first approved photo auto-set as is_main=True
```

### 8.5 Discovery Algorithm

```
GET /discover:
  1. Filter by gender (opposite gender only)
  2. Filter is_active=True, is_verified can vary
  3. Exclude already-swiped users (subquery on swipes table)
  4. Exclude blocked/blocking users
  5. Filter by age range (birth_date calculation)
  6. Filter by distance (PostGIS ST_DWithin on location GEOGRAPHY)
  7. Order by: distance ASC, last_seen DESC
  8. Return paginated card stack (default 20)
```

### 8.6 WebSocket Architecture

Two WS connections per active user:

| Connection | Path | Purpose |
|------------|------|---------|
| Match WS | `/ws/matches?token=...` | Match events, like notifications |
| Chat WS | `/ws/chat/{match_id}?token=...` | Real-time messages in a specific match |

Manager pattern (`websocket_manager.py`):
```python
class WebSocketManager:
    # match_connections: Dict[user_id, WebSocket]
    # chat_connections: Dict[match_id, Dict[user_id, WebSocket]]

    async def broadcast_match(user_id, event: dict)
    async def broadcast_chat(match_id, sender_id, event: dict)
    async def send_personal(user_id, event: dict)
```

Redis pub/sub used for multi-worker deployments (future horizontal scaling).

### 8.7 Chat Flow

```
User A sends message:
  1. POST /messages/{match_id}/text  OR  WS send event
  2. Validate match exists + both users are participants
  3. Check daily_chats limit (free users, new match only)
  4. Save Message to DB
  5. If recipient is connected on WS → send live event
  6. Else → create Notification record (+ push via FCM in Session 15)
  7. Update match.last_message_preview (for match list)
```

### 8.8 Subscription & Premium Logic

```python
# Helper used everywhere
def is_premium(user: User) -> bool:
    return user.premium_until is not None and user.premium_until > datetime.utcnow()
```

Premium activation flow:
```
POST /subscriptions/purchase (Iran IP only)
  → Create ZarinPal payment request
  → Return redirect URL to frontend

ZarinPal redirects to /subscriptions/verify?Authority=...&Status=OK
  → Verify with ZarinPal API
  → Create Subscription record
  → Set user.premium_until = now() + plan_duration
  → Return success to frontend
```

### 8.9 Location Architecture

- **Backend stores:** `location` (PostGIS GEOGRAPHY point for distance queries) + `country`, `province`, `city` (text for display/filtering)
- **Frontend responsibility:** Convert city name → approximate lat/lng coordinates (using geocoding API or static lookup table), send both to backend
- **Endpoint:** `PATCH /users/me/location` accepts `{lat, lng, country, province, city}`
- **Distance queries:** Use `ST_DWithin(location, ST_Point(lng, lat)::GEOGRAPHY, distance_meters)`
- **location_manual=True** when user explicitly set location (vs auto-detected from IP)

### 8.10 Dependency Injection Pattern

```python
# core/dependencies.py

async def get_db() -> AsyncSession: ...          # DB session per request
async def get_current_user(token, db) -> User: ... # Validates JWT + token_version
async def get_current_premium_user(user) -> User: # Raises 403 if not premium
async def get_admin_user(user) -> User: ...       # Raises 403 if not admin
```

---

## 9. Business Rules

### Free User Daily Limits

| Action | Daily Limit | Ad Bonus | Max Ad Bonus/Day |
|--------|------------|----------|-----------------|
| Likes (swipes) | 20 | +5 per ad | 2 ads/day → max +10 |
| New chat initiations | 10 | +3 per ad | 2 ads/day → max +6 |

### Premium User

| Feature | Premium |
|---------|---------|
| Likes | Unlimited |
| New chats | Unlimited |
| Ads shown | None |
| See who liked them | ✅ |
| Advanced filters | ✅ (TBD) |

### Subscription Plans

| Plan | Duration | Notes |
|------|----------|-------|
| Monthly | 30 days | |
| Quarterly | 90 days | ~15% discount |
| Yearly | 365 days | ~30% discount |

### Rewards & Bonuses

| Trigger | Reward |
|---------|--------|
| New user registration | 7 days free premium (welcome bonus) |
| Referral — inviter | +3 days premium (stacked on current premium_until) |
| Referral — new user | +3 days premium (stacked on top of welcome 7 days = 10 days total) |
| Watch rewarded ad | +5 likes + +3 new chats (max 2 ads/day) |

### Referral System Rules

- Referral code generated at registration (8-char alphanumeric, unique)
- New user can enter referral code at registration OR within first 24 hours via `POST /referrals/claim`
- Each user can only be referred once (`UNIQUE (invited_id)` on referral_rewards)
- Reward is always days stacked onto `premium_until` (never reset, always extend)

### Payment Rules

- ZarinPal only
- Payment endpoint IP-restricted to Iran
- Rest of the app fully accessible worldwide
- Subscriptions from non-Iran markets: manual admin grant for now (future: Stripe)

### Content Moderation Rules

- All photos require admin approval before visible to other users
- First approved photo auto-set as main photo
- Rejected photos: user notified (notification or in-app message)
- Admin can deactivate user account (soft-ban) with optional message to user

---

## 10. Session Progress & Roadmap

| Session | Focus | Status | Notes |
|---------|-------|--------|-------|
| 1–2 | Project setup, Docker, base models | ✅ | |
| 3 | Auth endpoints | ✅ | |
| 4 | Auth hardening (token versioning, logging, tests) | ✅ | |
| 5 | Users endpoints + profile CRUD | ✅ | |
| 6 | Photo upload + admin moderation | ✅ | |
| 7 | Discover + Swipe system | ✅ | |
| 8 | Search + Block system | ✅ | |
| 9 | Match list + WebSocket match notifications | ✅ | |
| 10 | Full chat system (REST + WebSocket) | ✅ | |
| **11** | **Premium subscriptions + Daily limits + Ad rewards** | 🔲 | Next |
| **12** | **Notifications + Privacy settings + Reports** | 🔲 | |
| **13** | **Admin panel (Tickets + Reports + User management)** | 🔲 | |
| **14** | **Referral system + Welcome bonus + Location text fields** | 🔲 | |
| **15** | **Push notifications (FCM) + Performance optimization** | 🔲 | |
| **16+** | **Flutter mobile app** | 🔲 | |

---

## 11. Upcoming Session Plans (11–15)

---

### Session 11: Premium Subscriptions + Daily Limits + Ad Rewards

**Goal:** Monetization foundation — enforce free limits, allow ad boosts, enable ZarinPal purchases.

#### DB Changes
```sql
ALTER TABLE users ADD COLUMN premium_until TIMESTAMPTZ;
ALTER TABLE users ADD COLUMN referral_code VARCHAR(20) UNIQUE;
ALTER TABLE users ADD COLUMN referred_by UUID REFERENCES users(id) ON DELETE SET NULL;

CREATE TABLE subscriptions ( ... );   -- see schema above
CREATE TABLE referral_rewards ( ... ); -- see schema above
```

#### New Files
| File | Purpose |
|------|---------|
| `app/models/subscription.py` | Subscription ORM model |
| `app/models/referral_reward.py` | ReferralReward ORM model |
| `app/schemas/subscription.py` | Plan list, purchase request/response, status |
| `app/schemas/referral.py` | Referral claim request, stats response |
| `app/api/v1/endpoints/subscriptions.py` | `/plans`, `/purchase`, `/verify`, `/my`, `/cancel` |
| `app/api/v1/endpoints/rewards.py` | `/ad-watched`, `/my-limits` |
| `app/api/v1/endpoints/referrals.py` | `/my-code`, `/claim`, `/stats` |
| `app/services/payment_service.py` | ZarinPal API calls (request + verify) |
| `app/services/reward_service.py` | `grant_premium_days()`, `claim_ad_reward()`, `check_daily_limit()` |
| `app/utils/iran_ip.py` | `is_iran_ip(ip: str) -> bool` |
| `tests/test_subscriptions.py` | Plan listing, purchase flow, verify |
| `tests/test_rewards.py` | Ad reward cap, daily limit enforcement |

#### Files to Update
| File | Change |
|------|--------|
| `app/api/v1/endpoints/auth.py` | On register: generate `referral_code`, grant 7-day welcome premium, handle optional `referral_code` input |
| `app/api/v1/endpoints/swipes.py` | Call `check_daily_limit(user, 'likes')` before recording swipe |
| `app/services/chat_service.py` | Call `check_daily_limit(user, 'chats')` before allowing new chat initiation |
| `app/core/dependencies.py` | Add `get_current_premium_user` dependency |
| `alembic/versions/` | New migration file |

#### Key Implementation Notes

```python
# reward_service.py

DAILY_LIKES_FREE = 20
DAILY_CHATS_FREE = 10
AD_REWARD_LIKES = 5
AD_REWARD_CHATS = 3
AD_REWARD_MAX_PER_DAY = 2

def get_redis_limit_key(user_id: str, action: str) -> str:
    today = date.today().isoformat()      # e.g. "2025-01-15"
    return f"daily_{action}:{user_id}:{today}"

async def check_daily_limit(user: User, action: str, redis: Redis) -> bool:
    if is_premium(user):
        return True  # no limit
    key = get_redis_limit_key(str(user.id), action)
    limit = DAILY_LIKES_FREE if action == "likes" else DAILY_CHATS_FREE
    count = int(await redis.get(key) or 0)
    return count < limit

async def increment_daily_counter(user_id: str, action: str, redis: Redis):
    key = get_redis_limit_key(user_id, action)
    pipe = redis.pipeline()
    pipe.incr(key)
    pipe.expireat(key, next_midnight_iran())   # TTL until midnight Iran time (UTC+3:30)
    await pipe.execute()
```

```python
# payment_service.py (ZarinPal)

ZARINPAL_REQUEST_URL = "https://api.zarinpal.com/pg/v4/payment/request.json"
ZARINPAL_VERIFY_URL  = "https://api.zarinpal.com/pg/v4/payment/verify.json"
ZARINPAL_GATE_URL    = "https://www.zarinpal.com/pg/StartPay/{authority}"

async def create_payment(user_id, amount_rials, description, callback_url) -> str:
    # Returns redirect URL

async def verify_payment(authority: str, amount_rials: int) -> dict:
    # Returns {"ref_id": ..., "card_pan": ...} or raises
```

#### Tests Checklist
- [ ] Free user hits 20 like limit → 429 response
- [ ] Premium user has no like limit
- [ ] Ad reward increments counters correctly
- [ ] Ad reward max 2x/day enforced
- [ ] Limits reset after midnight
- [ ] Welcome premium granted on registration
- [ ] ZarinPal payment flow (mock in tests)

---

### Session 12: Notifications + Privacy Settings + Reports

**Goal:** In-app notification system, user privacy controls, user reporting.

#### DB Changes
```sql
ALTER TABLE users ADD COLUMN hide_last_seen BOOLEAN DEFAULT FALSE;
ALTER TABLE users ADD COLUMN hide_online_status BOOLEAN DEFAULT FALSE;

CREATE TABLE notifications ( ... );   -- see schema above
CREATE TABLE reports ( ... );          -- see schema above
```

#### New Files
| File | Purpose |
|------|---------|
| `app/models/notification.py` | Notification ORM model |
| `app/models/report.py` | Report ORM model |
| `app/schemas/notification.py` | Notification list, read request |
| `app/schemas/report.py` | Report create request |
| `app/api/v1/endpoints/notifications.py` | List, read, delete notifications |
| `app/api/v1/endpoints/reports.py` | Submit report |
| `app/api/v1/endpoints/privacy.py` | PATCH/GET privacy settings |
| `app/services/notification_service.py` | `create_notification()`, `notify_like()`, `notify_match()`, `notify_message()` |
| `tests/test_notifications.py` | Notification CRUD |
| `tests/test_reports.py` | Submit + list reports |

#### Files to Update
| File | Change |
|------|--------|
| `app/api/v1/endpoints/swipes.py` | Call `notify_like()` when user A likes user B |
| `app/services/match_service.py` | Call `notify_match()` on match creation |
| `app/services/chat_service.py` | Call `notify_message()` when recipient is offline |
| `app/schemas/user.py` | Respect `hide_last_seen` and `hide_online_status` in public profile response |

#### Key Implementation Notes

```python
# notification_service.py

async def create_notification(db, user_id, type, title, body, data=None):
    notif = Notification(user_id=user_id, type=type, title=title, body=body, data=data)
    db.add(notif)
    await db.commit()
    # In Session 15: also trigger FCM push here

async def notify_like(db, liker: User, liked_user_id: UUID):
    # Only notify if liked_user is premium (seeing likes is premium feature)
    liked_user = await get_user(db, liked_user_id)
    if is_premium(liked_user):
        await create_notification(db, liked_user_id, "like",
            title="کسی شما را لایک کرد",
            body=f"{liker.full_name} شما را لایک کرد",
            data={"user_id": str(liker.id)}
        )
```

```python
# Privacy: respect in public profile schema
class PublicUserResponse(BaseModel):
    id: UUID
    full_name: str
    last_seen: Optional[datetime]        # None if hide_last_seen=True
    is_online: Optional[bool]            # None if hide_online_status=True
```

#### Tests Checklist
- [ ] Like creates notification for premium recipient
- [ ] Like does NOT create notification for free recipient
- [ ] Match creates notification for both users
- [ ] Message creates notification for offline recipient
- [ ] Privacy: last_seen hidden when hide_last_seen=True
- [ ] Privacy: online_status hidden when hide_online_status=True
- [ ] Report submitted successfully
- [ ] User cannot report same person twice (within 24h)

---

### Session 13: Admin Panel

**Goal:** Admin tools for content moderation, user management, and support tickets.

#### DB Changes
```sql
CREATE TABLE tickets ( ... );   -- see schema above
-- reports table already created in Session 12
```

#### New Files
| File | Purpose |
|------|---------|
| `app/models/ticket.py` | Ticket ORM model |
| `app/schemas/ticket.py` | Ticket create, list, detail, admin response |
| `app/api/v1/endpoints/tickets.py` | User: submit + list + view tickets |
| `app/api/v1/endpoints/admin_tickets.py` | Admin: list all, respond, close |
| `app/api/v1/endpoints/admin_reports.py` | Admin: list, review, take action |
| `app/api/v1/endpoints/admin_users.py` | Admin: list, activate/deactivate, delete, grant premium |
| `tests/test_tickets.py` | Ticket submission + listing |
| `tests/test_admin.py` | Admin actions (requires admin user fixture) |

#### Files to Update
| File | Change |
|------|--------|
| `app/core/dependencies.py` | `get_admin_user` dependency already exists; verify it's tested |
| `app/models/user.py` | No change needed (is_admin already exists) |

#### Key Admin Actions
```
Admin deactivates user:
  1. Set user.is_active = False
  2. Revoke all sessions (increment token_version)
  3. Optionally send system notification with reason

Admin permanently deletes user:
  1. Soft-delete must exist for > 7 days cooldown
  2. Delete all photos from disk
  3. Anonymize messages (set sender name to "Deleted User")
  4. Hard-delete user record

Admin grants premium:
  1. POST /admin/users/{id}/grant-premium with {"days": 30}
  2. Extend premium_until by N days
  3. Create subscription record with source="admin_grant"
```

#### Tests Checklist
- [ ] Non-admin cannot access admin endpoints (403)
- [ ] Admin can list + respond to tickets
- [ ] Admin can deactivate + reactivate users
- [ ] Admin can view + action reports
- [ ] Deactivating user revokes all tokens
- [ ] Admin can grant premium days

---

### Session 14: Referral System + Location Text Fields + Welcome Bonus

**Goal:** Complete referral system, add text-based location fields for filtering.

**Note:** Welcome bonus (7 days) and referral_code generation are already added in Session 11.
This session completes the referral claim flow and adds country/province/city fields.

#### DB Changes
```sql
ALTER TABLE users
  ADD COLUMN country VARCHAR(100),
  ADD COLUMN province VARCHAR(100),
  ADD COLUMN city VARCHAR(100),
  ADD COLUMN location_manual BOOLEAN DEFAULT FALSE;
```

#### New Files
| File | Purpose |
|------|---------|
| `app/services/location_service.py` | City/province validation, province list for Iran |
| `tests/test_referrals.py` | Referral claim, duplicate prevention, reward stacking |
| `tests/test_location.py` | Location update, search by province/city |

#### Files to Update
| File | Change |
|------|--------|
| `app/api/v1/endpoints/users.py` | `PATCH /me/location-text` endpoint; include country/province/city in profile response |
| `app/api/v1/endpoints/search.py` | Add `province` and `city` query params to search filters |
| `app/models/user.py` | Add country, province, city, location_manual columns |
| `app/api/v1/endpoints/referrals.py` | Complete `/claim` endpoint: validate code, prevent double-claim, apply rewards |
| `alembic/versions/` | New migration |

#### Location Flow Detail
```
Frontend:
  1. User selects city from dropdown (e.g. "تهران" → Tehran)
  2. Frontend looks up approximate lat/lng (e.g. 35.6892, 51.3890)
  3. PATCH /users/me/location  body: {lat, lng, country, province, city}
  
Backend:
  1. Update location GEOGRAPHY(POINT) from lat/lng
  2. Update country, province, city text fields
  3. Set location_updated_at, location_manual=True
```

#### Tests Checklist
- [ ] Referral claim applies rewards to both inviter and invited
- [ ] Referral code cannot be claimed twice
- [ ] User cannot use their own referral code
- [ ] Premium days stack correctly (welcome + referral = 10 days)
- [ ] Location text fields saved correctly
- [ ] Search by province returns correct users
- [ ] Search by city returns correct users

---

### Session 15: Push Notifications + Performance Optimization

**Goal:** Real push notifications via FCM, add missing indexes, finalize OpenAPI docs.

#### New Files
| File | Purpose |
|------|---------|
| `app/services/push_service.py` | FCM send_push(), send_to_topic() |
| `app/models/device_token.py` | Store FCM tokens per user/device |

#### Files to Update
| File | Change |
|------|--------|
| `app/services/notification_service.py` | Call push_service after creating DB notification |
| `app/api/v1/endpoints/notifications.py` | Add `POST /device-token` endpoint |

#### Performance Work
```sql
-- Add all indexes from Section 6 "Key Indexes"
-- Review slow query log
-- Add DB connection pooling config (pool_size=10, max_overflow=20)
-- Add Redis connection pool limits
```

#### API Documentation
- Ensure all endpoints have proper OpenAPI `summary`, `description`, `response_model`
- Add example request/response bodies
- Export final OpenAPI spec as `api_spec.json`

---

## 12. Testing Strategy

### Setup (`conftest.py`)

```python
# Fixtures available in all tests:
# - async_client: TestClient with real DB (test schema)
# - db_session: async DB session
# - test_user_male: active male user with approved photo
# - test_user_female: active female user with approved photo
# - premium_user: user with premium_until = now() + 30 days
# - admin_user: user with is_admin=True
# - auth_headers(user): {"Authorization": "Bearer {token}"}
```

### Conventions

- Each test file mirrors its endpoint file (e.g. `test_swipes.py` ↔ `swipes.py`)
- Test DB is separate from dev DB (`TEST_DATABASE_URL` env var)
- Rate limiting disabled in tests (`TESTING=true`)
- Each test is fully isolated (rollback or truncate between tests)
- Use `pytest-asyncio` with `asyncio_mode=auto`

### Test Coverage Targets

| Module | Target |
|--------|--------|
| Auth | 95% |
| Core business logic (swipes, matches, limits) | 90% |
| Chat | 85% |
| Admin | 80% |
| Payment (ZarinPal) | 70% (mocked) |

---

## 13. Deployment Notes

### Docker Compose Services

```yaml
services:
  api:       # FastAPI app (uvicorn)
  db:        # PostgreSQL 15 + PostGIS
  redis:     # Redis 7
  nginx:     # Reverse proxy (production only)
```

### Startup Order
`db` + `redis` must be healthy before `api` starts.
Use `depends_on` with `condition: service_healthy` and healthchecks.

### Alembic Migration Workflow
```bash
# Generate migration after model changes:
alembic revision --autogenerate -m "add premium fields to users"

# Apply migrations:
alembic upgrade head

# Rollback one step:
alembic downgrade -1
```

### File Storage
- **MVP:** Local disk at `uploads/` (bind-mounted in Docker)
- **Production:** Migrate to S3-compatible storage (e.g. Arvan Cloud Object Storage for Iran)
- File paths stored in DB as relative paths; prepend base URL in response schema

### Environment Files
- `.env` — local dev (gitignored)
- `.env.test` — test environment
- `.env.example` — committed to repo, template for new devs
- Production secrets via Docker secrets or Vault (not in repo)

---

## Quick Reference: Redis Key Patterns

| Key | Value | TTL | Purpose |
|-----|-------|-----|---------|
| `refresh:{token_hash}` | `user_id` | 30 days | Refresh token store |
| `daily_likes:{user_id}:{date}` | integer | until midnight Iran | Daily swipe counter |
| `daily_chats:{user_id}:{date}` | integer | until midnight Iran | Daily chat counter |
| `daily_ad_rewards:{user_id}:{date}` | integer | until midnight Iran | Ad reward cap counter |
| `ratelimit:{endpoint}:{ip}` | counter | per window | Rate limit tracking |
| `ws:match:{user_id}` | connection info | session | WS match connection |

---

## Quick Reference: HTTP Error Codes

| Code | When |
|------|------|
| 400 | Validation error, bad input |
| 401 | Missing or invalid token |
| 403 | Valid token but insufficient permissions (not admin, not premium) |
| 404 | Resource not found |
| 409 | Conflict (duplicate swipe, already blocked, etc.) |
| 422 | Pydantic validation error |
| 429 | Rate limit or daily limit exceeded |
| 451 | Payment endpoint accessed from outside Iran (legal restriction) |

---

*Last updated: End of Session 10*  
*Next session: Session 11 — Premium subscriptions + Daily limits + Ad rewards*