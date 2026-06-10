Here's the updated `dev.md` for Session 10 completion:

```markdown
# dev.md — Iranian Dating App

> **Purpose:** This file is the single source of truth for the project.  
> It is updated at the end of every session and passed to Claude at the start of the next one.  
> Claude should read this fully before doing anything in a new session.

---

## Project Status

- **Session:** 10 (Completed)
- **Current Phase:** Chat system fully implemented (text, photo, voice, reply, delete, forward, WebSocket) ✅
- **Next Phase:** Premium subscriptions + Ad rewards + Daily limits

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
- Different limits per endpoint
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

### Chat System ✅ (Session 10)

| Feature | Endpoint | Status |
|---------|----------|--------|
| Chat history | GET /messages/{match_id} | ✅ |
| Text message | POST /messages/{match_id}/text | ✅ |
| Photo message | POST /messages/{match_id}/photo | ✅ |
| Voice message | POST /messages/{match_id}/voice | ✅ |
| Accept chat | POST /messages/{match_id}/accept | ✅ |
| Mark delivered | POST /messages/delivered | ✅ |
| Mark read | POST /messages/read | ✅ |
| Delete message | DELETE /messages/{message_id} | ✅ |
| Forward message | POST /messages/{message_id}/forward | ✅ |
| Message status | GET /messages/{message_id}/status | ✅ |
| Realtime chat | WS /ws/chat/{match_id} | ✅ |

---

## Database Schema

### Tables (9 implemented)

| Table | Key Columns |
|-------|-------------|
| users | id, email, name, age, gender, lat/lng, is_premium, token_version |
| photos | user_id, url, is_main, status, reject_reason |
| swipes | from_user, to_user, direction, created_at |
| matches | user1_id, user2_id, is_active, matched_at |
| daily_limits | user_id, date, likes_used, chats_used, ad_likes_bonus, ad_chats_bonus |
| blocks | blocker_id, blocked_id |
| messages | match_id, sender_id, receiver_id, message_type, content, media_url, reply_to_id, is_accepted, is_read, is_delivered, is_deleted_for_sender, is_deleted_for_receiver, is_deleted_for_all |
| subscriptions | user_id, status, plan, expires_at (🔲 Session 11) |
| reports | reporter_id, reported_id, reason (🔲 Future) |

### Message Fields Detail

```sql
-- messages table fields
id                  UUID PRIMARY KEY
match_id            UUID REFERENCES matches(id) (nullable for unmatched chats)
sender_id           UUID REFERENCES users(id)
receiver_id         UUID REFERENCES users(id)
message_type        VARCHAR(20) DEFAULT 'text'  -- text, photo, voice
content             TEXT
reply_to_id         UUID REFERENCES messages(id)
media_url           TEXT
media_duration      INTEGER  -- for voice messages
media_size          INTEGER
is_sent             BOOLEAN DEFAULT TRUE
is_delivered        BOOLEAN DEFAULT FALSE
is_read             BOOLEAN DEFAULT FALSE
is_accepted         BOOLEAN DEFAULT FALSE
is_deleted_for_sender   BOOLEAN DEFAULT FALSE
is_deleted_for_receiver BOOLEAN DEFAULT FALSE
is_deleted_for_all      BOOLEAN DEFAULT FALSE
deleted_at          TIMESTAMPTZ
sent_at             TIMESTAMPTZ
delivered_at        TIMESTAMPTZ
read_at             TIMESTAMPTZ
updated_at          TIMESTAMPTZ
```

### Redis Keys

- `refresh_token:{token}` → user_id (30 days)
- `user:{user_id}` → WebSocket pub/sub channel
- `chat:{match_id}:{user_id}` → Chat WebSocket connections

### File Storage

```
uploads/
├── users/                    # Profile photos
│   └── {user_id}/
│       └── {photo_id}.jpg
└── chat/                     # Chat media
    ├── photo/
    │   └── {match_id}/
    │       └── {message_id}.jpg
    └── voice/
        └── {match_id}/
            └── {message_id}.mp3
```

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
│   │   ├── matches.py       ✅
│   │   └── messages.py      ✅
│   └── websocket/
│       ├── matches.py       ✅
│       └── chat.py          ✅
├── core/                    ✅ (config, security, redis, limiter, logging, deps)
├── db/                      ✅ (base, session)
├── models/                  ✅ (9 models)
├── schemas/                 ✅ (7 schemas)
├── services/                ✅ (photo_service, websocket_manager, chat_service, media_service)
└── main.py                  ✅

tests/                       ✅ (10 test files)
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
| 10 | Chat system (text, photo, voice, reply, delete, forward, WebSocket) |

---

## Session 10 Completed Features

### REST Endpoints
- `GET /api/v1/messages/{match_id}` — Chat history with pagination
- `POST /api/v1/messages/{match_id}/text` — Send text message (with reply support)
- `POST /api/v1/messages/{match_id}/photo` — Send photo (5MB max, auto-compress)
- `POST /api/v1/messages/{match_id}/voice` — Send voice (2 min max)
- `POST /api/v1/messages/{match_id}/accept` — Accept unmatched chat
- `POST /api/v1/messages/read` — Mark messages as read
- `POST /api/v1/messages/delivered` — Mark messages as delivered
- `DELETE /api/v1/messages/{message_id}` — Delete message (me/everyone)
- `POST /api/v1/messages/{message_id}/forward` — Forward to another chat
- `GET /api/v1/messages/{message_id}/status` — Get delivery/read status

### WebSocket
- `WS /ws/chat/{match_id}?token={access_token}` — Realtime chat
  - Send/receive text, photo, voice
  - Typing indicators
  - Delivery receipts
  - Read receipts

### Business Rules Implemented
- Unmatched chat: 2 messages limit before acceptance
- Daily new chat limit: 10/day for free users
- Delete for everyone: 1 hour window
- Photo/voice messages: only in accepted/matched chats

---

## Next Session (Session 11) - Premium + Ads + Daily Limits

### What to Build

| Feature | Description |
|---------|-------------|
| Premium subscriptions | Monthly/quarterly plans via ZarinPal |
| Daily like limit | 50/day for free users (already implemented, needs premium override) |
| Daily chat limit | 10 new chats/day for free users (already implemented) |
| Ad reward system | Watch ad → +5 likes, +1 new chat |
| Subscription webhook | Verify payments from ZarinPal |
| Premium status check | GET /api/v1/subscriptions/me |

### Files to Create

| File | Purpose |
|------|---------|
| `app/models/subscription.py` | Subscription model |
| `app/schemas/subscription.py` | Subscription schemas |
| `app/api/v1/endpoints/subscriptions.py` | Subscription endpoints |
| `app/api/v1/endpoints/rewards.py` | Ad reward endpoints |
| `app/services/payment_service.py` | ZarinPal integration |
| `tests/test_subscriptions.py` | Subscription tests |

### Files to Update

| File | Changes |
|------|---------|
| `app/models/user.py` | Add `is_premium` check (already exists) |
| `app/api/v1/endpoints/swipes.py` | Use premium status for unlimited likes |
| `app/services/chat_service.py` | Use premium status for unlimited chats |

---

## Future Sessions

| Session | Focus |
|---------|-------|
| 11 | Premium subscriptions + Ad rewards + Daily limits |
| 12 | Push notifications + Admin dashboard |
| 13 | Face verification + Review rewards |
| 14 | Flutter mobile app start |

---

## Useful Commands

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

### WebSocket connections
```javascript
// Match notifications
ws = new WebSocket("ws://localhost:8000/ws/matches?token=ACCESS_TOKEN")

// Chat
ws = new WebSocket("ws://localhost:8000/ws/chat/{match_id}?token=ACCESS_TOKEN")
```

### Admin endpoints
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
- WebSocket manager handles both match and chat connections
- Chat supports text, photo, voice messages
- Delete for everyone available within 1 hour window
- Unmatched chat requires acceptance after 2 messages
- Daily new chat limit: 10/day for free users
- Ready for Session 11: Premium subscriptions + Ad rewards
```

Now commit the changes:

```bash
git add .
git commit -m "feat(chat): implement complete chat system with WebSocket

- Add message endpoints (text, photo, voice)
- Add reply to messages functionality
- Add delete for me / delete for everyone (1 hour window)
- Add forward messages to other chats
- Add message status tracking (sent → delivered → read)
- Add WebSocket chat with typing indicators
- Add unmatched chat limits (2 messages before accept)
- Add daily new chat limit (10/day for free users)
- Add photo/voice upload with validation
- Add chat_service and media_service
- Add comprehensive chat tests

Session 10 complete. Ready for Session 11: Premium subscriptions + Ad rewards"
```