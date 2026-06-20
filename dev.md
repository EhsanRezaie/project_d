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
| File storage | MinIO (S3-compatible, self-hosted) — public/private bucket split by moderation status |
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
│   │   ├── db/
│   │   │   ├── base.py
│   │   │   ├── session.py
│   │   │   ├── seed_data/
│   │   │   │   └── interests.json             # 158 interests, 13 categories
│   │   │   └── scripts/
│   │   │       └── seed_interests.py          # Idempotent upsert seed/sync script
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
│   │   │   ├── users.py                   # GET /me returns UserProfileResponse
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
│   │   │   ├── photo_service.py           # MinIO/S3 storage — upload, public/private bucket move, signed URLs
│   │   │   ├── websocket_manager.py
│   │   │   └── location_service.py
│   │   │
│   │   ├── core/
│   │   │   ├── config.py
│   │   │   ├── security.py
│   │   │   ├── deps.py                    # get_current_user with profile & settings
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
│   │   ├── test_auth.py                   # ✅ Passing (re-verified post-MinIO migration)
│   │   ├── test_users.py                  # ✅ Passing (re-verified post-MinIO migration)
│   │   ├── test_photos.py                 # ✅ Passing — real MinIO round-trip tests, no mocking
│   │   ├── test_swipes.py                 # ⚠️ Needs re-run (not verified since MinIO migration)
│   │   ├── test_matches.py                # ⚠️ Needs re-run (not verified since MinIO migration)
│   │   ├── test_messages.py               # ⚠️ Needs re-run (not verified since MinIO migration)
│   │   ├── test_search.py                 # ⚠️ Needs re-run (not verified since MinIO migration)
│   │   ├── test_blocks.py                 # ⚠️ Needs re-run (not verified since MinIO migration)
│   │   ├── test_rewards.py                # ⚠️ Needs re-run (not verified since MinIO migration)
│   │   ├── test_referrals.py              # ⚠️ Needs re-run (not verified since MinIO migration)
│   │   ├── test_subscriptions.py          # ⚠️ Needs re-run (not verified since MinIO migration)
│   │   ├── test_daily_limits.py           # ⚠️ Needs re-run (not verified since MinIO migration)
│   │   ├── test_notifications.py          # ⚠️ Needs re-run (not verified since MinIO migration)
│   │   ├── test_reports.py                # ⚠️ Needs re-run (not verified since MinIO migration)
│   │   ├── test_tickets.py                # ⚠️ Needs re-run (not verified since MinIO migration)
│   │   ├── test_admin_tickets.py          # ⚠️ Needs re-run (not verified since MinIO migration)
│   │   ├── test_admin_reports.py          # ⚠️ Needs re-run (not verified since MinIO migration)
│   │   ├── test_admin_users.py            # ⚠️ Needs re-run (not verified since MinIO migration)
│   │   ├── test_admin_dashboard.py        # ⚠️ Needs re-run (not verified since MinIO migration)
│   │   ├── test_admin_photos.py           # ⚠️ Needs re-run (admin_photos.py changed — name-field bug fix, publish/unpublish wiring)
│   │   ├── test_admin_messages.py         # ⚠️ Needs re-run (not verified since MinIO migration)
│   │   └── test_location.py               # ⚠️ Needs re-run (not verified since MinIO migration)
│   │
│   ├── uploads/
│   ├── .env
│   ├── .env.example
│   ├── .env.test
│   ├── docker-compose.yml                 # db, redis, minio, minio-init
│   ├── docker-compose_test.yml            # db_test, redis_test, minio-test, minio-test-init
│   ├── requirements.txt
│   └── Dockerfile
│
└── mobile/                                # Flutter app (Session 16+)
    ├── lib/
    │   ├── main.dart
    │   ├── config/
    │   │   ├── app_constants.dart
    │   │   └── app_theme.dart
    │   ├── models/
    │   │   └── user.dart                  # Full Badoo fields
    │   ├── services/
    │   │   ├── api_service.dart           # Dio + interceptors
    │   │   ├── auth_service.dart          # 3-step registration
    │   │   └── storage_service.dart       # Token storage + userId
    │   ├── providers/
    │   │   ├── auth_provider.dart         # Auth state + token persistence
    │   │   ├── language_provider.dart
    │   │   └── onboarding_provider.dart   # Multi-step profile data
    │   └── screens/
    │       ├── splash_screen.dart
    │       ├── login_screen.dart          # Welcome + Login combined
    │       ├── main_screen.dart           # Bottom nav + onboarding check
    │       ├── auth/
    │       │   ├── sign_up_screen.dart    # Step 1: Email + Password
    │       │   └── verify_code_screen.dart # Step 2: OTP + Referral
    │       └── onboarding/
    │           ├── personal_info_screen.dart  # Step 3a: Name, Birth Date, Gender
    │           ├── lifestyle_screen.dart      # Step 3b: (TODO)
    │           ├── interests_screen.dart      # Step 3c: (TODO)
    │           └── location_screen.dart       # Step 3d: (TODO)
    ├── pubspec.yaml
    └── .env
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

# File Uploads (legacy — superseded by MinIO below; UPLOADS_DIR/local
# static mount in main.py can be removed once fully migrated)
UPLOADS_DIR=uploads
MAX_PHOTO_SIZE_MB=5
MAX_PHOTOS_PER_USER=6

# MinIO / S3-compatible object storage (NO DEFAULTS — must be in .env)
S3_ENDPOINT_URL=http://localhost:9000
S3_ACCESS_KEY=minioadmin
S3_SECRET_KEY=minioadmin
S3_REGION=us-east-1
S3_PUBLIC_BUCKET=photos-public
S3_PRIVATE_BUCKET=photos-private
S3_PUBLIC_BASE_URL=http://localhost:9000/photos-public
S3_SIGNED_URL_EXPIRE_SECONDS=900
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

# MinIO / S3 — points at the minio-test service (docker-compose_test.yml)
S3_ENDPOINT_URL=http://localhost:9090
S3_ACCESS_KEY=minioadmin
S3_SECRET_KEY=minioadmin
S3_REGION=us-east-1
S3_PUBLIC_BUCKET=photos-public-test
S3_PRIVATE_BUCKET=photos-private-test
S3_PUBLIC_BASE_URL=http://localhost:9090/photos-public-test
S3_SIGNED_URL_EXPIRE_SECONDS=900
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

#### `photos` Table

| Column | Type | Notes |
|--------|------|-------|
| id | UUID | |
| user_id | UUID (FK → users) | |
| url | VARCHAR | Stores the object **key** (e.g. `users/{id}/{photo_id}.jpg`), NOT a full URL — resolved to a real URL at read time via `PhotoService.get_photo_url()` based on `status` |
| order | SMALLINT | |
| is_main | BOOLEAN | |
| status | VARCHAR(20) | `pending` / `approved` / `rejected` — also determines which bucket the object lives in |
| reject_reason | TEXT | |
| face_verified | BOOLEAN | Currently auto-set True on upload (see TODO in `admin_photos.py`) until real face-match API is wired in |
| created_at | TIMESTAMPTZ | |

### Other Tables (Unchanged)

| Table | Purpose |
|-------|---------|
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

### Photo Storage Architecture (MinIO / S3)

Replaced local-disk `uploads/` storage with MinIO (self-hosted, S3-compatible), chosen over managed cloud storage (S3/R2) because the app deploys to a self-managed VPS — MinIO runs in the same Docker Compose stack as Postgres/Redis, no external account or cross-border data dependency.

**Two-bucket split by moderation status** (not a single bucket with ACL flags):

| Bucket | Holds | Access |
|--------|-------|--------|
| `photos-private` | `pending`, `rejected` photos | Signed URLs only (15 min expiry), owner can still view their own |
| `photos-public` | `approved` photos | Plain public URL, anonymous read (bucket policy via `mc anonymous set download`) |

- `Photo.url` stores the object **key** only (e.g. `users/{id}/{photo_id}.jpg`), never a full URL — the key is identical regardless of which bucket the object is currently in.
- On admin approval, `PhotoService.publish_photo()` copies the object from `photos-private` → `photos-public` and deletes the original — status flip in the DB happens only after the move succeeds, so `status="approved"` never points at a non-public object.
- `PhotoService.get_photo_url(key, status)` resolves the correct URL at read time: public URL if `approved`, signed private URL otherwise.
- **Known gotcha:** MinIO's S3 hostname validation rejects underscores in service hostnames (`minio_test` → `Invalid Request (invalid hostname)`). Any new MinIO-related Docker Compose service must use hyphens (`minio-test`, not `minio_test`).
- **Known gotcha:** bucket *naming* (e.g. `photos-public`) does not itself grant public access — `mc anonymous set download <bucket>` (a real bucket policy) is required; per-object ACLs are legacy/unreliable on MinIO specifically.

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

### Backend Fixes (Session 18)

| Fix | Description |
|-----|-------------|
| `deps.py` | `get_current_user` now loads `profile` and `settings` with `selectinload` |
| `users.py` | `GET /me` returns `UserProfileResponse` with all fields |
| `user.py` schema | Added `model_validator` to extract `is_premium` and `is_profile_complete` from `profile` |
| `users.py` | All PUT/PATCH endpoints now use `profile` for profile fields |

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
| **16-17** | **Flutter mobile app - Auth screens (Splash, Login, Sign Up, Verify)** | ✅ |
| **18** | **Flutter - Token persistence + Backend compatibility fixes** | ✅ |
| **19** | **Flutter - Onboarding Flow (Lifestyle, Interests, Location)** | 🔲 |
| **20** | **Flutter - Main App Features (Discover, Search, Chats, Profile)** | 🔲 |
| **21** | **Flutter - Polish & Production** | 🔲 |

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

#### 2. Real Payment Integration (ZarinPal)

**Files to Update:**

| File | Changes |
|------|---------|
| `app/api/v1/endpoints/subscriptions.py` | Replace mock with real ZarinPal calls |
| `app/services/payment_service.py` | NEW - real ZarinPal API integration |

**ZarinPal Flow:**
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

---

## 12. Testing Strategy

### Test Files by Session

| Session | Test Files | Tests | Status |
|---------|------------|-------|--------|
| 1-10 | test_auth, test_users, test_photos | ~50+ | ✅ Re-verified passing post-MinIO migration |
| 1-10 (cont.) | test_swipes, test_matches, test_messages, test_search, test_blocks | — | ⚠️ Not re-run since MinIO migration |
| 11 | test_rewards, test_referrals, test_subscriptions, test_daily_limits | 32 | ⚠️ Not re-run since MinIO migration |
| 12 | test_notifications, test_reports, test_privacy | 31 | ⚠️ Not re-run since MinIO migration |
| 13 | test_tickets, test_admin_tickets, test_admin_reports, test_admin_users, test_admin_dashboard, test_admin_photos, test_admin_messages | 57 | ⚠️ Not re-run since MinIO migration (test_admin_photos.py especially — admin_photos.py logic changed) |
| 14 | test_location | 25 | ⚠️ Not re-run since MinIO migration |
| **16-17** | **test_auth, test_users** | — | **✅ Passing** |
| **MinIO migration** | **test_photos.py** | **62** | **✅ Passing — real MinIO round-trips, no mocking** |

**Action item:** run the full suite (`pytest tests/ -v`) against the current MinIO-based setup to re-confirm the ⚠️ files. The MinIO/config/docker-compose changes touched shared infrastructure (`config.py` gained required `S3_*` fields with no defaults — app won't even start without them in `.env`/`.env.test`), so any test file is at risk of failing purely on settings load, independent of its own logic.

### Run All Tests

```bash
pytest tests/ -v
```

### Run a Single File

```bash
pytest tests/test_photos.py -v
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

  minio:
    image: minio/minio:latest
    container_name: dating_minio
    command: server /data --console-address ":9001"
    environment:
      MINIO_ROOT_USER: minioadmin
      MINIO_ROOT_PASSWORD: minioadmin
    ports:
      - "9000:9000"   # S3 API
      - "9001:9001"   # Web console
    volumes:
      - minio_data:/data
    healthcheck:
      test: ["CMD", "mc", "ready", "local"]
      interval: 5s
      timeout: 5s
      retries: 5

  # One-shot: creates buckets, sets photos-public to anonymous-read.
  # NOTE: keep service names hyphenated, not underscored — MinIO rejects
  # underscored hostnames ("Invalid Request (invalid hostname)").
  minio-init:
    image: minio/mc:latest
    container_name: dating_minio_init
    depends_on:
      minio:
        condition: service_healthy
    entrypoint: >
      /bin/sh -c "
      mc alias set local http://minio:9000 minioadmin minioadmin &&
      mc mb --ignore-existing local/photos-public &&
      mc mb --ignore-existing local/photos-private &&
      mc anonymous set download local/photos-public &&
      echo 'MinIO buckets ready'
      "

volumes:
  postgres_data:
  minio_data:
```

### Docker Compose (Testing) — `docker-compose_test.yml`

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

  minio-test:
    image: minio/minio:latest
    container_name: dating_minio_test
    command: server /data --console-address ":9091"
    environment:
      MINIO_ROOT_USER: minioadmin
      MINIO_ROOT_PASSWORD: minioadmin
    ports:
      - "9090:9000"   # S3 API
      - "9091:9091"   # Web console
    volumes:
      - minio_test_data:/data
    healthcheck:
      test: ["CMD", "mc", "ready", "local"]
      interval: 5s
      timeout: 5s
      retries: 5

  minio-test-init:
    image: minio/mc:latest
    container_name: dating_minio_test_init
    depends_on:
      minio-test:
        condition: service_healthy
    entrypoint: >
      /bin/sh -c "
      mc alias set local http://minio-test:9000 minioadmin minioadmin &&
      mc mb --ignore-existing local/photos-public-test &&
      mc mb --ignore-existing local/photos-private-test &&
      mc anonymous set download local/photos-public-test &&
      echo 'Test MinIO buckets ready'
      "

volumes:
  postgres_test_data:
  minio_test_data:
```

To run/reset the test stack:

```bash
docker compose -f docker-compose_test.yml down -v --remove-orphans
docker compose -f docker-compose_test.yml up -d
docker compose -f docker-compose_test.yml logs minio-test-init   # confirm "Test MinIO buckets ready"
pytest tests/ -v
```

### Alembic Commands

```bash
alembic revision --autogenerate -m "description"
alembic upgrade head
alembic downgrade -1
```

---

## Session 11-18 Completion Summary

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

### ✅ Session 16-17 Complete (Flutter Auth)
| Feature | Status |
|---------|--------|
| Flutter project setup | ✅ |
| Auth screens (Splash, Login, Sign Up, Verify) | ✅ |
| API integration with Dio | ✅ |
| State management with Provider | ✅ |
| Theme system (Light/Dark) | ✅ |
| Multi-language (English/Persian) | ✅ |

### ✅ Session 18 Complete (Flutter Auth + Backend Fixes)
| Feature | Status |
|---------|--------|
| Token persistence on app restart | ✅ |
| 3-step registration flow | ✅ |
| VerifyCodeScreen with OTP + referral | ✅ |
| LoginScreen (Welcome + Login combined) | ✅ |
| MainScreen with bottom nav | ✅ |
| ProfileScreen with user info + logout | ✅ |
| Backend `deps.py` fixed (selectinload for profile/settings) | ✅ |
| Backend `users.py` fixed (UserProfileResponse) | ✅ |
| Backend `user.py` schema fixed (model_validator) | ✅ |
| Fixed `initState` notifyListeners error | ✅ |

### ✅ Photo Storage Migration Complete (Local Disk → MinIO)
| Feature | Status |
|---------|--------|
| MinIO added to docker-compose.yml + docker-compose_test.yml | ✅ |
| `photo_service.py` rewritten for MinIO/S3 (aioboto3) | ✅ |
| Public/private bucket split by moderation status | ✅ |
| `admin_photos.py` — approve now calls `publish_photo()`, name-field bug fixed (was `user.name`, now correctly `profile.name` via join) | ✅ |
| `photos.py` — responses resolve object key to real URL via `get_photo_url()` | ✅ |
| `test_photos.py` — 62 tests, real MinIO round-trips (no mocking) | ✅ Passing |
| `test_auth.py`, `test_users.py` — re-verified post-migration | ✅ Passing |
| Remaining test files (swipes, matches, messages, search, blocks, rewards, referrals, subscriptions, daily_limits, notifications, reports, tickets, admin_*, location) | ⚠️ Not yet re-run |
| TODO: real face-match API integration (currently all uploads auto-verified — see TODO block in `admin_photos.py`) | 🔲 |

### ⚠️ Pending

| Item | Priority | Session |
|------|----------|---------|
| Re-run full test suite against MinIO setup (swipes, matches, messages, search, blocks, rewards, referrals, subscriptions, daily_limits, notifications, reports, tickets, admin_*, location) | High | — |
| Real ZarinPal integration | High | 15 |
| FCM push notifications | High | 15 |
| Database indexes | Medium | 15 |
| Real face-match API (photo verification) | Medium | — |
| Onboarding Flow (Flutter) | High | 19 |
| Main App Features (Flutter) | High | 20 |
| Polish & Production (Flutter) | Medium | 21 |

---

**Next: Session 15 - Push Notifications + Real Payment + Production Ready (Backend)**

**Then: Session 19 - Flutter Onboarding Flow (Lifestyle, Interests, Location)**

Ready to start when you are. 🚀
```