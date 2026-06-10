from fastapi import WebSocket, WebSocketDisconnect, APIRouter, Query
from app.services.websocket_manager import websocket_manager
from app.core.security import decode_access_token
from app.core.logging import get_logger

logger = get_logger("websocket")

router = APIRouter()


@router.websocket("/ws/chat/{match_id}")
async def websocket_chat(
    websocket: WebSocket,
    match_id: str,
    token: str = Query(...),
):
    """
    WebSocket endpoint for real-time chat.
    Connect with: ws://localhost:8000/ws/chat/{match_id}?token={access_token}
    """

    # Authenticate user
    user_id = decode_access_token(token)
    if not user_id:
        await websocket.close(code=4001, reason="Invalid token")
        return

    # Convert to string
    user_id_str = str(user_id)

    # Accept connection and add to manager
    await websocket_manager.add_chat_connection(match_id, user_id_str, websocket)

    try:
        while True:
            data = await websocket.receive_text()

            # Parse message
            import json
            try:
                message = json.loads(data)
            except:
                await websocket.send_text(json.dumps({"type": "error", "message": "Invalid JSON"}))
                continue

            msg_type = message.get("type")

            if msg_type == "ping":
                await websocket.send_text(json.dumps({"type": "pong"}))

            elif msg_type == "typing":
                # Broadcast typing indicator to other user
                # For now, just log - we need to know other user ID
                logger.debug(f"User {user_id_str} typing in chat {match_id}")

            elif msg_type == "delivery_ack":
                logger.debug(f"Delivery ack for messages: {message.get('message_ids')}")

            elif msg_type == "read_ack":
                logger.debug(f"Read ack for messages: {message.get('message_ids')}")

    except WebSocketDisconnect:
        await websocket_manager.remove_chat_connection(match_id, user_id_str, websocket)
        logger.info(f"Chat WebSocket disconnected for user {user_id_str}, match {match_id}")
    except Exception as e:
        logger.error(f"Chat WebSocket error: {e}")
        await websocket_manager.remove_chat_connection(match_id, user_id_str, websocket)