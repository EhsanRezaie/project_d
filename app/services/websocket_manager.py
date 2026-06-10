import json
from typing import Dict, Set, Optional
from uuid import UUID
from fastapi import WebSocket, WebSocketDisconnect
from app.core.logging import get_logger
from app.core.redis import redis_client

logger = get_logger("websocket")

class WebSocketManager:
    """
    Manage WebSocket connections for real-time notifications and chat.
    """
    
    def __init__(self):
        self.active_connections: Dict[str, Set[WebSocket]] = {}  # user_id -> set of websockets
        self.chat_connections: Dict[str, Set[WebSocket]] = {}    # "chat:{match_id}:{user_id}" -> websockets
        self._pubsub = None
    
    async def _get_pubsub(self):
        """Lazy initialize pubsub"""
        if self._pubsub is None:
            self._pubsub = redis_client.pubsub()
            await self._pubsub.subscribe()
        return self._pubsub
    
    # ==================== Match Notification Methods ====================
    
    async def connect(self, websocket: WebSocket, user_id: str):
        """Accept WebSocket connection and store it for match notifications"""
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
    
    # ==================== Chat Methods ====================
    
    async def add_chat_connection(self, match_id: str, user_id: str, websocket: WebSocket):
        """Add a chat WebSocket connection"""
        await websocket.accept()
        
        key = f"chat:{match_id}:{user_id}"
        if key not in self.chat_connections:
            self.chat_connections[key] = set()
        self.chat_connections[key].add(websocket)
        
        logger.info(f"Chat WebSocket connected for match {match_id}, user {user_id}")
    
    async def remove_chat_connection(self, match_id: str, user_id: str, websocket: WebSocket):
        """Remove a chat WebSocket connection"""
        key = f"chat:{match_id}:{user_id}"
        if key in self.chat_connections:
            self.chat_connections[key].discard(websocket)
            if not self.chat_connections[key]:
                del self.chat_connections[key]
        
        logger.info(f"Chat WebSocket disconnected for match {match_id}, user {user_id}")
    
    async def send_to_match(self, match_id: str, sender_id: str, message: dict, other_user_id: str = None):
        """
        Send message to both users in a match.
        For matched chats, we need to know both user IDs.
        For unmatched chats, we need the other user's ID.
        """
        data = json.dumps(message)
        
        # Send to the other user
        if other_user_id:
            other_key = f"chat:{match_id}:{other_user_id}"
            if other_key in self.chat_connections:
                for ws in self.chat_connections[other_key]:
                    try:
                        await ws.send_text(data)
                    except Exception as e:
                        logger.error(f"Failed to send to {other_key}: {e}")
        
        # Also send back to sender (for confirmation)
        sender_key = f"chat:{match_id}:{sender_id}"
        if sender_key in self.chat_connections:
            for ws in self.chat_connections[sender_key]:
                try:
                    await ws.send_text(data)
                except Exception as e:
                    logger.error(f"Failed to send to {sender_key}: {e}")


# Create singleton instance
websocket_manager = WebSocketManager()