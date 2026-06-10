import json
from typing import Dict, Set, Optional
from uuid import UUID
from fastapi import WebSocket, WebSocketDisconnect
from app.core.logging import get_logger
from app.core.redis import redis_client

logger = get_logger("websocket")

class WebSocketManager:
    """
    Manage WebSocket connections for real-time notifications.
    Uses Redis pub/sub for multi-worker support.
    """
    
    def __init__(self):
        self.active_connections: Dict[str, Set[WebSocket]] = {}
        self._pubsub = None
    
    async def _get_pubsub(self):
        """Lazy initialize pubsub"""
        if self._pubsub is None:
            self._pubsub = redis_client.pubsub()
            await self._pubsub.subscribe()
        return self._pubsub
    
    async def connect(self, websocket: WebSocket, user_id: str):
        """Accept WebSocket connection and store it"""
        await websocket.accept()
        
        if user_id not in self.active_connections:
            self.active_connections[user_id] = set()
        self.active_connections[user_id].add(websocket)
        
        logger.info(f"WebSocket connected for user {user_id}")
    
    async def disconnect(self, websocket: WebSocket, user_id: str):
        """Remove WebSocket connection"""
        if user_id in self.active_connections:
            self.active_connections[user_id].discard(websocket)
            if not self.active_connections[user_id]:
                del self.active_connections[user_id]
        
        logger.info(f"WebSocket disconnected for user {user_id}")
    
    async def send_personal_message(self, user_id: str, message: dict):
        """Send message to a specific user via all their active connections"""
        if user_id not in self.active_connections:
            logger.debug(f"No active connection for user {user_id}")
            return
        
        data = json.dumps(message)
        disconnected = []
        
        for websocket in self.active_connections[user_id]:
            try:
                await websocket.send_text(data)
            except Exception as e:
                logger.error(f"Failed to send message to user {user_id}: {e}")
                disconnected.append(websocket)
        
        # Clean up disconnected sockets
        for ws in disconnected:
            await self.disconnect(ws, user_id)
    
    async def broadcast_match(self, user1_id: str, user2_id: str, match_id: str, user1_data: dict, user2_data: dict):
        """Broadcast match notification to both users"""
        message1 = {
            "type": "new_match",
            "data": {
                "match_id": match_id,
                "user": user2_data
            }
        }
        
        message2 = {
            "type": "new_match",
            "data": {
                "match_id": match_id,
                "user": user1_data
            }
        }
        
        await self.send_personal_message(user1_id, message1)
        await self.send_personal_message(user2_id, message2)
        
        logger.info(f"Match broadcast sent for match {match_id}")


# Singleton instance
websocket_manager = WebSocketManager()