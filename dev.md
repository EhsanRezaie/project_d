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
11. [Session 13 Plan: Admin Panel](#11-session-13-plan-admin-panel)
12. [Session 14 Plan: Location Fields + Referral Complete](#12-session-14-plan-location-fields--referral-complete)
13. [Session 15 Plan: Push Notifications + Production Ready](#13-session-15-plan-push-notifications--production-ready)
14. [Testing Strategy](#14-testing-strategy)
15. [Deployment Notes](#15-deployment-notes)

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
│   │   │   ├── user.py                    # ✅
│   │   │   ├── photo.py                   # ✅
│   │   │   ├── swipe.py                   # ✅
│   │   │   ├── match.py                   # ✅
│   │   │   ├── block.py                   # ✅
│   │   │   ├── message.py                 # ✅
│   │   │   ├── daily_limit.py             # ✅
│   │   │   ├── review_reward.py           # ✅
│   │   │   ├── subscription.py            # ✅ Session 11
│   │   │   ├── referral_reward.py         # ✅ Session 11
│   │   │   ├── notification.py            # ✅ Session 12
│   │   │   ├── report.py                  # ✅ Session 12
│   │   │   └── ticket.py                  # 🔲 Session 13
│   │   │
│   │   ├── schemas/
│   │   │   ├── auth.py                    # ✅
│   │   │   ├── user.py                    # ✅
│   │   │   ├── photo.py                   # ✅
│   │   │   ├── discover.py                # ✅
│   │   │   ├── search.py                  # ✅
│   │   │   ├── match.py                   # ✅
│   │   │   ├── message.py                 # ✅
│   │   │   ├── subscription.py            # ✅ Session 11
│   │   │   ├── rewards.py                 # ✅ Session 11
│   │   │   ├── referral.py                # ✅ Session 11
│   │   │   ├── notification.py            # ✅ Session 12
│   │   │   ├── report.py                  # ✅ Session 12
│   │   │   ├── privacy.py                 # ✅ Session 12
│   │   │   └── ticket.py                  # 🔲 Session 13
│   │   │
│   │   ├── api/v1/endpoints/
│   │   │   ├── auth.py                    # ✅
│   │   │   ├── users.py                   # ✅
│   │   │   ├── photos.py                  # ✅
│   │   │   ├── admin_photos.py            # ✅
│   │   │   ├── discover.py                # ✅
│   │   │   ├── swipes.py                  # ✅
│   │   │   ├── search.py                  # ✅
│   │   │   ├── matches.py                 # ✅
│   │   │   ├── blocks.py                  # ✅
│   │   │   ├── messages.py                # ✅
│   │   │   ├── subscriptions.py           # ✅ Session 11
│   │   │   ├── rewards.py                 # ✅ Session 11
│   │   │   ├── referrals.py               # ✅ Session 11
│   │   │   ├── notifications.py           # ✅ Session 12
│   │   │   ├── reports.py                 # ✅ Session 12
│   │   │   ├── privacy.py                 # ✅ Session 12
│   │   │   ├── tickets.py                 # 🔲 Session 13
│   │   │   └── admin_*.py                 # 🔲 Session 13
│   │   │
│   │   ├── api/v1/websocket/
│   │   │   ├── matches.py                 # ✅
│   │   │   └── chat.py                    # ✅
│   │   │
│   │   ├── services/
│   │   │   ├── reward_service.py          # ✅ Session 11
│   │   │   ├── notification_service.py    # ✅ Session 12
│   │   │   ├── chat_service.py            # ✅
│   │   │   ├── photo_service.py           # ✅
│   │   │   ├── websocket_manager.py       # ✅
│   │   │   ├── payment_service.py         # 🔲 Session 15
│   │   │   └── location_service.py        # 🔲 Session 14
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
│   ├── alembic/versions/                  # Migration files
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
│   │   ├── test_rewards.py                # ✅ Session 11
│   │   ├── test_referrals.py              # ✅ Session 11
│   │   ├── test_subscriptions.py          # ✅ Session 11
│   │   ├── test_daily_limits.py           # ✅ Session 11
│   │   ├── test_notifications.py          # ✅ Session 12
│   │   ├── test_reports.py                # ✅ Session 12
│   │   ├── test_privacy.py                # ✅ Session 12
│   │   ├── test_tickets.py                # 🔲 Session 13
│   │   └── test_admin.py                  # 🔲 Session 13
│   │
│   ├── uploads/                           # User photos (gitignored)
│   ├── .env                               # Local env vars (gitignored)
│   ├── .env.example
│   ├── requirements.txt
│   └── Dockerfile
│
└── mobile/                                # Flutter app (Session 16+)
```

---

## 5. Environment & Configuration

### Current `.env` Variables

```env
# Database
DATABASE_URL=postgresql+asyncpg://user:pass@localhost:5432/dating_db
REDIS_URL=redis://localhost:6379

# Security
SECRET_KEY=your-secret-key
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=10080
ADMIN_SECRET_KEY=your-admin-key

# App
APP_NAME=DatingApp
DEBUG=True

# Daily Limits (ONLY restrictions in the app)
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

# Subscription Plans
SUBSCRIPTION_MONTHLY_DAYS=30
SUBSCRIPTION_QUARTERLY_DAYS=90
SUBSCRIPTION_YEARLY_DAYS=365
SUBSCRIPTION_QUARTERLY_DISCOUNT=15
SUBSCRIPTION_YEARLY_DISCOUNT=30

# Payment (MOCKED)
ZARINPAL_MERCHANT_ID=
ZARINPAL_SANDBOX=true
ZARINPAL_CALLBACK_URL=

# File Uploads
UPLOADS_DIR=uploads
MAX_PHOTO_SIZE_MB=5
MAX_PHOTOS_PER_USER=6
```

---

## 6. Database Schema

### `users` Table (Current State)

| Column | Type | Description |
|--------|------|-------------|
| id | UUID | Primary Key |
| email | VARCHAR(255) | Unique |
| password_hash | VARCHAR(255) | Nullable for Google users |
| google_id | VARCHAR(255) | Unique |
| phone | VARCHAR(20) | |
| phone_verified | BOOLEAN | |
| name | VARCHAR(100) | |
| age | SMALLINT | |
| gender | VARCHAR(10) | male/female |
| bio | TEXT | |
| height | SMALLINT | |
| weight | SMALLINT | |
| lat/lng | DOUBLE | Location coordinates |
| premium_until | TIMESTAMPTZ | NULL = free user |
| is_active | BOOLEAN | |
| token_version | INTEGER | |
| is_profile_complete | BOOLEAN | |
| referral_code | VARCHAR(20) | Unique |
| referred_by | UUID | |
| hide_last_seen | BOOLEAN | Privacy setting |
| country/province/city | VARCHAR(100) | Location text |
| location_manual | BOOLEAN | |
| created_at | TIMESTAMPTZ | |
| last_seen_at | TIMESTAMPTZ | |

### `subscriptions` Table (Session 11)

Tracks premium subscriptions and rewards.

### `referral_rewards` Table (Session 11)

Tracks referral rewards given.

### `daily_limits` Table (Session 7)

Tracks daily likes and chats usage.

### `notifications` Table (Session 12)

| Column | Type |
|--------|------|
| id | UUID |
| user_id | UUID FK |
| type | VARCHAR(50) |
| title | VARCHAR(200) |
| body | TEXT |
| data | JSONB |
| is_read | BOOLEAN |
| created_at | TIMESTAMPTZ |

### `reports` Table (Session 12)

| Column | Type |
|--------|------|
| id | UUID |
| reporter_id | UUID FK |
| reported_id | UUID FK |
| reason | TEXT |
| status | VARCHAR(20) |
| admin_note | TEXT |
| created_at | TIMESTAMPTZ |
| resolved_at | TIMESTAMPTZ |

### `tickets` Table (Session 13)

| Column | Type |
|--------|------|
| id | UUID |
| user_id | UUID FK |
| subject | VARCHAR(200) |
| message | TEXT |
| status | VARCHAR(20) |
| admin_response | TEXT |
| created_at | TIMESTAMPTZ |
| updated_at | TIMESTAMPTZ |

---

## 7. API Reference

### Completed Endpoints

| Category | Endpoints | Session |
|----------|-----------|---------|
| Auth | POST /register, /login, /google, /refresh, /logout, /change-password | 3-4 |
| Users | GET/PUT/DELETE /me, GET /{user_id}, POST /me/location | 5 |
| Photos | POST/GET/DELETE /users/me/photos, PUT /{photo_id}/main | 6 |
| Admin Photos | GET /admin/photos/pending, POST /approve|reject, GET /stats | 6 |
| Discover | GET /discover | 7 |
| Swipes | POST /swipes, GET /stats | 7 |
| Search | GET /search (age, gender, height, weight, province, city) | 8 |
| Matches | GET /matches, GET /{match_id}, WS /ws/matches | 9 |
| Blocks | POST /{user_id}/block|unblock, GET /blocks | 8 |
| Messages | GET/POST /{match_id}, POST /accept, /delivered, /read, DELETE /{id}, POST /forward, GET /{id}/status, WS /ws/chat | 10 |
| Rewards | POST /rewards/ad-watched, GET /rewards/my-limits | 11 |
| Referrals | GET /referrals/my-code, POST /referrals/claim, GET /referrals/stats | 11 |
| Subscriptions | GET /subscriptions/plans, POST /purchase, GET /verify, GET /my, POST /cancel | 11 |
| Notifications | GET /notifications, POST /notifications/read, DELETE /notifications/{id} | 12 |
| Reports | POST /reports/{user_id}, GET /reports/my | 12 |
| Privacy | GET /privacy/settings, PATCH /privacy/settings | 12 |

### Pending Endpoints (Session 13)

| Category | Endpoint | Description |
|----------|----------|-------------|
| Tickets | POST /tickets | Submit support ticket |
| Tickets | GET /tickets | List user tickets |
| Tickets | GET /tickets/{id} | Get ticket detail |
| Admin | GET /admin/tickets | List all tickets |
| Admin | PATCH /admin/tickets/{id} | Respond to ticket |
| Admin | GET /admin/reports | List all reports |
| Admin | PATCH /admin/reports/{id} | Review report |
| Admin | GET /admin/users | List users |
| Admin | PATCH /admin/users/{id} | Activate/deactivate user |
| Admin | DELETE /admin/users/{id} | Delete user |
| Admin | POST /admin/users/{id}/grant-premium | Grant premium days |

---

## 8. Architecture Decisions

### Authentication Flow

```
Register/Login → access_token (JWT, 7d) + refresh_token (opaque, Redis 30d)
         ↓
API call → Bearer {access_token}
         ↓
access_token expires → POST /auth/refresh (token rotation)
         ↓
Logout → delete refresh_token from Redis
Logout-all → increment user.token_version
```

### Premium Logic

```python
@property
def is_premium(self) -> bool:
    if self.premium_until is None:
        return False
    return self.premium_until > datetime.now(timezone.utc)
```

### Daily Limits (ONLY restrictions in the app)

- **Free users:** `FREE_USER_DAILY_LIKES` (20) and `FREE_USER_DAILY_CHATS` (10)
- **Premium users:** unlimited (-1)
- **Ad rewards:** +5 likes, +3 chats per ad (max 2 ads/day)
- Limits stored in `daily_limits` table

### All Other Features Are FREE

- ✅ Searching users
- ✅ Viewing profiles
- ✅ Receiving likes (notifications)
- ✅ Matching
- ✅ Chatting (after match or within limits)
- ✅ Sending photos/voice in chats
- ✅ Report users
- ✅ Privacy settings

### ⚠️ Important Notes

- **Like notifications are sent to ALL users** (not just premium)
- **Premium ONLY removes daily limits** (unlimited likes and new chats)
- **No other paywalls** - everything else is completely free

### Payment Status

- ⚠️ **ZarinPal is MOCKED** - Real integration needed before production (Session 15)
- ⚠️ **No IP restriction for Iran** - Not implemented (Session 15)

---

## 9. Business Rules

### Free User Daily Limits (ONLY RESTRICTIONS)

| Action | Daily Limit | Ad Bonus (max 2x/day) |
|--------|-------------|----------------------|
| Likes | 20 | +5 each |
| New Chats (first message to someone new) | 10 | +3 each |

### Premium User

- Unlimited likes
- Unlimited new chats
- Same everything else as free users

### Rewards (All Users)

| Event | Reward |
|-------|--------|
| New registration | 7 days premium (welcome bonus) |
| Referral (inviter) | +3 days premium |
| Referral (invited) | +3 days premium |
| Watch ad | +5 likes, +3 chats (max 2 ads/day) |

### Subscription Plans (MOCKED)

| Plan | Duration | Discount |
|------|----------|----------|
| Monthly | 30 days | 0% |
| Quarterly | 90 days | 15% |
| Yearly | 365 days | 30% |

### Notifications

| Type | Trigger | Recipient |
|------|---------|-----------|
| Like | User likes another user | The user who was liked |
| Match | Two users like each other | Both users |
| Message | User sends message | Recipient (if offline) |

### Reports

- User can report another user with reason (min 5 chars, max 500)
- Cannot report same user twice within 24 hours
- Cannot report yourself
- Reports go to admin for review

### Privacy

- `hide_last_seen = True` → last_seen_at hidden, online status hidden
- `hide_last_seen = False` → last_seen_at visible, online status visible

---

## 10. Session Progress

| Session | Focus | Status |
|---------|-------|--------|
| 1-2 | Project setup, Docker, base models | ✅ |
| 3 | Auth endpoints | ✅ |
| 4 | Auth hardening | ✅ |
| 5 | Users endpoints | ✅ |
| 6 | Photo upload + admin moderation | ✅ |
| 7 | Discover + Swipe system | ✅ |
| 8 | Search + Block system | ✅ |
| 9 | Match list + WebSocket | ✅ |
| 10 | Chat system | ✅ |
| **11** | **Premium + Daily Limits + Ad Rewards + Referrals** | ✅ |
| **12** | **Notifications + Privacy + Reports** | ✅ |
| **13** | **Admin Panel (Tickets + Reports + User management)** | 🔲 |
| **14** | **Location fields + Referral complete** | 🔲 |
| **15** | **Push notifications + Real Payment + Production** | 🔲 |
| 16+ | Flutter mobile app | 🔲 |

---

## 11. Session 13 Plan: Admin Panel

### Goal
Build admin tools for content moderation, user management, and support tickets.

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

| Action | Endpoint | Method |
|--------|----------|--------|
| List tickets | /admin/tickets | GET |
| Respond to ticket | /admin/tickets/{id} | PATCH |
| List reports | /admin/reports | GET |
| Review report | /admin/reports/{id} | PATCH |
| List users | /admin/users | GET |
| Deactivate user | /admin/users/{id} | PATCH |
| Delete user | /admin/users/{id} | DELETE |
| Grant premium | /admin/users/{id}/grant-premium | POST |

### Admin Authentication

- Use `ADMIN_SECRET_KEY` from `.env`
- Header: `X-Admin-Key: your-admin-secret-key`

### Tests Checklist

- [ ] Non-admin cannot access admin endpoints (403)
- [ ] Admin can list tickets
- [ ] Admin can respond to tickets
- [ ] Admin can list reports
- [ ] Admin can review reports
- [ ] Admin can deactivate user (sets is_active=False, increments token_version)
- [ ] Admin can delete user (hard delete after cooldown)
- [ ] Admin can grant premium days

---

## 12. Session 14 Plan: Location Fields + Referral Complete

### Goal
Complete location system with province/city and finalize referral claim flow.

### Database Changes

Already in `users` table from Session 11:
- `country`, `province`, `city`, `location_manual`

### Files to Update

| File | Changes |
|------|---------|
| `app/api/v1/endpoints/users.py` | Add `PATCH /me/location-text` for country/province/city |
| `app/api/v1/endpoints/search.py` | Already has province/city filters ✅ |
| `app/api/v1/endpoints/referrals.py` | Complete `/claim` with 24-hour window check |
| `app/services/location_service.py` | NEW - province/city validation |

### Location Flow

```
Frontend:
  1. User selects province/city from dropdown
  2. Frontend converts city name to lat/lng
  3. PATCH /users/me/location with {lat, lng, country, province, city}

Backend:
  1. Update lat/lng
  2. Update country, province, city
  3. Set location_manual = True
```

### Tests Checklist

- [ ] Referral claim within 24 hours works
- [ ] Referral claim after 24 hours fails
- [ ] Location text fields saved correctly
- [ ] Search by province returns correct users
- [ ] Search by city returns correct users

---

## 13. Session 15 Plan: Push Notifications + Production Ready

### Goal
Real push notifications via Firebase Cloud Messaging, real ZarinPal integration.

### Files to Create

| File | Purpose |
|------|---------|
| `app/services/push_service.py` | FCM send_push() |
| `app/models/device_token.py` | Store FCM tokens |
| `app/services/payment_service.py` | REAL ZarinPal integration |

### Files to Update

| File | Changes |
|------|---------|
| `app/services/notification_service.py` | Call push_service after DB notification |
| `app/api/v1/endpoints/notifications.py` | Add POST /device-token |
| `app/api/v1/endpoints/subscriptions.py` | Replace mock with real ZarinPal |

### Performance Work

```sql
-- Add missing indexes
CREATE INDEX idx_users_premium_until ON users(premium_until);
CREATE INDEX idx_users_province ON users(province);
CREATE INDEX idx_users_city ON users(city);
CREATE INDEX idx_notifications_user ON notifications(user_id, is_read, created_at DESC);
```

### Production Checklist

- [ ] Real ZarinPal integration (replace mock)
- [ ] FCM push notifications
- [ ] Iran-only IP check for payment (optional)
- [ ] All indexes added
- [ ] OpenAPI documentation complete
- [ ] Environment variables documented

---

## 14. Testing Strategy

### Test Files by Session

| Session | Test Files | Tests |
|---------|------------|-------|
| 1-10 | test_auth, test_users, test_photos, test_swipes, test_matches, test_messages, test_search, test_blocks | ~50 |
| 11 | test_rewards, test_referrals, test_subscriptions, test_daily_limits | 32 |
| 12 | test_notifications, test_reports, test_privacy | 31 |
| 13 | test_tickets, test_admin | TBD |

### Run All Tests

```bash
pytest tests/ -v
```

---

## 15. Deployment Notes

### Docker Compose

```yaml
services:
  db:
    image: postgres:15
  redis:
    image: redis:7-alpine
  api:
    build: .
    depends_on:
      - db
      - redis
    volumes:
      - ./uploads:/app/uploads
```

### Alembic Commands

```bash
alembic revision --autogenerate -m "description"
alembic upgrade head
alembic downgrade -1
```

### Environment Files

- `.env` - Local development (gitignored)
- `.env.example` - Template (committed)
- `.env.test` - Test environment

---

## Session 11 & 12 Completion Summary

### ✅ Session 11 Complete

| Feature | Status |
|---------|--------|
| Premium system (premium_until, is_premium) | ✅ |
| Daily limits (20 likes, 10 chats) | ✅ |
| Ad rewards (+5 likes, +3 chats, max 2/day) | ✅ |
| Referral system (codes + rewards) | ✅ |
| Welcome bonus (7 days premium) | ✅ |
| Subscription plans (mock payment) | ✅ |
| Search with province/city filters | ✅ |
| 32 tests passing | ✅ |

### ✅ Session 12 Complete

| Feature | Status |
|---------|--------|
| Notifications (like, match, message) | ✅ |
| Reports system (report users) | ✅ |
| Privacy settings (hide_last_seen) | ✅ |
| 31 tests passing | ✅ |

### ⚠️ Pending for Production

| Item | Session |
|------|---------|
| Real ZarinPal integration | 15 |
| FCM push notifications | 15 |
| Iran IP restriction (optional) | 15 |

---

**Next: Session 13 - Admin Panel (Tickets + Reports management + User management)**

Ready to start Session 13 when you are.
```