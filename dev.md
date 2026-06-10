You're right. Let me give you a clean, detailed `dev.md` without the redundant command sections:

```markdown
# dev.md — Iranian Dating App

> **Purpose:** This file is the single source of truth for the project.  
> It is updated at the end of every session and passed to Claude at the start of the next one.  
> Claude should read this fully before doing anything in a new session.

---

## Project Status

- **Session:** 9 (Completed)
- **Current Phase:** Match list + WebSocket notifications fully implemented ✅
- **Next Phase:** Chat system (messages + WebSocket chat)

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

---

## Final Tech Stack

| Tool | Role |
|------|------|
| FastAPI | Main framework |
| PostgreSQL + PostGIS | Primary database |
| Redis | Caching, pub/sub, rate limiting, refresh tokens |
| WebSocket | Realtime chat and notifications |
| SQLAlchemy (async) | ORM |
| Alembic | Migrations |
| Docker | Containerization |
| Flutter | Mobile app |

---

## Key Decisions

### Authentication ✅

- Email/Password or Google OAuth
- JWT with access token (7 days) + refresh token (30 days)
- Refresh tokens stored in Redis with 30-day TTL
- Refresh token rotation (old revoked on each refresh)
- Token versioning in User model for instant revocation
- `is_profile_complete` flag for Google OAuth users
- Health check endpoint for Redis monitoring

### Rate Limiting ✅

- Implemented via slowapi + Redis backend
- Different limits per endpoint (register: 5/min, login: 10/min, etc.)
- Disabled during tests

### Photo System ✅

- Max 6 photos per user
- Upload validation: 5MB max, 200x200 min, JPEG/PNG/WEBP
- Photos saved to `uploads/users/{user_id}/{photo_id}.jpg`
- Status: pending → approved/rejected (admin review)
- First photo automatically becomes main
- Admin endpoints: list pending, approve, reject, stats

### Discovery Modes ✅

| Mode | Endpoint | Excludes swiped? | Filters |
|------|----------|------------------|---------|
| Discover | GET /discover | Yes | Age, Distance |
| Search | GET /search | No (only blocks) | Age, Distance, Gender, Height, Weight, Verified, Has Photos |

### Swipe System ✅

- POST /swipes — like or pass
- 50 likes/day limit for free users (daily_limits table)
- Match created when both users like each other
- WebSocket notification sent to both users on match

### Match System ✅

- GET /matches — list with last message preview
- GET /matches/{id} — details with both user profiles
- WS /ws/matches — real-time match notifications
- Uses `selectinload` for eager loading (async SQLAlchemy)

### Block System ✅

- POST /blocks/{user_id}/block — block user
- POST /blocks/{user_id}/unblock — unblock user
- GET /blocks — list blocked users
- Blocked users excluded from Discover and Search

---

## Database Schema

### Tables (8 implemented)

| Table | Key Columns |
|-------|-------------|
| users | id, email, name, age, gender, lat/lng, is_premium, token_version |
| photos | user_id, url, is_main, status, reject_reason |
| swipes | from_user, to_user, direction, created_at |
| matches | user1_id, user2_id, is_active, matched_at |
| daily_limits | user_id, date, likes_used, chats_used |
| blocks | blocker_id, blocked_id |
| messages | match_id, sender_id, receiver_id, content, is_accepted |
| subscriptions | user_id, status, plan, expires_at (🔲 Session 11) |

### Redis Keys

- `refresh_token:{token}` → user_id (30 days)
- `user:{user_id}` → WebSocket pub/sub channel

---

## Project Structure

```
app/
├── api/v1/
│   ├── endpoints/
│   │   ├── auth.py          ✅
│   │   ├── users.py         ✅
│   │   ├── photos.py        ✅
│   │   ├── admin.py         ✅
│   │   ├── discover.py      ✅
│   │   ├── swipes.py        ✅
│   │   ├── search.py        ✅
│   │   ├── blocks.py        ✅
│   │   └── matches.py       ✅
│   └── websocket/
│       └── matches.py       ✅
├── core/                    ✅ (config, security, redis, limiter, logging, deps)
├── db/                      ✅ (base, session)
├── models/                  ✅ (9 models)
├── schemas/                 ✅ (6 schemas)
├── services/                ✅ (photo_service, websocket_manager)
└── main.py                  ✅

tests/                       ✅ (9 test files)
```

---

## Session Log

| Session | Completed |
|---------|-----------|
| 1 | Planning |
| 2 | Docker, models, FastAPI setup |
| 3 | Auth endpoints |
| 4 | Auth hardening (token versioning, logging, tests) |
| 5 | Users endpoints |
| 6 | Photo upload + admin moderation |
| 7 | Discover + Swipe system |
| 8 | Search + Block system |
| 9 | Match list + WebSocket notifications |

---

## Session 10: Chat System

### What to Build

| Feature | Endpoint | Description |
|---------|----------|-------------|
| Chat history | GET /messages/{match_id} | Paginated messages |
| Send message | POST /messages/{match_id} | Create message |
| Accept chat | POST /messages/{match_id}/accept | Accept unmatched conversation |
| Realtime chat | WS /ws/chat/{match_id} | WebSocket for live messaging |
| Typing indicators | WS event | User typing status |
| Mark as read | WS event | Mark messages as read |

### Business Rules

1. **Unmatched chat:** User can send 2 messages without a match
2. After 2 messages, `is_accepted` must be true to continue
3. **Daily chat limit:** Free users: 10 chats/day (track in `daily_limits.chats_used`)
4. **Matched chat:** No limits, WebSocket for real-time

### Files to Create

| File | Purpose |
|------|---------|
| `app/schemas/message.py` | Message schemas |
| `app/api/v1/endpoints/messages.py` | Message endpoints |
| `app/api/v1/websocket/chat.py` | WebSocket chat handler |
| `app/services/chat_service.py` | Chat business logic |
| `tests/test_messages.py` | Message tests |
| `tests/test_chat_ws.py` | WebSocket chat tests |

### Files to Update

- `app/models/daily_limit.py` — ensure `chats_used` field exists
- `app/main.py` — add new routers

### Files Needed from You

```
1. app/models/message.py
2. app/models/match.py
3. app/models/daily_limit.py
```

---

## Future Sessions

| Session | Focus |
|---------|-------|
| 10 | Chat system (messages + WebSocket) |
| 11 | Premium subscriptions + Ad rewards + Daily limits |
| 12 | Push notifications + Admin dashboard |
| 13 | Face verification + Review rewards |
| 14 | Flutter mobile app start |

---

## Ready for Session 10

Send me:
```
1. app/models/message.py
2. app/models/match.py
3. app/models/daily_limit.py
```
```