## `dev.md` - Iranian Dating App (Updated)

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
11. [Session 15 Plan: Push Notifications + Production Ready](#11-session-15-plan-push-notifications--production-ready)
12. [Testing Strategy](#12-testing-strategy)
13. [Deployment Notes](#13-deployment-notes)

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
| Cache | Redis 7 (tokens, rate limiting) + LRU cache (static location data) |
| Realtime | WebSocket |
| File storage | Local disk (`uploads/`) |
| Containerization | Docker + Docker Compose |
| Mobile | Flutter |
| Payment | ZarinPal (MOCKED - real integration needed) |
| Location | countrystatecity-countries package |
| Reverse Geocoding | Nominatim (OpenStreetMap) |

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
│   │   │   ├── subscription.py
│   │   │   ├── referral_reward.py
│   │   │   ├── notification.py
│   │   │   ├── report.py
│   │   │   └── ticket.py
│   │   │
│   │   ├── schemas/
│   │   │   ├── auth.py
│   │   │   ├── user.py
│   │   │   ├── photo.py
│   │   │   ├── discover.py
│   │   │   ├── search.py
│   │   │   ├── match.py
│   │   │   ├── message.py
│   │   │   ├── subscription.py
│   │   │   ├── rewards.py
│   │   │   ├── referral.py
│   │   │   ├── notification.py
│   │   │   ├── report.py
│   │   │   ├── privacy.py
│   │   │   ├── ticket.py
│   │   │   ├── admin.py
│   │   │   ├── dashboard.py
│   │   │   └── location.py
│   │   │
│   │   ├── api/v1/endpoints/
│   │   │   ├── auth.py
│   │   │   ├── users.py
│   │   │   ├── photos.py
│   │   │   ├── admin_photos.py
│   │   │   ├── discover.py
│   │   │   ├── swipes.py
│   │   │   ├── search.py
│   │   │   ├── matches.py
│   │   │   ├── blocks.py
│   │   │   ├── messages.py
│   │   │   ├── subscriptions.py
│   │   │   ├── rewards.py
│   │   │   ├── referrals.py
│   │   │   ├── notifications.py
│   │   │   ├── reports.py
│   │   │   ├── privacy.py
│   │   │   ├── tickets.py
│   │   │   ├── admin_tickets.py
│   │   │   ├── admin_reports.py
│   │   │   ├── admin_users.py
│   │   │   ├── admin_dashboard.py
│   │   │   ├── admin_announcements.py
│   │   │   ├── admin_photos.py
│   │   │   └── locations.py
│   │   │
│   │   ├── api/v1/websocket/
│   │   │   ├── matches.py
│   │   │   └── chat.py
│   │   │
│   │   ├── services/
│   │   │   ├── reward_service.py
│   │   │   ├── notification_service.py
│   │   │   ├── chat_service.py
│   │   │   ├── photo_service.py
│   │   │   ├── websocket_manager.py
│   │   │   └── location_service.py
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
│   ├── alembic/versions/
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
│   │   ├── test_rewards.py
│   │   ├── test_referrals.py
│   │   ├── test_subscriptions.py
│   │   ├── test_daily_limits.py
│   │   ├── test_notifications.py
│   │   ├── test_reports.py
│   │   ├── test_privacy.py
│   │   ├── test_tickets.py
│   │   ├── test_admin_tickets.py
│   │   ├── test_admin_reports.py
│   │   ├── test_admin_users.py
│   │   ├── test_admin_dashboard.py
│   │   ├── test_admin_photos.py
│   │   ├── test_admin_messages.py
│   │   └── test_location.py
│   │
│   ├── uploads/
│   ├── .env
│   ├── .env.example
│   ├── requirements.txt
│   └── Dockerfile
│
└── mobile/                                # Flutter app (Session 16+)
```

---

## 5. Environment & Configuration

### `.env` Variables

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

### `users` Table

| Column | Type |
|--------|------|
| id | UUID |
| email | VARCHAR(255) UNIQUE |
| password_hash | VARCHAR(255) |
| google_id | VARCHAR(255) UNIQUE |
| phone | VARCHAR(20) |
| phone_verified | BOOLEAN |
| name | VARCHAR(100) |
| age | SMALLINT |
| gender | VARCHAR(10) |
| bio | TEXT |
| height | SMALLINT |
| weight | SMALLINT |
| lat/lng | DOUBLE |
| premium_until | TIMESTAMPTZ |
| is_active | BOOLEAN |
| token_version | INTEGER |
| is_profile_complete | BOOLEAN |
| referral_code | VARCHAR(20) UNIQUE |
| referred_by | UUID |
| hide_last_seen | BOOLEAN |
| country/province/city | VARCHAR(100) |
| location_manual | BOOLEAN |
| created_at | TIMESTAMPTZ |
| last_seen_at | TIMESTAMPTZ |

### Other Tables

| Table | Purpose |
|-------|---------|
| photos | User photos with moderation |
| swipes | Like/pass records |
| matches | Mutual likes |
| blocks | Blocked users |
| messages | Chat messages |
| daily_limits | Daily likes/chats usage |
| subscriptions | Premium subscriptions |
| referral_rewards | Referral rewards |
| notifications | In-app notifications |
| reports | User reports |
| tickets | Support tickets |

---

## 7. API Reference

### Completed Endpoints (Sessions 1-14)

| Category | Endpoints |
|----------|-----------|
| Auth | POST /register, /login, /google, /refresh, /logout, /change-password |
| Users | GET/PUT/DELETE /me, GET /{user_id}, POST /me/location, PATCH /me/location-text |
| Photos | POST/GET/DELETE /users/me/photos, PUT /{photo_id}/main |
| Discover | GET /discover |
| Swipes | POST /swipes, GET /stats |
| Search | GET /search (country, province, city, distance, age, gender, height, weight) |
| Matches | GET /matches, GET /{match_id}, WS /ws/matches |
| Blocks | POST /{user_id}/block|unblock, GET /blocks |
| Messages | GET/POST /{match_id}, POST /accept, /delivered, /read, DELETE /{id}, POST /forward, GET /{id}/status, WS /ws/chat |
| Rewards | POST /rewards/ad-watched, GET /rewards/my-limits |
| Referrals | GET /referrals/my-code, POST /referrals/claim, GET /referrals/stats |
| Subscriptions | GET /subscriptions/plans, POST /purchase, GET /verify, GET /my, POST /cancel |
| Notifications | GET /notifications, POST /notifications/read, DELETE /notifications/{id} |
| Reports | POST /reports/{user_id}, GET /reports/my |
| Privacy | GET /privacy/settings, PATCH /privacy/settings |
| Tickets | POST /tickets, GET /tickets, GET /tickets/{id} |
| Locations | GET /locations/provinces, GET /locations/cities, GET /locations/validate |
| Admin | GET /admin/tickets, PATCH /admin/tickets/{id}, GET /admin/reports, PATCH /admin/reports/{id}, GET /admin/users, PATCH /admin/users/{id}, DELETE /admin/users/{id}, POST /admin/users/{id}/premium, POST /admin/users/{id}/message, GET /admin/users/{id}/activity, POST /admin/announcements, GET /admin/dashboard, GET /admin/dashboard/stats/*, GET /admin/photos/pending, POST /admin/photos/{id}/approve, POST /admin/photos/{id}/reject, GET /admin/photos/stats, GET /admin/photos/{id}, POST /admin/photos/{id}/verify-face, GET /admin/photos/users/{user_id}/photos |

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

| Action | Free User | Premium User |
|--------|-----------|--------------|
| Likes | 20/day | Unlimited |
| New Chats | 10/day | Unlimited |

**All other features are FREE:**
- Searching users
- Viewing profiles
- Matching
- Chatting (after match)
- Sending photos/voice
- Notifications
- Reports

### Location System

| Method | Description |
|--------|-------------|
| `POST /users/me/location` | Update lat/lng from GPS, auto-fills country/province/city via reverse geocoding |
| `PATCH /users/me/location-text` | Manually set country/province/city (sets location_manual=True) |
| `GET /locations/provinces` | Get all Iranian provinces (cached with LRU) |
| `GET /locations/cities` | Get cities by province code (cached with LRU) |
| `GET /search?country=&province=&city=&distance_km=` | Search users by location |

**Reverse Geocoding:** Uses Nominatim (OpenStreetMap) to convert lat/lng to country/province/city.

**Caching:** 
- Provinces list: `@lru_cache(maxsize=1)` - forever
- Cities list per province: `@lru_cache(maxsize=32)` - forever

### Admin Authentication

- Header: `X-Admin-Key: {ADMIN_SECRET_KEY}`
- Returns 403 if missing or invalid
- No JWT required for admin endpoints

### Notifications

| Type | Trigger | Recipient |
|------|---------|-----------|
| Like | User likes another user | The user who was liked |
| Match | Two users like each other | Both users |
| Message | User sends message | Recipient (if offline) |
| System | Admin message or announcement | Target user(s) |

### Privacy

- `hide_last_seen = True` → last_seen_at hidden, online status hidden
- `hide_last_seen = False` → last_seen_at visible, online status visible

---

## 9. Business Rules

### Free User Daily Limits (ONLY RESTRICTIONS)

| Action | Daily Limit | Ad Bonus (max 2x/day) |
|--------|-------------|----------------------|
| Likes | 20 | +5 each |
| New Chats | 10 | +3 each |

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

### Admin Capabilities

- View all users with filters
- Activate/deactivate users
- Delete users (hard delete)
- Grant premium days
- View user activity (swipes, matches, messages)
- Send direct messages to users
- Send announcements to all or premium-only users
- View dashboard analytics
- Moderate photos (approve/reject/verify face)
- Manage support tickets
- Review user reports

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
| 11 | Premium + Daily Limits + Ad Rewards + Referrals | ✅ |
| 12 | Notifications + Privacy + Reports | ✅ |
| 13 | Admin Panel (Tickets + Reports + User management + Dashboard + Announcements) | ✅ |
| 14 | Location fields + Referral complete + Reverse geocoding + Search by country | ✅ |
| **15** | **Push notifications + Real Payment + Production** | 🔲 |
| 16+ | Flutter mobile app | 🔲 |

---

## 11. Session 15 Plan: Push Notifications + Production Ready

### Goal
Real push notifications via Firebase Cloud Messaging, real ZarinPal integration, performance optimization, and production readiness.

### Tasks

#### 1. Push Notifications (FCM)

**Files to Create:**

| File | Purpose |
|------|---------|
| `app/services/push_service.py` | FCM send_push(), send_to_topic() |
| `app/models/device_token.py` | Store FCM tokens per user/device |

**Files to Update:**

| File | Changes |
|------|---------|
| `app/services/notification_service.py` | Call push_service after creating DB notification |
| `app/api/v1/endpoints/notifications.py` | Add POST /device-token endpoint |

**Implementation:**

```python
# POST /notifications/device-token
{
    "device_token": "fcm_token_string",
    "device_type": "android"  # or ios
}
```

#### 2. Real Payment Integration (ZarinPal)

**Files to Update:**

| File | Changes |
|------|---------|
| `app/api/v1/endpoints/subscriptions.py` | Replace mock with real ZarinPal calls |
| `app/services/payment_service.py` | NEW - real ZarinPal API integration |

**ZarinPal API Endpoints:**

```python
ZARINPAL_REQUEST_URL = "https://api.zarinpal.com/pg/v4/payment/request.json"
ZARINPAL_VERIFY_URL = "https://api.zarinpal.com/pg/v4/payment/verify.json"
```

**Flow:**
1. User selects plan → POST /subscriptions/purchase
2. Backend calls ZarinPal API → gets redirect URL
3. User pays on ZarinPal
4. ZarinPal redirects to /subscriptions/verify
5. Backend verifies payment → activates premium

#### 3. Performance Optimization

**Indexes to Add:**

```sql
CREATE INDEX idx_users_premium_until ON users(premium_until);
CREATE INDEX idx_users_province ON users(province);
CREATE INDEX idx_users_city ON users(city);
CREATE INDEX idx_notifications_user ON notifications(user_id, is_read, created_at DESC);
CREATE INDEX idx_messages_match ON messages(match_id, created_at DESC);
```

**Other Optimizations:**
- Add DB connection pooling (pool_size=20, max_overflow=40)
- Add Redis connection pool limits
- Review slow queries with logging
- Add response compression (gzip)

#### 4. API Documentation

- Ensure all endpoints have proper OpenAPI `summary`, `description`, `response_model`
- Add example request/response bodies
- Export final OpenAPI spec as `openapi.json`

#### 5. Production Checklist

| Item | Status |
|------|--------|
| Real ZarinPal integration (replace mock) | 🔲 |
| FCM push notifications | 🔲 |
| Device token storage | 🔲 |
| All indexes added | 🔲 |
| DB connection pooling configured | 🔲 |
| Redis connection pooling configured | 🔲 |
| OpenAPI documentation complete | 🔲 |
| Environment variables documented | 🔲 |
| CORS configured for production | 🔲 |
| Rate limiting tuned | 🔲 |
| Logging configured | 🔲 |
| Backup strategy for uploads | 🔲 |

---

## 12. Testing Strategy

### Test Files by Session

| Session | Test Files | Tests |
|---------|------------|-------|
| 1-10 | test_auth, test_users, test_photos, test_swipes, test_matches, test_messages, test_search, test_blocks | ~50 |
| 11 | test_rewards, test_referrals, test_subscriptions, test_daily_limits | 32 |
| 12 | test_notifications, test_reports, test_privacy | 31 |
| 13 | test_tickets, test_admin_tickets, test_admin_reports, test_admin_users, test_admin_dashboard, test_admin_photos, test_admin_messages | 57 |
| 14 | test_location | 25 |

### Run All Tests

```bash
pytest tests/ -v
```

---

## 13. Deployment Notes

### Docker Compose

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
alembic revision --autogenerate -m "description"
alembic upgrade head
alembic downgrade -1
```

### Environment Files

- `.env` - Local development (gitignored)
- `.env.example` - Template (committed)
- `.env.test` - Test environment

---

## Session 11-14 Completion Summary

### ✅ Session 11 Complete

| Feature | Status |
|---------|--------|
| Premium system (premium_until, is_premium) | ✅ |
| Daily limits (20 likes, 10 chats) | ✅ |
| Ad rewards (+5 likes, +3 chats, max 2/day) | ✅ |
| Referral system (codes + rewards) | ✅ |
| Welcome bonus (7 days premium) | ✅ |
| Subscription plans (mock payment) | ✅ |

### ✅ Session 12 Complete

| Feature | Status |
|---------|--------|
| Notifications (like, match, message) | ✅ |
| Reports system (report users) | ✅ |
| Privacy settings (hide_last_seen) | ✅ |

### ✅ Session 13 Complete

| Feature | Status |
|---------|--------|
| Admin authentication (X-Admin-Key) | ✅ |
| Ticket system (user support) | ✅ |
| Report management | ✅ |
| User management (list, activate, deactivate, delete, grant premium) | ✅ |
| User activity tracking | ✅ |
| Admin messaging to users | ✅ |
| Announcements to all/premium users | ✅ |
| Dashboard analytics (overview, user growth, activity charts) | ✅ |
| Photo moderation with face verification | ✅ |

### ✅ Session 14 Complete

| Feature | Status |
|---------|--------|
| Location text fields (country, province, city) | ✅ |
| Reverse geocoding (lat/lng → text location) | ✅ |
| Manual location override with location_manual flag | ✅ |
| Location validation with countrystatecity-countries | ✅ |
| GET /locations/provinces (cached) | ✅ |
| GET /locations/cities (cached) | ✅ |
| Search by country, province, city, distance | ✅ |
| Location cache with @lru_cache | ✅ |
| Complete location tests (25 tests) | ✅ |

### ⚠️ Pending for Production (Session 15)

| Item | Priority |
|------|----------|
| Real ZarinPal integration | High |
| FCM push notifications | High |
| Database indexes | Medium |
| Connection pooling optimization | Medium |
| API documentation (OpenAPI) | Low |

---

**Next: Session 15 - Push Notifications + Real Payment + Production Ready**

Ready to start Session 15 when you are.
```