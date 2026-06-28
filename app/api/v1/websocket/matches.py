from fastapi import WebSocket, WebSocketDisconnect, APIRouter
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import get_session
from app.core.deps import get_current_user_ws
from app.services.websocket_manager import websocket_manager
from app.core.logging import get_logger

logger = get_logger("websocket")

router = APIRouter()


@router.websocket("/ws/matches")
async def websocket_matches(
    websocket: WebSocket,
    token: str,
):
    """
    WebSocket endpoint for real-time match notifications.
    Connect with: ws://localhost:8000/ws/matches?token={access_token}
    """
    
    # Authenticate user
    user_id = await get_current_user_ws(token)
    if not user_id:
        await websocket.close(code=4001, reason="Invalid token")
        return
    
    # Accept connection and add to manager
    await websocket_manager.connect(websocket, str(user_id))
    
    try:
        # Keep connection alive and listen for messages
        while True:
            # Wait for any message from client (ping/pong)
            data = await websocket.receive_text()
            
            # Handle ping/pong
            if data == "ping":
                await websocket.send_text("pong")
            else:
                # Log other messages but don't process
                logger.debug("Received message", user_id=user_id, data=data)
                
    except WebSocketDisconnect:
        await websocket_manager.disconnect(websocket, str(user_id))
        logger.info("WebSocket disconnected", user_id=user_id)
    except Exception as e:
        logger.error("WebSocket error", user_id=user_id, error=str(e))
        await websocket_manager.disconnect(websocket, str(user_id))