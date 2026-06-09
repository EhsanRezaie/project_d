# dev.md — Iranian Dating App
> **Purpose:** This file is the single source of truth for the project.
> It is updated at the end of every session and passed to Claude at the start of the next one.
> Claude should read this fully before doing anything in a new session.

---

## Project Status
- **Session:** 1
- **Current Phase:** Database design (in progress)
- **Next Phase:** Finalize ERD → Project structure → Start coding

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
- **Developer:** Solo (project owner)
- **Backend expertise:** Senior — FastAPI & Django (FastAPI preferred)
- **Mobile:** Learning Flutter from scratch (beginner)
- **Daily availability:** 2–3 hours/day
- **Estimated MVP timeline:** 3–4 months (with Claude assistance)
- **Collaboration model:** Developer codes with Claude as a pair programmer every session

---

## Final Tech Stack

### Backend
| Tool | Role |
|------|------|
| FastAPI | Main framework — async-native, WebSocket support built-in |
| PostgreSQL + PostGIS | Primary database + geospatial queries for location-based matching |
| Redis | Realtime chat pub/sub + session store + online presence tracking |
| WebSocket (FastAPI native) | Realtime chat and notifications |
| Celery + Redis | Async task queue (e.g. match detection, push notifications) |
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
| Hetzner VPS | Primary hosting (affordable, payable from Iran) |
| ArvanCloud / Liara | Iranian cloud alternative if needed |

### Ads & Payments
| Tool | Role | Status |
|------|------|--------|
| AdMob | In-app ads every 10 min | ⚠️ Needs foreign account for payouts |
| Yektanet / MediaAd | Iranian ad network fallback | To be decided |
| ZarinPal / PayPing | Iranian payment gateway for subscriptions | To be integrated |
| Cafe Bazaar + Myket | Primary app distribution (replaces Play Store) | To be integrated |

---

## Key Decisions & Reasoning

### Authentication
- **Login method:** Email or Google OAuth (required)
- **Phone number:** Optional — used only for identity verification badge
- **No mandatory phone login** — reduces friction on signup
- **Verified badge:** Users who verify their phone number get a "Verified" badge on their profile
- **Reasoning:** Lower signup friction + still have a trust/verification mechanism

### User Profile Fields
- Name, age, gender (male/female), bio
- Height (cm) — optional
- Weight (kg) — optional
- Profile photos (multiple)
- Location (lat/lng — updated on app open)

### Matching Model
- Heterosexual only: males see females, females see males
- Swipe-based: like or pass
- Match created when both users like each other
- No algorithm complexity for MVP — recency + distance only

### Monetization
- All features free for all users
- Ad shown every 10 minutes (full-screen interstitial)
- Premium subscription = no ads
- Subscription managed via Iranian payment gateway (not Google Play Billing)

### Iranian Market Constraints
| Challenge | Status | Solution |
|-----------|--------|----------|
| AdMob payouts | ⚠️ Blocked for Iranian accounts | Use foreign partner account |
| Google Play Billing | ❌ Not available in Iran | Use ZarinPal/PayPing directly |
| Play Store publishing | ⚠️ Restricted | Publish on Cafe Bazaar + Myket |
| Server latency | ⚠️ Must be fast for Iranian users | Hetzner EU or ArvanCloud |

---

## Database Design (Session 1 Draft)

### Table: `users`
```sql
id               UUID PRIMARY KEY DEFAULT gen_random_uuid()
email            VARCHAR(255) UNIQUE NOT NULL
password_hash    VARCHAR(255)                        -- null if Google OAuth only
google_id        VARCHAR(255) UNIQUE                 -- null if email login
phone            VARCHAR(20)                         -- optional, for verification only
phone_verified   BOOLEAN DEFAULT FALSE
name             VARCHAR(100) NOT NULL
age              SMALLINT NOT NULL
gender           VARCHAR(10) NOT NULL                -- 'male' | 'female'
bio              TEXT
height           SMALLINT                            -- cm, optional
weight           SMALLINT                            -- kg, optional
lat              DOUBLE PRECISION                    -- updated on app open
lng              DOUBLE PRECISION                    -- updated on app open
is_premium       BOOLEAN DEFAULT FALSE
is_active        BOOLEAN DEFAULT TRUE
created_at       TIMESTAMPTZ DEFAULT NOW()
last_seen_at     TIMESTAMPTZ
```

### Table: `photos`
```sql
id        UUID PRIMARY KEY DEFAULT gen_random_uuid()
user_id   UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE
url       TEXT NOT NULL
order     SMALLINT NOT NULL DEFAULT 0
is_main   BOOLEAN DEFAULT FALSE
```

### Table: `swipes`
```sql
id          UUID PRIMARY KEY DEFAULT gen_random_uuid()
from_user   UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE
to_user     UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE
direction   VARCHAR(10) NOT NULL                    -- 'like' | 'pass'
created_at  TIMESTAMPTZ DEFAULT NOW()
UNIQUE (from_user, to_user)
```
> When both users swipe 'like' on each other → a `matches` record is created (via Celery task or DB trigger)

### Table: `matches`
```sql
id          UUID PRIMARY KEY DEFAULT gen_random_uuid()
user1_id    UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE
user2_id    UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE
is_active   BOOLEAN DEFAULT TRUE
matched_at  TIMESTAMPTZ DEFAULT NOW()
UNIQUE (user1_id, user2_id)
```

### Table: `messages`
```sql
id          UUID PRIMARY KEY DEFAULT gen_random_uuid()
match_id    UUID NOT NULL REFERENCES matches(id) ON DELETE CASCADE
sender_id   UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE
content     TEXT NOT NULL
is_read     BOOLEAN DEFAULT FALSE
sent_at     TIMESTAMPTZ DEFAULT NOW()
```

### Table: `subscriptions`
```sql
id          UUID PRIMARY KEY DEFAULT gen_random_uuid()
user_id     UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE
status      VARCHAR(20) NOT NULL                    -- 'active' | 'expired' | 'cancelled'
started_at  TIMESTAMPTZ NOT NULL
expires_at  TIMESTAMPTZ NOT NULL
```
> Kept separate so multiple plans can be added later without changing `users` table

### Table: `reports`
```sql
id           UUID PRIMARY KEY DEFAULT gen_random_uuid()
reporter_id  UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE
reported_id  UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE
reason       TEXT NOT NULL
created_at   TIMESTAMPTZ DEFAULT NOW()
```

### Open Questions (to decide next session)
- [ ] Do we need a separate `blocks` table, or handle it inside `reports`?
- [ ] Should `last_seen_at` be stored in Redis (for real-time online status) or only in Postgres?
- [ ] Do we add PostGIS `GEOGRAPHY` column now or add it in a later migration?

---

## API Endpoints Plan (not started yet)
> Will be designed next session

### Planned endpoint groups:
- `POST /auth/register`
- `POST /auth/login`
- `POST /auth/google`
- `GET/PUT /users/me`
- `POST /users/me/photos`
- `GET /discover` — returns candidate profiles based on location + filters
- `POST /swipes`
- `GET /matches`
- `WS /ws/chat/{match_id}` — WebSocket for realtime chat
- `GET/POST /messages/{match_id}`
- `POST /subscriptions`
- `POST /reports`

---

## Code Written So Far
> Nothing yet — Session 1 was planning and architecture only.

---

## Session Log

### Session 1 — [Date: TBD]
**Decisions made:**
- Chose FastAPI over Django for better async/WebSocket support
- Chose Flutter for cross-platform (Android + iOS)
- Defined monetization model (free + ads + premium)
- Defined auth model (email/Google + optional phone verification)
- Added height + weight fields to user profile
- Designed initial ERD (7 tables)
- Identified Iranian market constraints (AdMob payouts, Play Store, payment gateway)

**Next session goals:**
- [ ] Finalize ERD (blocks table decision, PostGIS strategy)
- [ ] Design project folder structure
- [ ] Define all API endpoints
- [ ] Start writing code: project setup + models + auth
