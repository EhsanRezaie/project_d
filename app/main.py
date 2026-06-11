from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
import os

from app.core.config import settings
from app.core.limiter import limiter
from app.api.v1.endpoints.auth import router as auth_router
from app.api.v1.endpoints.users import router as users_router
from app.api.v1.endpoints.photos import router as photos_router  
from app.api.v1.endpoints.admin import router as admin_router
from app.api.v1.endpoints.discover import router as discover_router
from app.api.v1.endpoints.swipes import router as swipes_router  
from app.api.v1.endpoints.search import router as search_router
from app.api.v1.endpoints.blocks import router as blocks_router
from app.api.v1.endpoints.rewards import router as rewards_router
from app.api.v1.endpoints.referrals import router as referrals_router
from app.api.v1.endpoints.subscriptions import router as subscription_router
from app.api.v1.endpoints.notifications import router as notifications_router
from app.api.v1.endpoints.reports import router as reports_router
from app.api.v1.endpoints.privacy import router as privacy_router

from app.api.v1.websocket.matches import router as websocket_router
from app.api.v1.endpoints.matches import router as matches_router
from app.api.v1.endpoints.messages import router as messages_router
from app.api.v1.websocket.chat import router as chat_websocket_router


from app.core.logging import setup_logging
setup_logging()


app = FastAPI(
    title=settings.APP_NAME,
    debug=settings.DEBUG,
)

# Rate limiter
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Serve uploaded files
uploads_dir = "uploads"
if not os.path.exists(uploads_dir):
    os.makedirs(uploads_dir)
app.mount("/uploads", StaticFiles(directory=uploads_dir), name="uploads")

# Routers
app.include_router(auth_router, prefix="/api/v1")
app.include_router(users_router, prefix="/api/v1")
app.include_router(photos_router, prefix="/api/v1")  
app.include_router(admin_router, prefix="/api/v1")
app.include_router(discover_router, prefix="/api/v1")
app.include_router(swipes_router, prefix="/api/v1")  
app.include_router(search_router, prefix="/api/v1")
app.include_router(blocks_router, prefix="/api/v1")
app.include_router(matches_router, prefix="/api/v1")
app.include_router(messages_router, prefix="/api/v1")
app.include_router(rewards_router, prefix="/api/v1")
app.include_router(referrals_router, prefix="/api/v1")
app.include_router(subscription_router, prefix="/api/v1")
app.router.include_router(notifications_router,prefix="/api/v1")
app.router.include_router(reports_router,prefix="/api/v1")
app.router.include_router(privacy_router,prefix="/api/v1")


# WebSocket Router
app.include_router(websocket_router)
app.include_router(chat_websocket_router)


@app.get("/health")
async def health():
    return {"status": "ok"}