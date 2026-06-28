# Backend Scale & Production Hardening Plan
## Iranian Dating App

> Phases 1–4 of performance_plan.md are complete (indexes, caching, query optimization).
> This document covers what comes next: production hardening, scale, and missing features
> needed before real users hit the app.
>
> Work top to bottom. Each section is a separate session.

---

## Where You Stand

| Area | Status |
|------|--------|
| DB indexes (37 across 10 tables) | ✅ Done |
| Redis caching (static + user + daily limits) | ✅ Done |
| Haversine in PostgreSQL | ✅ Done |
| Eager loading / N+1 eliminated | ✅ Done |
| Cursor pagination for chat | ✅ Done |
| BackgroundTasks for notifications | ✅ Done |
| GZip middleware | ✅ Done |
| 511 tests passing | ✅ Done |
| FCM push notifications | ❌ Missing |
| Real ZarinPal payment | ❌ Missing |
| Email sending (verification, reset) | ❌ Missing |
| Connection pooling (PgBouncer) | ❌ Missing |
| Rate limiting per endpoint | ❌ Missing / incomplete |
| WebSocket scale (multi-process) | ❌ Missing |
| Structured logging + error tracking | ❌ Missing |
| Health checks for Docker | ❌ Missing |
| Nginx reverse proxy | ❌ Missing |
| HTTPS / SSL | ❌ Missing |
| Discover card stack pre-caching | ❌ Missing |
| Swipe deduplication (Redis set) | ❌ Missing |
| Photo moderation pipeline | ❌ Partial |

---

## Section 1 — Connection Pooling (PgBouncer)

### The problem
FastAPI runs multiple async workers. Each worker holds open SQLAlchemy connection pool
slots. Without a connection pooler, under load (100+ concurrent users) you'll hit
PostgreSQL's `max_connections` (default: 100) and start getting:

```
asyncpg.exceptions.TooManyConnectionsError: sorry, too many clients already
```

### The fix: PgBouncer in front of PostgreSQL

Add to `docker-compose.yml`:

```yaml
pgbouncer:
  image: edoburu/pgbouncer:latest
  container_name: dating_pgbouncer
  environment:
    DATABASE_URL: "postgres://dating_user:dating_pass@db:5432/dating_db"
    POOL_MODE: transaction          # best for async FastAPI
    MAX_CLIENT_CONN: 1000           # connections from FastAPI workers
    DEFAULT_POOL_SIZE: 20           # actual connections to PostgreSQL
    MIN_POOL_SIZE: 5
    RESERVE_POOL_SIZE: 5
    SERVER_RESET_QUERY: DISCARD ALL
  ports:
    - "5432:5432"                   # FastAPI connects here instead of db:5432
  depends_on:
    - db
```

Update `.env`:
```env
# FastAPI now connects to PgBouncer, not PostgreSQL directly
DATABASE_URL=postgresql+asyncpg://dating_user:dating_pass@pgbouncer:5432/dating_db
```

Update SQLAlchemy engine in `app/database.py` — disable statement cache
(incompatible with PgBouncer transaction mode):

```python
engine = create_async_engine(
    settings.DATABASE_URL,
    pool_size=5,           # per-worker pool (small — PgBouncer handles the real pooling)
    max_overflow=10,
    pool_pre_ping=True,    # detect dead connections
    connect_args={
        "prepared_statement_cache_size": 0,   # REQUIRED for PgBouncer transaction mode
        "statement_cache_size": 0,
    }
)
```

**Impact:** Supports 1000+ concurrent connections to FastAPI while keeping ≤20 real
PostgreSQL connections. Essential before any real traffic.

---

## Section 2 — Rate Limiting (Complete the job)

### Current state
`app/core/limiter.py` exists but the coverage is likely partial.

### What needs rate limits and at what level

| Endpoint | Limit | Reason |
|----------|-------|--------|
| `POST /auth/register/init` | 5/hour per IP | Prevent SMS/email bombing |
| `POST /auth/register/verify` | 10/hour per IP | Prevent code brute-force |
| `POST /auth/login` | 10/min per IP | Prevent password brute-force |
| `POST /auth/password-reset` | 3/hour per IP | Prevent reset bombing |
| `GET /discover` | 60/min per user | Prevent scraping |
| `GET /search` | 30/min per user | Prevent scraping |
| `POST /swipes` | 200/min per user | Supplement daily limit |
| `POST /reports/{user_id}` | 10/hour per user | Prevent report abuse |
| `GET /system/status` | 60/min per IP | Already done — verify |

### Implementation with `slowapi` (already in your stack via `limiter.py`)

```python
# app/core/limiter.py
from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(
    key_func=get_remote_address,
    default_limits=["1000/minute"],   # global fallback
    storage_uri=settings.REDIS_URL,   # store counts in Redis (shared across workers)
)
```

```python
# Example: auth.py
@router.post("/register/init")
@limiter.limit("5/hour")
async def register_init(request: Request, ...):
    ...

# For per-user limits (authenticated endpoints):
def get_user_key(request: Request):
    return str(request.state.user_id)   # set in middleware

@router.post("/swipes")
@limiter.limit("200/minute", key_func=get_user_key)
async def create_swipe(request: Request, ...):
    ...
```

**Critical:** Rate limit storage must be Redis, not in-memory — otherwise limits
reset when the process restarts and don't work across multiple workers.

---

## Section 3 — WebSocket Scale (Multi-Process Problem)

### The problem
Your `websocket_manager.py` stores active connections in a Python dict:

```python
class WebSocketManager:
    def __init__(self):
        self.connections: dict[UUID, WebSocket] = {}
```

This works fine with one worker. The moment you run 2+ Uvicorn workers (which you
will need for any real load), user A might connect to worker 1 and user B to worker 2.
When A sends B a message, worker 1 has no reference to B's connection on worker 2.
Messages silently fail to deliver.

### The fix: Redis Pub/Sub as the message bus

```python
# app/services/websocket_manager.py — rewrite

import json
from uuid import UUID
from redis.asyncio import Redis
from fastapi import WebSocket

class WebSocketManager:
    def __init__(self):
        self.local_connections: dict[str, WebSocket] = {}  # only THIS worker's connections

    async def connect(self, user_id: UUID, websocket: WebSocket, redis: Redis):
        await websocket.accept()
        self.local_connections[str(user_id)] = websocket
        # Subscribe to this user's channel
        pubsub = redis.pubsub()
        await pubsub.subscribe(f"ws:user:{user_id}")
        # Start listening for messages from other workers
        asyncio.create_task(self._listen(user_id, pubsub))

    async def disconnect(self, user_id: UUID):
        self.local_connections.pop(str(user_id), None)

    async def send_to_user(self, user_id: UUID, message: dict, redis: Redis):
        """
        Publishes to Redis. Whichever worker holds the connection will deliver it.
        Works across multiple Uvicorn workers.
        """
        await redis.publish(
            f"ws:user:{user_id}",
            json.dumps(message)
        )

    async def _listen(self, user_id: UUID, pubsub):
        """Receive from Redis and forward to the local WebSocket connection."""
        async for msg in pubsub.listen():
            if msg["type"] == "message":
                ws = self.local_connections.get(str(user_id))
                if ws:
                    await ws.send_json(json.loads(msg["data"]))

manager = WebSocketManager()
```

**Impact:** Now you can run `uvicorn app.main:app --workers 4` and WebSocket delivery
works correctly across all workers. This is a hard requirement before going to production.

---

## Section 4 — Discover Card Stack Pre-Caching

### The problem
`GET /discover` runs an expensive query on every swipe batch request:
- JOIN user_profiles
- Haversine distance filter (now in DB — good)
- Subquery to exclude swiped users (grows with swipe history)
- Subquery to exclude blocked users

As swipe history grows per user, the exclusion subquery gets slower.

### The fix: Pre-compute and cache a card stack per user

```python
# app/core/cache.py — add these

DISCOVER_STACK_TTL = 1800   # 30 minutes
DISCOVER_STACK_SIZE = 50    # pre-fetch 50 cards at a time

def key_discover_stack(user_id: UUID) -> str:
    return f"cache:discover:{user_id}:stack"

async def get_discover_stack(redis: Redis, user_id: UUID) -> list[str] | None:
    """Returns list of pre-fetched user IDs, or None if cache miss."""
    raw = await redis.get(key_discover_stack(user_id))
    return json.loads(raw) if raw else None

async def set_discover_stack(redis: Redis, user_id: UUID, user_ids: list[str]):
    await redis.setex(
        key_discover_stack(user_id),
        DISCOVER_STACK_TTL,
        json.dumps(user_ids)
    )

async def pop_from_discover_stack(redis: Redis, user_id: UUID, count: int) -> list[str]:
    """
    Pop `count` IDs from the cached stack.
    Returns empty list if stack is empty (trigger refetch).
    """
    key = key_discover_stack(user_id)
    pipe = redis.pipeline()
    pipe.lrange(key, 0, count - 1)
    pipe.ltrim(key, count, -1)
    results = await pipe.execute()
    return results[0]
```

```python
# endpoints/discover.py — updated flow

@router.get("/discover")
async def discover(limit: int = Query(20, le=50), ...):
    # 1. Try cache first
    stack = await pop_from_discover_stack(redis, current_user.id, limit)

    if not stack:
        # 2. Cache miss — run the full query for 50 users
        user_ids = await _run_discover_query(current_user, filters, limit=50, db=db)
        if len(user_ids) > limit:
            # Cache the overflow for next requests
            await set_discover_stack(redis, current_user.id, user_ids[limit:])
        stack = user_ids[:limit]

    # 3. Fetch full profiles for the IDs in the stack
    users = await _fetch_profiles_by_ids(stack, db)
    return users
```

**Invalidate stack when:** user updates location, user changes discover filters.

**Impact:** After the first discover load, subsequent loads serve from Redis.
The expensive exclusion query only runs once per 30 minutes per user.

---

## Section 5 — Swipe Deduplication (Redis Set)

### The problem
The discover query excludes swiped users via a DB subquery:
```sql
WHERE u.id NOT IN (SELECT swipee_id FROM swipes WHERE swiper_id = :user_id)
```

A power user who swipes 500 people/day generates a subquery scanning 500+ rows
on every discover load. At 10,000 total swipes, this is noticeably slow even with
the index.

### The fix: Mirror swipe history in a Redis Set

```python
# After every swipe, add to Redis set:
# Key: swiped:{user_id}
# Value: Set of swipee_ids
# TTL: 7 days (rolling window — most discover exclusions are recent anyway)

async def record_swipe_cache(redis: Redis, swiper_id: UUID, swipee_id: UUID):
    key = f"swiped:{swiper_id}"
    await redis.sadd(key, str(swipee_id))
    await redis.expire(key, 7 * 86400)   # 7 days TTL

async def get_swiped_ids(redis: Redis, user_id: UUID) -> set[str]:
    members = await redis.smembers(f"swiped:{user_id}")
    return {m.decode() for m in members}
```

In `discover.py`, replace the DB subquery with a Redis set lookup:

```python
swiped_ids = await get_swiped_ids(redis, current_user.id)
# Pass swiped_ids as exclusion list to the query
stmt = stmt.where(User.id.not_in(swiped_ids))
```

**Note:** Redis sets work fine up to ~10,000 members per key with negligible memory.
At 10,000 swipes × 16 bytes per UUID = 160KB per user. Acceptable.

---

## Section 6 — Nginx + SSL (Required Before Production)

### docker-compose.yml addition

```yaml
nginx:
  image: nginx:alpine
  container_name: dating_nginx
  ports:
    - "80:80"
    - "443:443"
  volumes:
    - ./nginx/nginx.conf:/etc/nginx/nginx.conf:ro
    - ./nginx/ssl:/etc/nginx/ssl:ro     # your SSL certs
    - ./nginx/certbot:/var/www/certbot  # for Let's Encrypt
  depends_on:
    - api
```

### `nginx/nginx.conf`

```nginx
upstream api {
    server api:8000;
    keepalive 32;
}

server {
    listen 80;
    server_name api.yourapp.ir;
    return 301 https://$host$request_uri;
}

server {
    listen 443 ssl http2;
    server_name api.yourapp.ir;

    ssl_certificate     /etc/nginx/ssl/fullchain.pem;
    ssl_certificate_key /etc/nginx/ssl/privkey.pem;
    ssl_protocols       TLSv1.2 TLSv1.3;
    ssl_ciphers         HIGH:!aNULL:!MD5;
    ssl_session_cache   shared:SSL:10m;

    # Security headers
    add_header X-Content-Type-Options nosniff;
    add_header X-Frame-Options DENY;
    add_header X-XSS-Protection "1; mode=block";
    add_header Strict-Transport-Security "max-age=31536000" always;

    # File upload size (photos)
    client_max_body_size 12M;

    # API
    location /api/ {
        proxy_pass http://api;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header Connection "";    # keepalive to upstream
        proxy_read_timeout 60s;
    }

    # WebSocket — requires Upgrade header
    location /api/v1/ws/ {
        proxy_pass http://api;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_read_timeout 3600s;     # WebSocket stays open
        proxy_send_timeout 3600s;
    }
}
```

### Get SSL Certificate (Let's Encrypt — free)

```bash
sudo apt install certbot
sudo certbot certonly --standalone -d api.yourapp.ir
# Certs saved to /etc/letsencrypt/live/api.yourapp.ir/
# Auto-renewal: certbot renew runs in cron
```

---

## Section 7 — Structured Logging + Error Tracking

### Current state
`app/core/logging.py` exists — likely basic Python logging.

### What's missing: structured JSON logs + Sentry

**Structured logging** (grep-able, parseable):

```python
# app/core/logging.py — replace with structlog

import structlog

structlog.configure(
    processors=[
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.JSONRenderer(),   # → each log line is valid JSON
    ],
    context_class=dict,
    logger_factory=structlog.stdlib.LoggerFactory(),
)

log = structlog.get_logger()
```

Usage anywhere in the app:
```python
log.info("swipe_recorded", swiper=str(user_id), swipee=str(swipee_id), type="like")
log.error("payment_failed", user=str(user_id), plan="monthly", error=str(e))
```

**Sentry for error tracking** (free tier: 5,000 errors/month):

```python
# app/main.py
import sentry_sdk
from sentry_sdk.integrations.fastapi import FastApiIntegration
from sentry_sdk.integrations.sqlalchemy import SqlalchemyIntegration

sentry_sdk.init(
    dsn=settings.SENTRY_DSN,   # add to .env
    integrations=[
        FastApiIntegration(transaction_style="endpoint"),
        SqlalchemyIntegration(),
    ],
    traces_sample_rate=0.1,    # 10% of requests traced (performance)
    environment=settings.ENVIRONMENT,
)
```

```bash
pip install sentry-sdk[fastapi]
```

**Add to `.env`:**
```env
SENTRY_DSN=https://xxx@yyy.ingest.sentry.io/zzz
```

Without this, when something breaks in production you have no visibility.

---

## Section 8 — Docker Health Checks + Multi-Worker Production Config

### Health checks for all services in `docker-compose.yml`

```yaml
services:
  api:
    build: .
    command: >
      uvicorn app.main:app
      --host 0.0.0.0
      --port 8000
      --workers 4               # 4 workers for a 2-core VPS
      --worker-class uvicorn.workers.UvicornWorker
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/api/v1/auth/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 40s
    restart: unless-stopped
    depends_on:
      db:
        condition: service_healthy
      redis:
        condition: service_healthy

  db:
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U dating_user -d dating_db"]
      interval: 10s
      timeout: 5s
      retries: 5

  redis:
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 10s
      timeout: 5s
      retries: 5

  minio:
    healthcheck:
      test: ["CMD", "mc", "ready", "local"]
      interval: 10s
      timeout: 5s
      retries: 5
```

### Workers calculation
- 1-core VPS: `--workers 2`
- 2-core VPS: `--workers 4`
- 4-core VPS: `--workers 8`
- Formula: `(2 × CPU cores) + 1`

**Note:** With multiple workers, WebSocket fix from Section 3 (Redis Pub/Sub) is
mandatory — otherwise WebSocket delivery breaks.

---

## Section 9 — FCM Push Notifications

Already planned in Session 15. This is what to build:

### New files needed

**`app/models/device_token.py`**
```python
class DeviceToken(Base):
    __tablename__ = "device_tokens"
    id = Column(UUID, primary_key=True, default=uuid4)
    user_id = Column(UUID, ForeignKey("users.id"), nullable=False)
    token = Column(String, nullable=False)
    platform = Column(String(10))   # "android" or "ios"
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    __table_args__ = (
        UniqueConstraint("user_id", "token"),
        Index("idx_device_tokens_user", "user_id"),
    )
```

**`app/services/push_service.py`**
```python
import firebase_admin
from firebase_admin import credentials, messaging

class PushService:
    def __init__(self):
        cred = credentials.Certificate(settings.FCM_SERVICE_ACCOUNT_PATH)
        firebase_admin.initialize_app(cred)

    async def send_to_user(self, user_id: UUID, title: str, body: str, data: dict, db: AsyncSession):
        tokens = await self._get_user_tokens(user_id, db)
        if not tokens:
            return

        message = messaging.MulticastMessage(
            tokens=tokens,
            notification=messaging.Notification(title=title, body=body),
            data={k: str(v) for k, v in data.items()},
            android=messaging.AndroidConfig(priority="high"),
            apns=messaging.APNSConfig(
                payload=messaging.APNSPayload(
                    aps=messaging.Aps(sound="default")
                )
            )
        )
        response = messaging.send_each_for_multicast(message)
        # Handle failed tokens (remove invalid ones from DB)
        await self._cleanup_failed_tokens(tokens, response, db)
```

**New endpoint:** `POST /api/v1/notifications/device-token`
```python
@router.post("/device-token", status_code=204)
async def register_device_token(
    payload: DeviceTokenRequest,
    current_user_id: UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    await upsert_device_token(current_user_id, payload.token, payload.platform, db)
```

**Integrate into notification_service.py:**
```python
# After creating DB notification, fire push in background:
background_tasks.add_task(
    push_service.send_to_user,
    user_id=target_user_id,
    title=push_title,
    body=push_body,
    data={"type": "match", "match_id": str(match_id)},
    db=db
)
```

**Add to `.env`:**
```env
FCM_SERVICE_ACCOUNT_PATH=/app/firebase-service-account.json
```

---

## Section 10 — ZarinPal Real Payment

### The flow (replace mock)

```python
# app/services/payment_service.py

import httpx

ZARINPAL_REQUEST_URL = "https://api.zarinpal.com/pg/v4/payment/request.json"
ZARINPAL_VERIFY_URL  = "https://api.zarinpal.com/pg/v4/payment/verify.json"
ZARINPAL_START_URL   = "https://www.zarinpal.com/pg/StartPay/{authority}"

class ZarinpalService:
    async def create_payment(self, amount_toman: int, description: str, callback_url: str) -> dict:
        async with httpx.AsyncClient() as client:
            response = await client.post(ZARINPAL_REQUEST_URL, json={
                "merchant_id": settings.ZARINPAL_MERCHANT_ID,
                "amount": amount_toman * 10,   # ZarinPal uses Rials
                "description": description,
                "callback_url": callback_url,
            })
        data = response.json()
        if data["data"]["code"] != 100:
            raise PaymentError(f"ZarinPal error: {data['errors']}")
        authority = data["data"]["authority"]
        return {
            "authority": authority,
            "payment_url": ZARINPAL_START_URL.format(authority=authority),
        }

    async def verify_payment(self, authority: str, amount_toman: int) -> str:
        """Returns ref_id on success, raises on failure."""
        async with httpx.AsyncClient() as client:
            response = await client.post(ZARINPAL_VERIFY_URL, json={
                "merchant_id": settings.ZARINPAL_MERCHANT_ID,
                "amount": amount_toman * 10,
                "authority": authority,
            })
        data = response.json()
        code = data["data"]["code"]
        if code not in (100, 101):   # 101 = already verified
            raise PaymentError(f"Verification failed: {data['errors']}")
        return str(data["data"]["ref_id"])
```

**Flow in `subscriptions.py`:**
```
POST /subscriptions/purchase → create_payment() → return {payment_url}
GET  /subscriptions/verify?Authority=xxx&Status=OK → verify_payment() → activate premium
```

---

## Implementation Order

Work through these in order. Each is one session.

### Session A — Connection Pooling + Rate Limiting
- [ ] Add PgBouncer to `docker-compose.yml` (Section 1)
- [ ] Update SQLAlchemy engine with `prepared_statement_cache_size=0` (Section 1)
- [ ] Audit `limiter.py` — confirm Redis storage, not in-memory (Section 2)
- [ ] Add rate limits to all auth endpoints (Section 2)
- [ ] Add rate limits to discover/search (Section 2)

### Session B — WebSocket Scale + Discover Cache
- [ ] Rewrite `websocket_manager.py` to use Redis Pub/Sub (Section 3)
- [ ] Add discover card stack pre-caching (Section 4)
- [ ] Add swipe deduplication Redis Set (Section 5)
- [ ] Test with multiple Uvicorn workers: `--workers 4`

### Session C — Nginx + SSL + Docker Production Config
- [ ] Write `nginx/nginx.conf` with SSL, security headers, WebSocket proxy (Section 6)
- [ ] Get SSL cert via Let's Encrypt (Section 6)
- [ ] Add health checks to all services in `docker-compose.yml` (Section 8)
- [ ] Set `--workers 4` in production compose command (Section 8)

### Session D — Observability
- [ ] Replace logging with `structlog` JSON output (Section 7)
- [ ] Add Sentry SDK to `main.py` (Section 7)
- [ ] Add `SENTRY_DSN` to `.env` (Section 7)
- [ ] Verify errors appear in Sentry dashboard

### Session E — FCM Push Notifications (was Session 15)
- [ ] Create `DeviceToken` model + migration (Section 9)
- [ ] Build `push_service.py` (Section 9)
- [ ] Add `POST /notifications/device-token` endpoint (Section 9)
- [ ] Wire into `notification_service.py` via BackgroundTasks (Section 9)
- [ ] Test on Android emulator

### Session F — Real ZarinPal Payment (was Session 15)
- [ ] Build `payment_service.py` (Section 10)
- [ ] Replace mock in `subscriptions.py` with real ZarinPal flow (Section 10)
- [ ] Add callback endpoint `GET /subscriptions/verify` (Section 10)
- [ ] Test in ZarinPal sandbox

---

## Priority Order (if you can only do some of these)

| Priority | Item | Why |
|----------|------|-----|
| 🔴 Must before launch | Nginx + SSL (Section 6) | HTTPS required for Play Store |
| 🔴 Must before launch | Docker health checks + workers (Section 8) | Crashes won't recover without restart policy |
| 🔴 Must before launch | FCM push notifications (Section 9) | Dating apps are useless without match/message alerts |
| 🔴 Must before launch | Real ZarinPal (Section 10) | Can't monetize without it |
| 🟡 Do before scaling | PgBouncer (Section 1) | Needed at 100+ concurrent users |
| 🟡 Do before scaling | Rate limiting audit (Section 2) | Needed before public exposure |
| 🟡 Do before scaling | WebSocket Redis Pub/Sub (Section 3) | Needed with multiple workers |
| 🟢 Nice to have | Sentry + structlog (Section 7) | Visibility into production issues |
| 🟢 Nice to have | Discover card stack cache (Section 4) | UX improvement at scale |
| 🟢 Nice to have | Swipe Redis set (Section 5) | Needed at 10,000+ swipes per user |
