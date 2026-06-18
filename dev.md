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
| Cache | Redis 7 (tokens, rate limiting, verification codes) + LRU cache (static location data) |
| Realtime | WebSocket |
| File storage | Local disk (`uploads/`) |
| Containerization | Docker + Docker Compose |
| Mobile | Flutter |
| Payment | ZarinPal (MOCKED - real integration needed) |
| Location | countrystatecity-countries package |
| Reverse Geocoding | Nominatim (OpenStreetMap) |
| Email | SMTP/SendGrid (TODO) |

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
│   │   │   ├── user.py                    # Core user model (auth only)
│   │   │   ├── user_profile.py            # User profile data (name, birth_date, gender, etc.)
│   │   │   ├── user_settings.py           # User settings (privacy, notifications)
│   │   │   ├── interest.py                # Available interests
│   │   │   ├── user_interest.py           # User interests (many-to-many)
│   │   │   ├── prompt.py                  # Available prompts/questions
│   │   │   ├── user_prompt.py             # User answers to prompts
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
│   │   │   ├── auth.py                    # 3-step registration schemas
│   │   │   ├── user.py                    # User profile schemas with all Badoo fields
│   │   │   ├── settings.py                # User settings schemas
│   │   │   ├── interest.py
│   │   │   ├── prompt.py
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
│   │   │   ├── ticket.py
│   │   │   ├── admin.py
│   │   │   ├── dashboard.py
│   │   │   └── location.py
│   │   │
│   │   ├── api/v1/endpoints/
│   │   │   ├── auth.py                    # 3-step registration: init → verify → complete
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
│   │   │   ├── email_service.py           # Email sending (verification, password reset)
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
│   │   │   └── redis.py                   # Refresh tokens + Verification codes
│   │   │
│   │   └── utils/
│   │       ├── geo.py
│   │       └── pagination.py
│   │
│   ├── alembic/versions/
│   ├── tests/
│   │   ├── conftest.py
│   │   ├── test_auth.py                   # ✅ All tests passing
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
│   ├── .env.test
│   ├── docker-compose.yml
│   ├── docker-compose.test.yml
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

### `.env.test`

```env
DATABASE_URL=postgresql+asyncpg://dating_user:dating_pass@localhost:5433/dating_test
REDIS_URL=redis://localhost:6380

SECRET_KEY=test-secret-key
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=10080
ADMIN_SECRET_KEY=test-admin-key

APP_NAME=DatingApp
DEBUG=True

FREE_USER_DAILY_LIKES=20
FREE_USER_DAILY_CHATS=10
AD_REWARD_LIKES_BONUS=5
AD_REWARD_CHATS_BONUS=3
MAX_AD_REWARDS_PER_DAY=2
WELCOME_BONUS_DAYS=7
REFERRAL_INVITER_DAYS=3
REFERRAL_INVITED_DAYS=3
SUBSCRIPTION_MONTHLY_DAYS=30
SUBSCRIPTION_QUARTERLY_DAYS=90
SUBSCRIPTION_YEARLY_DAYS=365
SUBSCRIPTION_QUARTERLY_DISCOUNT=15
SUBSCRIPTION_YEARLY_DISCOUNT=30

ZARINPAL_MERCHANT_ID=
ZARINPAL_SANDBOX=true
ZARINPAL_CALLBACK_URL=

UPLOADS_DIR=uploads
MAX_PHOTO_SIZE_MB=5
MAX_PHOTOS_PER_USER=6
```

---

## 6. Database Schema

### New Schema Design (Session 16-17)

#### `users` Table (Core - Authentication)

| Column | Type |
|--------|------|
| id | UUID |
| email | VARCHAR(255) UNIQUE |
| password_hash | VARCHAR(255) |
| google_id | VARCHAR(255) UNIQUE |
| phone | VARCHAR(20) |
| phone_verified | BOOLEAN |
| is_active | BOOLEAN |
| token_version | INTEGER |
| registration_status | VARCHAR(20) |  # email_pending, email_verified, onboarding_complete
| referral_code | VARCHAR(20) UNIQUE |
| referred_by | UUID |
| created_at | TIMESTAMPTZ |
| last_seen_at | TIMESTAMPTZ |

#### `user_profiles` Table (All Profile Data)

| Column | Type |
|--------|------|
| id | UUID |
| user_id | UUID (FK → users) |
| name | VARCHAR(100) |
| birth_date | DATE |
| gender | VARCHAR(10) |
| sexual_orientation | VARCHAR(20) |
| bio | TEXT |
| height | SMALLINT |
| weight | SMALLINT |
| body_type | VARCHAR(20) |
| relationship_status | VARCHAR(20) |
| living_situation | VARCHAR(30) |
| children_status | VARCHAR(20) |
| smoking | VARCHAR(20) |
| drinking | VARCHAR(20) |
| languages | JSON |
| education | VARCHAR(50) |
| workplace | VARCHAR(100) |
| religion | VARCHAR(50) |
| ethnicity | VARCHAR(50) |
| political_orientation | VARCHAR(30) |
| lat | DOUBLE |
| lng | DOUBLE |
| country | VARCHAR(100) |
| province | VARCHAR(100) |
| city | VARCHAR(100) |
| location_manual | BOOLEAN |
| is_verified | BOOLEAN |
| premium_until | TIMESTAMPTZ |
| created_at | TIMESTAMPTZ |
| updated_at | TIMESTAMPTZ |

#### `user_settings` Table

| Column | Type |
|--------|------|
| id | UUID |
| user_id | UUID (FK → users) |
| hide_last_seen | BOOLEAN |
| hide_online_status | BOOLEAN |
| push_enabled | BOOLEAN |
| like_notifications | BOOLEAN |
| match_notifications | BOOLEAN |
| message_notifications | BOOLEAN |
| language | VARCHAR(10) |
| dark_mode | BOOLEAN |
| created_at | TIMESTAMPTZ |
| updated_at | TIMESTAMPTZ |

#### `interests` Table

| Column | Type |
|--------|------|
| id | UUID |
| name | VARCHAR(50) UNIQUE |
| category | VARCHAR(30) |
| icon | VARCHAR(50) |

#### `user_interests` Table (Many-to-Many)

| Column | Type |
|--------|------|
| id | UUID |
| user_id | UUID (FK → users) |
| interest_id | UUID (FK → interests) |

#### `prompts` Table

| Column | Type |
|--------|------|
| id | UUID |
| question | TEXT |
| category | VARCHAR(30) |
| is_active | BOOLEAN |

#### `user_prompts` Table

| Column | Type |
|--------|------|
| id | UUID |
| user_id | UUID (FK → users) |
| prompt_id | UUID (FK → prompts) |
| answer | TEXT |

### Other Tables (Unchanged)

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

### Authentication Flow (3-Step Registration)

| Step | Endpoint | Method | Description |
|------|----------|--------|-------------|
| 1 | `/auth/register/init` | POST | Check email, send verification code |
| 2 | `/auth/register/verify` | POST | Verify code, create user with email+password |
| 3 | `/auth/register/complete` | POST | Complete profile with all fields |

### Auth Endpoints (Updated)

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/auth/register/init` | POST | Email exists check + send code |
| `/auth/register/verify` | POST | Verify code + create user |
| `/auth/register/complete` | POST | Complete profile (name, birth_date, gender, etc.) |
| `/auth/login` | POST | Login with email + password |
| `/auth/google` | POST | Google OAuth login |
| `/auth/refresh` | POST | Refresh access token |
| `/auth/logout` | POST | Logout (revoke refresh token) |
| `/auth/change-password` | POST | Change password |
| `/auth/password-reset` | POST | Request password reset |
| `/auth/password-reset/verify` | POST | Verify reset code + set new password |
| `/auth/health` | GET | Health check |

### Users Endpoints (Updated)

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/users/me` | GET | Get current user profile with all fields |
| `/users/me` | PUT | Update profile (all Badoo fields) |
| `/users/me` | DELETE | Soft delete account |
| `/users/me/location` | POST | Update GPS location |
| `/users/me/location-text` | PATCH | Update location manually |
| `/users/{user_id}` | GET | Get public user profile |

---

## 8. Architecture Decisions

### Authentication Flow (3-Step)

```
Step 1: POST /auth/register/init
   ↓
   Check email → send 6-digit code (Redis, TTL 5min)
   ↓
Step 2: POST /auth/register/verify
   ↓
   Verify code → create User (email, password_hash, registration_status="email_verified")
   ↓
   Return access_token + refresh_token
   ↓
Step 3: POST /auth/register/complete (Authenticated)
   ↓
   Save all profile fields → registration_status="onboarding_complete"
   ↓
   Return new tokens with full profile
```

### Profile Fields (Badoo-complete)

| Category | Fields |
|----------|--------|
| Identity | name, birth_date, gender, sexual_orientation, bio |
| Appearance | height, weight, body_type |
| Lifestyle | relationship_status, living_situation, children_status, smoking, drinking |
| Background | education, workplace, religion, ethnicity, political_orientation, languages |
| Location | lat, lng, country, province, city, location_manual |
| Interests | List of interest names |
| Prompts | List of {prompt_id, answer} |

### Token Management

- Access Token: JWT (7 days) with `ver` (token_version)
- Refresh Token: Opaque (Redis, 30 days)
- Token Rotation: Old refresh token revoked on refresh
- Password Change: Increment token_version, revoke all tokens

### Redis Keys

| Key Pattern | Purpose | TTL |
|-------------|---------|-----|
| `refresh_token:{token}` | Store user_id | 30 days |
| `verification:{email}` | Store 6-digit code | 5 minutes |

### Email Service

| Function | Purpose |
|----------|---------|
| `send_verification_code(email, code)` | Send 6-digit verification code |
| `send_password_reset_code(email, code)` | Send password reset code |
| `send_welcome_email(email, name)` | Send welcome email |

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
| **16-17** | **Flutter mobile app - Auth screens (Splash, Welcome, Login, Sign Up)** | ✅ |
| **18** | **Flutter - Onboarding Flow (4 steps)** | 🔲 |
| **19** | **Flutter - Main App Features** | 🔲 |
| **20** | **Flutter - Polish & Production** | 🔲 |

### ✅ Session 16-17 Complete (Flutter)

| Feature | Status |
|---------|--------|
| Flutter project setup | ✅ |
| Dependencies installed | ✅ |
| Folder structure created | ✅ |
| Environment variables (.env) | ✅ |
| API Service (Dio) with interceptors | ✅ |
| Auth Service (login, register, healthCheck) | ✅ |
| Storage Service (secure token storage) | ✅ |
| Auth Provider (state management) | ✅ |
| Onboarding Provider | ✅ |
| Language Provider | ✅ |
| App Theme (Light/Dark mode ready) | ✅ |
| Splash Screen (with progress bar & random target) | ✅ |
| Welcome Screen (enhanced) | ✅ |
| Login Screen (with validation) | ✅ |
| Sign Up Screen (with validation) | ✅ |
| Email & Password validation | ✅ |
| Password visibility toggle | ✅ |
| Language selection (English/Persian) | ✅ |
| Google Sign-In button with custom icon | ✅ |
| Input filtering (English only) | ✅ |
| Real-time validation with localized errors | ✅ |
| Password min length: 8 characters | ✅ |
| Health Check on Splash | ✅ |
| Retry button on connection error | ✅ |
| Token refresh interceptor | ✅ |
| Theme-aware colors (Light/Dark ready) | ✅ |
| Keyboard handling (resize & dismiss on tap) | ✅ |
| All auth tests passing ✅ | ✅ |

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
| **16-17** | **test_auth (updated), test_users (updated)** | **✅ All passing** |

### Run All Tests

```bash
pytest tests/ -v
```

### Run Specific Test

```bash
pytest tests/test_auth.py -v
```

---

## 13. Deployment Notes

### Docker Compose (Development)

```yaml
services:
  db:
    image: postgis/postgis:15-3.3
    container_name: dating_db
    environment:
      POSTGRES_USER: dating_user
      POSTGRES_PASSWORD: dating_pass
      POSTGRES_DB: dating_db
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data

  redis:
    image: redis:7-alpine
    container_name: dating_redis
    ports:
      - "6379:6379"
```

### Docker Compose (Testing)

```yaml
services:
  db_test:
    image: postgis/postgis:15-3.3
    container_name: dating_db_test
    environment:
      POSTGRES_USER: dating_user
      POSTGRES_PASSWORD: dating_pass
      POSTGRES_DB: dating_test
    ports:
      - "5433:5432"
    volumes:
      - postgres_test_data:/var/lib/postgresql/data

  redis_test:
    image: redis:7-alpine
    container_name: dating_redis_test
    ports:
      - "6380:6379"
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

## Session 11-17 Completion Summary

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

### ✅ Session 16-17 Complete (Flutter)
| Feature | Status |
|---------|--------|
| Flutter project setup | ✅ |
| Auth screens (Splash, Welcome, Login, Sign Up) | ✅ |
| API integration with Dio | ✅ |
| State management with Provider | ✅ |
| Theme system (Light/Dark) | ✅ |
| Multi-language (English/Persian) | ✅ |
| All auth tests passing | ✅ |

### ⚠️ Pending

| Item | Priority | Session |
|------|----------|---------|
| Real ZarinPal integration | High | 15 |
| FCM push notifications | High | 15 |
| Database indexes | Medium | 15 |
| Onboarding Flow (Flutter) | High | 18 |
| Main App Features (Flutter) | High | 19 |
| Polish & Production (Flutter) | Medium | 20 |

---

**Next: Session 15 - Push Notifications + Real Payment + Production Ready (Backend)**

**Then: Session 18 - Flutter Onboarding Flow**

Ready to start when you are. 🚀
```