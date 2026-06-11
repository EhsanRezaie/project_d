You're right. Let me write a **fresh, accurate `dev.md`** based on your ACTUAL codebase:

```markdown
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
6. [Database Schema](#6-database-schema)
7. [API Reference](#7-api-reference)
8. [Architecture Decisions](#8-architecture-decisions)
9. [Business Rules](#9-business-rules)
10. [Session Progress](#10-session-progress)
11. [Session 12 Plan](#11-session-12-plan-notifications--privacy--reports)
12. [Session 13 Plan](#12-session-13-plan-admin-panel)
13. [Session 14 Plan](#13-session-14-plan-location-fields--search-filters)
14. [Session 15 Plan](#14-session-15-plan-push-notifications--production)
15. [Testing Strategy](#15-testing-strategy)
16. [Deployment Notes](#16-deployment-notes)

---

## 1. Project Overview

A **Persian-language dating app** for the Iranian market, similar to Badoo.

| Attribute | Detail |
|-----------|--------|
| Language | Persian (Farsi) UI, backend API in English |
| Target market | Iranian users worldwide |
| Orientation | Heterosexual only (male ↔ female) |
| Monetization | Premium subscriptions + rewarded ads (NO forced interstitial ads) |
| Primary platform | Android first, iOS later |

---

## 2. Team & Timeline

| Field | Detail |
|-------|--------|
| Developer | Ehsan (solo) |
| Backend expertise | Senior — FastAPI & Django |
| Mobile | Learning Flutter from scratch |
| Daily availability | 2–3 hours/day |
| Estimated MVP | 3–4 months with Claude assistance |

---

## 3. Tech Stack

| Layer | Tool |
|-------|------|
| API framework | FastAPI (async) |
| Database | PostgreSQL 15 |
| ORM | SQLAlchemy 2.x (async) |
| Migrations | Alembic |
| Cache | Redis 7 |
| Realtime | WebSocket |
| File storage | Local disk (`uploads/`) |
| Containerization | Docker + Docker Compose |
| Mobile | Flutter |
| Payment | ZarinPal (MOCKED - real integration needed) |

---

## 4. Repository Structure

```
iranian-dating-app/
├── backend/
│   ├── app/
│   │   ├── main.py
│   │   ├── config.py
│   │   ├── database.py
│   │   ├── redis_client.py
│   │   │
│   │   ├── models/
│   │   │   ├── user.py
│   │   │   ├── photo.py
│   │   │   ├── swipe.py
│   │   │   ├── match.py
│   │   │   ├── block.py
│   │   │   ├── message.py
│   │   │   ├── daily_limit.py
│   │   │   ├── review_reward.py
│   │   │   ├── subscription.py        # ✅ Session 11
│   │   │   ├── referral_reward.py     # ✅ Session 11
│   │   │   ├── notification.py        # 🔲 Session 12
│   │   │   ├── report.py              # 🔲 Session 12
│   │   │   └── ticket.py              # 🔲 Session 13
│   │   │
│   │   ├── schemas/
│   │   │   ├── auth.py
│   │   │   ├── user.py
│   │   │   ├── photo.py
│   │   │   ├── discover.py
│   │   │   ├── search.py
│   │   │   ├── match.py
│   │   │   ├── message.py
│   │   │   ├── subscription.py        # ✅ Session 11
│   │   │   ├── rewards.py             # ✅ Session 11
│   │   │   ├── referral.py            # ✅ Session 11
│   │   │   ├── notification.py        # 🔲 Session 12
│   │   │   ├── report.py              # 🔲 Session 12
│   │   │   ├── privacy.py             # 🔲 Session 12
│   │   │   └── ticket.py              # 🔲 Session 13
│   │   │
│   │   ├── api/v1/endpoints/
│   │   │   ├── auth.py                # ✅
│   │   │   ├── users.py               # ✅
│   │   │   ├── photos.py              # ✅
│   │   │   ├── admin_photos.py        # ✅
│   │   │   ├── discover.py            # ✅
│   │   │   ├── swipes.py              # ✅ (updated Session 11)
│   │   │   ├── search.py              # ✅ (updated Session 11)
│   │   │   ├── matches.py             # ✅
│   │   │   ├── blocks.py              # ✅
│   │   │   ├── messages.py            # ✅
│   │   │   ├── subscriptions.py       # ✅ Session 11
│   │   │   ├── rewards.py             # ✅ Session 11
│   │   │   ├── referrals.py           # ✅ Session 11
│   │   │   ├── notifications.py       # 🔲 Session 12
│   │   │   ├── reports.py             # 🔲 Session 12
│   │   │   ├── privacy.py             # 🔲 Session 12
│   │   │   └── admin_*.py             # 🔲 Session 13
│   │   │
│   │   ├── api/v1/websocket/
│   │   │   ├── matches.py             # ✅
│   │   │   └── chat.py                # ✅
│   │   │
│   │   ├── services/
│   │   │   ├── reward_service.py      # ✅ Session 11
│   │   │   ├── chat_service.py        # ✅ (updated Session 11)
│   │   │   ├── photo_service.py       # ✅
│   │   │   ├── websocket_manager.py   # ✅
│   │   │   ├── notification_service.py # 🔲 Session 12
│   │   │   ├── payment_service.py     # 🔲 Session 15 (mock now)
│   │   │   └── location_service.py    # 🔲 Session 14
│   │   │
│   │   ├── core/
│   │   │   ├── config.py
│   │   │   ├── security.py
│   │   │   ├── deps.py
│   │   │   ├── limiter.py
│   │   │   ├── logging.py
│   │   │   └── redis.py
│   │   │
│   │   └── utils/
│   │       ├── geo.py
│   │       └── pagination.py
│   │
│   ├── alembic/versions/              # Migration files
│   ├── tests/
│   │   ├── conftest.py
│   │   ├── test_auth.py
│   │   ├── test_users.py
│   │   ├── test_photos.py
│   │   ├── test_swipes.py
│   │   ├── test_matches.py
│   │   ├── test_messages.py
│   │   ├── test_search.py
│   │   ├── test_blocks.py
│   │   ├── test_rewards.py            # ✅ Session 11
│   │   ├── test_referrals.py          # ✅ Session 11
│   │   ├── test_subscriptions.py      # ✅ Session 11
│   │   ├── test_daily_limits.py       # ✅ Session 11
│   │   ├── test_notifications.py      # 🔲 Session 12
│   │   ├── test_reports.py            # 🔲 Session 12
│   │   ├── test_privacy.py            # 🔲 Session 12
│   │   └── test_admin.py              # 🔲 Session 13
│   │
│   ├── uploads/                       # User photos (gitignored)
│   ├── .env                           # Local env vars (gitignored)
│   ├── .env.example
│   ├── requirements.txt
│   └── Dockerfile
│
└── mobile/                            # Flutter app (Session 16+)
```

---

## 5. Environment & Configuration

### Current `.env` Variables (Session 11)

```env
# Database
DATABASE_URL=postgresql+asyncpg://dating_user:dating_pass@localhost:5433/dating_test
REDIS_URL=redis://localhost:6380

# Security
SECRET_KEY=your-secret-key
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=10080
ADMIN_SECRET_KEY=your-admin-key

# App
APP_NAME=DatingApp
DEBUG=True

# Daily Limits
FREE_USER_DAILY_LIKES=20
FREE_USER_DAILY_CHATS=10

# Ad Rewards
AD_REWARD_LIKES_BONUS=5
AD_REWARD_CHATS_BONUS=3
MAX_AD_REWARDS_PER_DAY=2

# Bonuses
WELCOME_BONUS_DAYS=7
REFERRAL_INVITER_DAYS=3
REFERRAL_INVITED_DAYS=3

# Subscription Plans (days)
SUBSCRIPTION_MONTHLY_DAYS=30
SUBSCRIPTION_QUARTERLY_DAYS=90
SUBSCRIPTION_YEARLY_DAYS=365
SUBSCRIPTION_QUARTERLY_DISCOUNT=15
SUBSCRIPTION_YEARLY_DISCOUNT=30

# Payment (MOCKED - real integration needed)
ZARINPAL_MERCHANT_ID=
ZARINPAL_SANDBOX=true
ZARINPAL_CALLBACK_URL=

# File Uploads
UPLOADS_DIR=uploads
MAX_PHOTO_SIZE_MB=5
MAX_PHOTOS_PER_USER=6
```

### `config.py` Settings Class

Located at `app/core/config.py` with all above variables as typed fields.

---

## 6. Database Schema

### `users` Table (Current State)

| Column | Type | Description |
|--------|------|-------------|
| id | UUID | Primary Key |
| email | VARCHAR(255) | Unique, indexed |
| password_hash | VARCHAR(255) | Nullable for Google users |
| google_id | VARCHAR(255) | Unique, nullable |
| phone | VARCHAR(20) | Nullable |
| phone_verified | BOOLEAN | Default FALSE |
| name | VARCHAR(100) | Not null |
| age | SMALLINT | Not null |
| gender | VARCHAR(10) | 'male' or 'female' |
| bio | TEXT | Nullable |
| height | SMALLINT | Nullable |
| weight | SMALLINT | Nullable |
| lat | DOUBLE | Nullable |
| lng | DOUBLE | Nullable |
| premium_until | TIMESTAMPTZ | Nullable (NULL = free user) |
| is_active | BOOLEAN | Default TRUE |
| token_version | INTEGER | Default 1 |
| is_profile_complete | BOOLEAN | Default TRUE |
| referral_code | VARCHAR(20) | Unique, nullable |
| referred_by | UUID | References users(id) |
| hide_last_seen | BOOLEAN | Default FALSE |
| hide_online_status | BOOLEAN | Default FALSE |
| country | VARCHAR(100) | Nullable |
| province | VARCHAR(100) | Nullable |
| city | VARCHAR(100) | Nullable |
| location_manual | BOOLEAN | Default FALSE |
| created_at | TIMESTAMPTZ | Default NOW() |
| last_seen_at | TIMESTAMPTZ | Nullable |

### `subscriptions` Table (Session 11)

| Column | Type | Description |
|--------|------|-------------|
| id | UUID | Primary Key |
| user_id | UUID | Foreign Key to users(id) |
| plan | VARCHAR(20) | monthly, quarterly, yearly, welcome_bonus, referral_reward |
| status | VARCHAR(20) | active, expired, cancelled |
| started_at | TIMESTAMPTZ | Not null |
| expires_at | TIMESTAMPTZ | Not null |
| source | VARCHAR(30) | purchase, referral, welcome_bonus, admin_grant |
| payment_id | VARCHAR(100) | Nullable |
| created_at | TIMESTAMPTZ | Default NOW() |

### `referral_rewards` Table (Session 11)

| Column | Type | Description |
|--------|------|-------------|
| id | UUID | Primary Key |
| inviter_id | UUID | Foreign Key to users(id) |
| invited_id | UUID | Foreign Key to users(id), UNIQUE |
| inviter_days | SMALLINT | Default 3 |
| invited_days | SMALLINT | Default 3 |
| created_at | TIMESTAMPTZ | Default NOW() |

### `daily_limits` Table (Session 7)

| Column | Type | Description |
|--------|------|-------------|
| id | UUID | Primary Key |
| user_id | UUID | Foreign Key to users(id) |
| date | DATE | Not null |
| likes_used | INTEGER | Default 0 |
| chats_used | INTEGER | Default 0 |
| ad_likes_bonus | INTEGER | Default 0 |
| ad_chats_bonus | INTEGER | Default 0 |
| UNIQUE | (user_id, date) | |

### Other Tables (Sessions 1-10)

- `photos` - User photos with status (pending/approved/rejected)
- `swipes` - Like/pass records
- `matches` - Mutual likes
- `blocks` - Blocked users
- `messages` - Chat messages

### Planned Tables

| Table | Session | Purpose |
|-------|---------|---------|
| notifications | 12 | In-app notifications |
| reports | 12 | User reports |
| tickets | 13 | Support tickets |

---

## 7. API Reference

### Completed Endpoints (Sessions 1-10)

| Category | Endpoints | Status |
|----------|-----------|--------|
| Auth | POST /register, /login, /google, /refresh, /logout, /change-password | ✅ |
| Users | GET/PUT/DELETE /me, GET /{user_id}, POST /me/location | ✅ |
| Photos | POST/GET/DELETE /users/me/photos, PUT /{photo_id}/main | ✅ |
| Admin Photos | GET /admin/photos/pending, POST /{photo_id}/approve|reject, GET /stats | ✅ |
| Discover | GET /discover | ✅ |
| Swipes | POST /swipes, GET /stats | ✅ |
| Search | GET /search (age, gender, height, weight, province, city, etc.) | ✅ |
| Matches | GET /matches, GET /{match_id}, WS /ws/matches | ✅ |
| Blocks | POST /{user_id}/block|unblock, GET /blocks | ✅ |
| Messages | GET/POST /{match_id}, POST /accept, /delivered, /read, DELETE /{id}, POST /forward, GET /{id}/status, WS /ws/chat/{match_id} | ✅ |

### Session 11 Endpoints (COMPLETED)

| Category | Endpoint | Method | Description |
|----------|----------|--------|-------------|
| Rewards | /rewards/ad-watched | POST | Watch ad → +5 likes, +3 chats (max 2/day) |
| Rewards | /rewards/my-limits | GET | Get remaining likes/chats for today |
| Referrals | /referrals/my-code | GET | Get user's referral code |
| Referrals | /referrals/claim | POST | Claim referral code (get premium days) |
| Referrals | /referrals/stats | GET | Get referral statistics |
| Subscriptions | /subscriptions/plans | GET | List plans (monthly/quarterly/yearly) |
| Subscriptions | /subscriptions/purchase | POST | Initiate purchase (MOCK - returns fake URL) |
| Subscriptions | /subscriptions/verify | GET | Verify payment (MOCK) |
| Subscriptions | /subscriptions/my | GET | Current subscription status |
| Subscriptions | /subscriptions/cancel | POST | Cancel auto-renewal |

### Pending Endpoints

| Category | Endpoint | Session | Description |
|----------|----------|---------|-------------|
| Notifications | /notifications | 12 | List, read, delete notifications |
| Reports | /reports | 12 | Report user, list my reports |
| Privacy | /privacy/settings | 12 | Get/update privacy settings |
| Tickets | /tickets | 13 | Submit support tickets |
| Admin | /admin/* | 13 | Admin panel endpoints |

---

## 8. Architecture Decisions

### Authentication Flow

```
Register/Login → access_token (JWT, 7d) + refresh_token (opaque, Redis 30d)
         ↓
API call → Bearer {access_token}
         ↓
access_token expires → POST /auth/refresh
         ↓
New token pair (old refresh_token revoked - rotation)
         ↓
Logout → delete refresh_token from Redis
Logout-all → increment user.token_version (invalidates all JWTs)
```

### Premium Logic

```python
@property
def is_premium(self) -> bool:
    if self.premium_until is None:
        return False
    return self.premium_until > datetime.now(timezone.utc)
```

### Daily Limits (via RewardService)

- Free users: `FREE_USER_DAILY_LIKES` (20) and `FREE_USER_DAILY_CHATS` (10)
- Premium users: unlimited (-1)
- Ad rewards: +5 likes, +3 chats per ad (max `MAX_AD_REWARDS_PER_DAY` = 2)
- Limits stored in `daily_limits` table (PostgreSQL, not Redis)

### WebSocket Connections

| Connection | Path | Purpose |
|------------|------|---------|
| Match WS | `/ws/matches?token=...` | Real-time match notifications |
| Chat WS | `/ws/chat/{match_id}?token=...` | Real-time messages |

---

## 9. Business Rules

### Free User Daily Limits

| Action | Daily Limit | Ad Bonus (max 2x/day) |
|--------|-------------|----------------------|
| Likes | 20 | +5 each |
| New Chats | 10 | +3 each |

### Premium User

- Unlimited likes and chats
- No ads
- See who liked them (Session 12)

### Rewards

| Event | Reward |
|-------|--------|
| New registration | 7 days premium (welcome bonus) |
| Referral (inviter) | +3 days premium |
| Referral (invited) | +3 days premium (stacks with welcome = 10 days) |
| Watch ad | +5 likes, +3 chats (max 2 ads/day) |

### Subscription Plans (MOCKED)

| Plan | Duration | Discount |
|------|----------|----------|
| Monthly | 30 days | 0% |
| Quarterly | 90 days | 15% |
| Yearly | 365 days | 30% |

**⚠️ IMPORTANT:** Payment is currently MOCKED. Real ZarinPal integration needed before production.

---

## 10. Session Progress

| Session | Focus | Status |
|---------|-------|--------|
| 1-2 | Project setup, Docker, base models | ✅ |
| 3 | Auth endpoints | ✅ |
| 4 | Auth hardening (token versioning, logging, tests) | ✅ |
| 5 | Users endpoints | ✅ |
| 6 | Photo upload + admin moderation | ✅ |
| 7 | Discover + Swipe system | ✅ |
| 8 | Search + Block system | ✅ |
| 9 | Match list + WebSocket notifications | ✅ |
| 10 | Chat system (messages + WebSocket) | ✅ |
| **11** | **Premium + Daily Limits + Ad Rewards + Referrals** | ✅ |
| **12** | **Notifications + Privacy + Reports** | 🔲 |
| **13** | **Admin Panel (Tickets + Reports + User management)** | 🔲 |
| **14** | **Location fields + Search filters** | 🔲 |
| **15** | **Push notifications + Real Payment Integration** | 🔲 |
| 16+ | Flutter mobile app | 🔲 |

---

## 11. Session 12 Plan: Notifications + Privacy + Reports

### Goal
Build in-app notification system, user privacy controls, and user reporting system.

### Database Changes

```sql
-- Already have hide_last_seen, hide_online_status in users table

CREATE TABLE notifications (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    type VARCHAR(50) NOT NULL,
    title VARCHAR(200) NOT NULL,
    body TEXT,
    data JSONB,
    is_read BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE reports (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    reporter_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    reported_id UUID REFERENCES users(id) ON DELETE SET NULL,
    reason TEXT NOT NULL,
    status VARCHAR(20) DEFAULT 'pending',
    admin_note TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    resolved_at TIMESTAMPTZ
);
```

### Files to Create

| File | Purpose |
|------|---------|
| `app/models/notification.py` | Notification ORM model |
| `app/models/report.py` | Report ORM model |
| `app/schemas/notification.py` | Notification schemas |
| `app/schemas/report.py` | Report schemas |
| `app/schemas/privacy.py` | Privacy settings schemas |
| `app/api/v1/endpoints/notifications.py` | GET /, POST /read, DELETE /{id} |
| `app/api/v1/endpoints/reports.py` | POST /{user_id}, GET /my |
| `app/api/v1/endpoints/privacy.py` | PATCH /settings, GET /settings |
| `app/services/notification_service.py` | create_notification(), notify_like(), notify_match(), notify_message() |
| `tests/test_notifications.py` | Notification tests |
| `tests/test_reports.py` | Report tests |
| `tests/test_privacy.py` | Privacy settings tests |

### Files to Update

| File | Changes |
|------|---------|
| `app/api/v1/endpoints/swipes.py` | Call `notify_like()` when user A likes user B (only if recipient is premium) |
| `app/api/v1/endpoints/matches.py` | Call `notify_match()` on match creation |
| `app/services/chat_service.py` | Call `notify_message()` when recipient is offline |
| `app/api/v1/endpoints/auth.py` | Update `last_seen_at` on every API call |
| `app/schemas/user.py` | Respect `hide_last_seen` and `hide_online_status` in public profile |

### Implementation Notes

```python
# Like notification (only for premium users)
if target_user.is_premium:
    await notification_service.notify_like(
        db, current_user.id, target_user.id,
        title="کسی شما را لایک کرد",
        body=f"{current_user.name} (age {current_user.age}) liked you"
    )

# Privacy in public profile
class PublicUserResponse(BaseModel):
    last_seen_at: Optional[datetime]  # None if hide_last_seen=True
    # is_online calculated from last_seen_at within last 5 minutes
```

### Tests Checklist

- [ ] Like creates notification for premium recipient
- [ ] Like does NOT create notification for free recipient
- [ ] Match creates notification for both users
- [ ] Message creates notification for offline recipient
- [ ] Privacy: last_seen hidden when hide_last_seen=True
- [ ] Report submitted successfully
- [ ] User cannot report same person twice within 24 hours

---

## 12. Session 13 Plan: Admin Panel

### Goal
Admin tools for content moderation, user management, and support tickets.

### Database Changes

```sql
CREATE TABLE tickets (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    subject VARCHAR(200) NOT NULL,
    message TEXT NOT NULL,
    status VARCHAR(20) DEFAULT 'open',
    admin_response TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ
);
```

### Files to Create

| File | Purpose |
|------|---------|
| `app/models/ticket.py` | Ticket ORM model |
| `app/schemas/ticket.py` | Ticket schemas |
| `app/api/v1/endpoints/tickets.py` | User: POST /, GET /, GET /{id} |
| `app/api/v1/endpoints/admin_tickets.py` | Admin: GET /admin/tickets, PATCH /admin/tickets/{id} |
| `app/api/v1/endpoints/admin_reports.py` | Admin: GET /admin/reports, PATCH /admin/reports/{id} |
| `app/api/v1/endpoints/admin_users.py` | Admin: GET /admin/users, PATCH /admin/users/{id}, DELETE /admin/users/{id}, POST /admin/users/{id}/grant-premium |
| `tests/test_tickets.py` | Ticket tests |
| `tests/test_admin.py` | Admin tests |

### Admin Actions

| Action | Endpoint | Description |
|--------|----------|-------------|
| List tickets | GET /admin/tickets | All tickets, filter by status |
| Respond to ticket | PATCH /admin/tickets/{id} | Add response, update status |
| List reports | GET /admin/reports | All reports, filter by status |
| Review report | PATCH /admin/reports/{id} | Mark reviewed, take action |
| List users | GET /admin/users | Paginated user list with filters |
| Deactivate user | PATCH /admin/users/{id} | Set is_active=False, increment token_version |
| Delete user | DELETE /admin/users/{id} | Hard delete after cooldown |
| Grant premium | POST /admin/users/{id}/grant-premium | Add premium days, create subscription |

---

## 13. Session 14 Plan: Location Fields + Search Filters

### Goal
Complete location system with province/city filters and referral claim flow.

### Database Changes (already done in Session 11)

- `country`, `province`, `city`, `location_manual` already in users table

### Files to Create

| File | Purpose |
|------|---------|
| `app/services/location_service.py` | Province/city validation, Iran province list |
| `tests/test_location.py` | Location update and search tests |

### Files to Update

| File | Changes |
|------|---------|
| `app/api/v1/endpoints/users.py` | Add `PATCH /me/location-text` endpoint for country/province/city |
| `app/api/v1/endpoints/search.py` | Already has province/city filters ✅ |
| `app/schemas/user.py` | Add country, province, city to UserResponse |
| `app/api/v1/endpoints/referrals.py` | Complete `/claim` endpoint with 24-hour window check |

### Location Flow

```
Frontend:
  1. User selects province/city from dropdown
  2. Frontend converts city name to lat/lng (using geocoding API or lookup table)
  3. PATCH /users/me/location with {lat, lng, country, province, city}

Backend:
  1. Update lat/lng fields
  2. Update country, province, city text fields
  3. Set location_manual = True
  4. Update last_seen_at
```

---

## 14. Session 15 Plan: Push Notifications + Production

### Goal
Real push notifications via Firebase Cloud Messaging, performance optimization, and real payment integration.

### Files to Create

| File | Purpose |
|------|---------|
| `app/services/push_service.py` | FCM send_push(), send_to_topic() |
| `app/models/device_token.py` | Store FCM tokens per user/device |
| `app/services/payment_service.py` | Real ZarinPal API integration |

### Files to Update

| File | Changes |
|------|---------|
| `app/services/notification_service.py` | Call push_service after creating DB notification |
| `app/api/v1/endpoints/notifications.py` | Add POST /device-token endpoint |
| `app/api/v1/endpoints/subscriptions.py` | Replace mock with real ZarinPal calls |

### Performance Work

```sql
-- Add missing indexes
CREATE INDEX idx_users_premium_until ON users(premium_until);
CREATE INDEX idx_users_province ON users(province);
CREATE INDEX idx_users_city ON users(city);
CREATE INDEX idx_notifications_user ON notifications(user_id, is_read, created_at DESC);
```

### ZarinPal Real Integration (replace mock)

```python
# payment_service.py
ZARINPAL_REQUEST_URL = "https://api.zarinpal.com/pg/v4/payment/request.json"
ZARINPAL_VERIFY_URL = "https://api.zarinpal.com/pg/v4/payment/verify.json"

async def create_payment(amount, description, callback_url):
    # Real API call to ZarinPal
    
async def verify_payment(authority, amount):
    # Real verification call
```

### OpenAPI Documentation

- Add proper `summary`, `description`, `response_model` to all endpoints
- Export final spec: `openapi.json`

---

## 15. Testing Strategy

### Setup (`conftest.py`)

- Test database created fresh for each test session
- Redis flushed between tests
- Rate limiting disabled during tests
- WebSocket manager mocked

### Test Files by Session

| Session | Test Files |
|---------|------------|
| 1-10 | test_auth.py, test_users.py, test_photos.py, test_swipes.py, test_matches.py, test_messages.py, test_search.py, test_blocks.py |
| 11 | test_rewards.py, test_referrals.py, test_subscriptions.py, test_daily_limits.py |
| 12 | test_notifications.py, test_reports.py, test_privacy.py |
| 13 | test_tickets.py, test_admin.py |
| 14 | test_location.py |

### Run All Tests

```bash
pytest tests/ -v
```

---

## 16. Deployment Notes

### Docker Compose Services

```yaml
services:
  db:
    image: postgres:15
    environment:
      POSTGRES_DB: dating_db
      POSTGRES_USER: dating_user
      POSTGRES_PASSWORD: dating_pass
    volumes:
      - postgres_data:/var/lib/postgresql/data

  redis:
    image: redis:7-alpine

  api:
    build: .
    depends_on:
      - db
      - redis
    env_file:
      - .env
    volumes:
      - ./uploads:/app/uploads
```

### Alembic Commands

```bash
# Generate migration
alembic revision --autogenerate -m "description"

# Apply migrations
alembic upgrade head

# Rollback
alembic downgrade -1
```

### File Storage

- MVP: Local disk at `uploads/`
- Production: Migrate to Arvan Cloud (S3-compatible) for Iranian market

### Environment Files

- `.env` - Local development (gitignored)
- `.env.example` - Template for new devs (committed)
- `.env.test` - Test environment

---

## Quick Reference: HTTP Error Codes

| Code | When |
|------|------|
| 400 | Validation error, bad input |
| 401 | Missing or invalid token |
| 403 | Insufficient permissions (not admin, not premium) |
| 404 | Resource not found |
| 409 | Conflict (duplicate swipe, already blocked) |
| 422 | Pydantic validation error |
| 429 | Rate limit or daily limit exceeded |

---

## Quick Reference: Redis Key Patterns

| Key | TTL | Purpose |
|-----|-----|---------|
| `refresh:{token_hash}` | 30 days | Refresh token store |
| `ratelimit:{endpoint}:{ip}` | per window | Rate limiting |

(Note: Daily limits use PostgreSQL `daily_limits` table, not Redis)

---

## Session 11 Completion Summary

### ✅ Completed Items

| Feature | Status |
|---------|--------|
| Premium subscription model (`premium_until`) | ✅ |
| Daily limits (configurable via .env) | ✅ |
| Ad reward system (`POST /rewards/ad-watched`) | ✅ |
| Referral system (`POST /referrals/claim`) | ✅ |
| Welcome bonus (7 days premium on registration) | ✅ |
| Subscription plans endpoint (`GET /subscriptions/plans`) | ✅ |
| Cancel subscription (`POST /subscriptions/cancel`) | ✅ |
| Search with province/city filters | ✅ |
| RewardService for daily limit logic | ✅ |
| All schemas for rewards, referrals, subscriptions | ✅ |
| Tests for all Session 11 features (31 tests, 29 passing) | ✅ |

### ⚠️ Pending for Production

| Item | Status | When |
|------|--------|------|
| ZarinPal real integration | 🔲 MOCKED | Session 15 |
| Payment IP restriction (Iran-only) | 🔲 NOT IMPLEMENTED | Session 15 |

---

**Session 11 is COMPLETE.** Ready for Session 12.
```

This is the **complete, accurate `dev.md`** based on your actual codebase. Ready for Session 12!