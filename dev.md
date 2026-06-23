# 📁 **Complete `dev.md` - Updated with Message Encryption**

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
| Encryption | AES-256-GCM (cryptography library) |

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
│   │   │   ├── message.py                 # ✅ Encrypted content support
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
│   │   │   ├── messages.py                # ✅ Updated with encryption
│   │   │   ├── admin_messages.py          # ✅ Admin decryption endpoints
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
│   │   │   ├── chat_service.py            # ✅ Encryption-aware
│   │   │   ├── photo_service.py           # MinIO/S3 storage — upload, public/private bucket move, signed URLs
│   │   │   ├── media_service.py           # ✅ Updated with MinIO support
│   │   │   ├── websocket_manager.py
│   │   │   └── location_service.py
│   │   │
│   │   ├── core/
│   │   │   ├── config.py
│   │   │   ├── security.py
│   │   │   ├── deps.py                    # get_current_user with profile & settings
│   │   │   ├── limiter.py
│   │   │   ├── logging.py
│   │   │   ├── redis.py                   # Refresh tokens + Verification codes
│   │   │   └── encryption.py              # ✅ AES-256-GCM encryption utilities
│   │   │
│   │   └── utils/
│   │       ├── geo.py
│   │       └── pagination.py
│   │
│   ├── alembic/versions/
│   ├── tests/
│   │   ├── conftest.py
│   │   ├── test_auth.py                   # ✅ Passing
│   │   ├── test_users.py                  # ✅ Passing
│   │   ├── test_photos.py                 # ✅ Passing
│   │   ├── test_messages_encryption.py    # ✅ Passing (14 tests)
│   │   ├── test_messages.py               # ✅ Passing (19 tests)
│   │   ├── test_locations.py              # ✅ Passing
│   │   ├── test_swipes.py                 # ⚠️ Needs re-run
│   │   ├── test_matches.py                # ⚠️ Needs re-run
│   │   ├── test_search.py                 # ⚠️ Needs re-run
│   │   ├── test_blocks.py                 # ⚠️ Needs re-run
│   │   ├── test_rewards.py                # ⚠️ Needs re-run
│   │   ├── test_referrals.py              # ⚠️ Needs re-run
│   │   ├── test_subscriptions.py          # ⚠️ Needs re-run
│   │   ├── test_daily_limits.py           # ⚠️ Needs re-run
│   │   ├── test_notifications.py          # ⚠️ Needs re-run
│   │   ├── test_reports.py                # ⚠️ Needs re-run
│   │   ├── test_tickets.py                # ⚠️ Needs re-run
│   │   ├── test_admin_*.py                # ⚠️ Needs re-run
│   │   └── test_location.py               # ⚠️ Needs re-run
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

# File Uploads (legacy — superseded by MinIO below)
MAX_PHOTO_SIZE_MB=10
MAX_PHOTOS_PER_USER=9

# MinIO / S3-compatible object storage (NO DEFAULTS — must be in .env)
S3_ENDPOINT_URL=http://localhost:9000
S3_ACCESS_KEY=minioadmin
S3_SECRET_KEY=minioadmin
S3_REGION=us-east-1
S3_PUBLIC_BUCKET=photos-public
S3_PRIVATE_BUCKET=photos-private
S3_PUBLIC_BASE_URL=http://localhost:9000/photos-public
S3_SIGNED_URL_EXPIRE_SECONDS=900

# ===========================================
# Encryption
# ===========================================
ENCRYPTION_SECRET=your-super-secret-32-byte-key-here-change-in-production

# ============================================
# Chat Media Settings
# ============================================
MAX_CHAT_PHOTO_SIZE_MB=5
MAX_CHAT_VOICE_SIZE_MB=2
MAX_CHAT_VOICE_DURATION=120
ALLOWED_CHAT_IMAGE_FORMATS=JPEG,PNG,WEBP,JPG
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

# ===========================================
# Encryption - Test
# ===========================================
ENCRYPTION_SECRET=test-encryption-secret-32-bytes-long-here

# ============================================
# Chat Media Settings - Test
# ============================================
MAX_CHAT_PHOTO_SIZE_MB=5
MAX_CHAT_VOICE_SIZE_MB=2
MAX_CHAT_VOICE_DURATION=120
ALLOWED_CHAT_IMAGE_FORMATS=JPEG,PNG,WEBP,JPG
```

---

## 6. Database Schema

### `users` Table (Core - Authentication)

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
| registration_status | VARCHAR(20) |
| referral_code | VARCHAR(20) UNIQUE |
| referred_by | UUID |
| created_at | TIMESTAMPTZ |
| last_seen_at | TIMESTAMPTZ |

### `user_profiles` Table (All Profile Data)

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

### `user_settings` Table

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

### `messages` Table

| Column | Type | Notes |
|--------|------|-------|
| id | UUID | |
| match_id | UUID (FK → matches) | Nullable for unmatched chats |
| sender_id | UUID (FK → users) | |
| receiver_id | UUID (FK → users) | |
| message_type | VARCHAR(20) | text, photo, voice |
| **content** | **TEXT** | **✅ ENCRYPTED** - AES-256-GCM |
| reply_to_id | UUID (FK → messages) | |
| media_url | TEXT | MinIO object key |
| media_duration | INTEGER | Voice duration |
| media_size | INTEGER | File size |
| is_sent | BOOLEAN | |
| is_delivered | BOOLEAN | |
| is_read | BOOLEAN | |
| is_deleted_for_sender | BOOLEAN | |
| is_deleted_for_receiver | BOOLEAN | |
| is_deleted_for_all | BOOLEAN | |
| deleted_at | TIMESTAMPTZ | |
| is_accepted | BOOLEAN | Unmatched chat acceptance |
| sent_at | TIMESTAMPTZ | |
| delivered_at | TIMESTAMPTZ | |
| read_at | TIMESTAMPTZ | |
| updated_at | TIMESTAMPTZ | |

### Other Tables (Unchanged)

| Table | Purpose |
|-------|---------|
| swipes | Like/pass records |
| matches | Mutual likes |
| blocks | Blocked users |
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

### Auth Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/auth/register/init` | POST | Email exists check + send code |
| `/auth/register/verify` | POST | Verify code + create user |
| `/auth/register/complete` | POST | Complete profile |
| `/auth/login` | POST | Login with email + password |
| `/auth/google` | POST | Google OAuth login |
| `/auth/refresh` | POST | Refresh access token |
| `/auth/logout` | POST | Logout (revoke refresh token) |
| `/auth/change-password` | POST | Change password |
| `/auth/password-reset` | POST | Request password reset |
| `/auth/password-reset/verify` | POST | Verify reset code + set new password |
| `/auth/health` | GET | Health check |

### Messages Endpoints (Updated)

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/messages/{identifier}` | GET | Get chat history (decrypted) |
| `/messages/{identifier}/text` | POST | Send text message (encrypted) |
| `/messages/{identifier}/photo` | POST | Send photo message (caption encrypted) |
| `/messages/{identifier}/voice` | POST | Send voice message |
| `/messages/{identifier}/accept` | POST | Accept unmatched chat |
| `/messages/delivered` | POST | Mark messages as delivered |
| `/messages/read` | POST | Mark messages as read |
| `/messages/{message_id}` | DELETE | Delete message |
| `/messages/{message_id}/forward` | POST | Forward message (re-encrypted) |
| `/messages/{message_id}/status` | GET | Get message status |

### Admin Messages Endpoints (New)

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/admin/messages/{message_id}/decrypt` | GET | Admin decrypt message |
| `/admin/messages/{message_id}` | DELETE | Admin delete message |
| `/admin/messages/reports/{report_id}/message` | GET | View reported message |

---

## 8. Architecture Decisions

### Message Encryption Architecture (Session 22)

**Server-side AES-256-GCM encryption** for all chat messages:

- **Encryption Algorithm:** AES-256-GCM (authenticated encryption with associated data)
- **Key Derivation:** PBKDF2 with 100,000 iterations
- **Key Material:** `match_id + ENCRYPTION_SECRET`
- **Key Storage:** Keys are NEVER stored - derived on-the-fly
- **Database Storage:** Encrypted content stored in `_content` column
- **Decryption:** Automatic via SQLAlchemy property getter

**Encryption Flow:**
1. Message sent → `match_id` used with `ENCRYPTION_SECRET` to derive key
2. Content encrypted with AES-256-GCM → stored in database
3. On retrieval → content decrypted automatically via property
4. Admin can decrypt via admin endpoints

**Security Benefits:**
- ✅ Database theft exposes only encrypted data
- ✅ Each chat has unique encryption key
- ✅ Admin can decrypt for moderation purposes
- ✅ Client receives decrypted content via API/WebSocket

**Encrypted Content Types:**
- Text messages (full content)
- Photo captions
- Voice message metadata (duration not encrypted)

**Admin Moderation:**
- Admin can decrypt messages via `/api/v1/admin/messages/{id}/decrypt`
- Admin can delete offensive messages
- Admin can view reported messages

**Files Created:**
- `app/core/encryption.py` - Core encryption utilities
- `app/api/v1/endpoints/admin_messages.py` - Admin decryption endpoints

**Files Modified:**
- `app/models/message.py` - Encrypted content property
- `app/services/chat_service.py` - Encryption-aware functions
- `app/api/v1/endpoints/messages.py` - Updated for encryption
- `app/core/config.py` - Added ENCRYPTION_SECRET

### Photo Storage Architecture (MinIO / S3)

Replaced local-disk `uploads/` storage with MinIO (self-hosted, S3-compatible), chosen over managed cloud storage (S3/R2) because the app deploys to a self-managed VPS — MinIO runs in the same Docker Compose stack as Postgres/Redis, no external account or cross-border data dependency.

**Two-bucket split by moderation status:**

| Bucket | Holds | Access |
|--------|-------|--------|
| `photos-private` | `pending`, `rejected` photos | Signed URLs only (15 min expiry), owner can still view their own |
| `photos-public` | `approved` photos | Plain public URL, anonymous read (bucket policy via `mc anonymous set download`) |

- `Photo.url` stores the object **key** only (e.g. `users/{id}/{photo_id}.jpg`), never a full URL
- On admin approval, `PhotoService.publish_photo()` copies the object from `photos-private` → `photos-public` and deletes the original
- `PhotoService.get_photo_url(key, status)` resolves the correct URL at read time: public URL if `approved`, signed private URL otherwise

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
| 15 | Push notifications + Real Payment + Production | 🔲 |
| 16-17 | Flutter mobile app - Auth screens (Splash, Login, Sign Up, Verify) | ✅ |
| 18 | Flutter - Token persistence + Backend compatibility fixes | ✅ |
| 19 | Flutter - Onboarding Flow (Lifestyle, Interests, Location) | 🔲 |
| 20 | Flutter - Main App Features (Discover, Search, Chats, Profile) | 🔲 |
| 21 | Flutter - Polish & Production | 🔲 |
| **22** | **Message Encryption (AES-256-GCM)** | ✅ |

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
| 1-10 | test_auth, test_users, test_photos | ~50+ | ✅ Passing |
| 1-10 (cont.) | test_swipes, test_matches, test_search, test_blocks | — | ⚠️ Needs re-run |
| 11 | test_rewards, test_referrals, test_subscriptions, test_daily_limits | 32 | ⚠️ Needs re-run |
| 12 | test_notifications, test_reports | 31 | ⚠️ Needs re-run |
| 13 | test_tickets, test_admin_* | 57 | ⚠️ Needs re-run |
| 14 | test_location | 25 | ⚠️ Needs re-run |
| 16-18 | test_auth, test_users | — | ✅ Passing |
| **22** | **test_messages_encryption.py** | **14** | **✅ Passing** |
| **22** | **test_messages.py** | **19** | **✅ Passing** |
| **22** | **test_locations.py** | **19** | **✅ Passing** |

### Run All Tests

```bash
pytest tests/ -v
```

### Run a Single File

```bash
pytest tests/test_messages_encryption.py -v
```

---

## 13. Deployment Notes

### Docker Compose (Development)

```yaml
version: '3.9'

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

### Docker Compose (Testing)

```yaml
version: '3.9'

services:
  db_test:
    image: postgis/postgis:15-3.3