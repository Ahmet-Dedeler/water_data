from typing import List, Dict, Set
from fastapi import WebSocket

class WebSocketManager:
    def __init__(self):
        # Maps a user_id to a list of their active WebSockets
        self.active_connections: Dict[int, List[WebSocket]] = {}
        # Maps a channel name to a set of user_ids subscribed to it
        self.subscriptions: Dict[str, Set[int]] = {}

    async def connect(self, websocket: WebSocket, user_id: int):
        await websocket.accept()
        if user_id not in self.active_connections:
            self.active_connections[user_id] = []
        self.active_connections[user_id].append(websocket)
        print(f"User {user_id} connected. Total connections for user: {len(self.active_connections[user_id])}")

    def disconnect(self, websocket: WebSocket, user_id: int):
        if user_id in self.active_connections:
            self.active_connections[user_id].remove(websocket)
            if not self.active_connections[user_id]:
                # If no more connections for this user, remove them from all subscriptions
                del self.active_connections[user_id]
                for channel in self.subscriptions:
                    if user_id in self.subscriptions[channel]:
                        self.subscriptions[channel].remove(user_id)
            print(f"User {user_id} disconnected.")

    def subscribe(self, user_id: int, channel: str) -> bool:
        if user_id not in self.active_connections:
            return False # Cannot subscribe if not connected
        
        if channel not in self.subscriptions:
            self.subscriptions[channel] = set()
        self.subscriptions[channel].add(user_id)
        print(f"User {user_id} subscribed to channel {channel}")
        return True

    def unsubscribe(self, user_id: int, channel: str):
        if channel in self.subscriptions and user_id in self.subscriptions[channel]:
            self.subscriptions[channel].remove(user_id)
            print(f"User {user_id} unsubscribed from channel {channel}")

    async def send_personal_message(self, message: str, user_id: int):
        if user_id in self.active_connections:
            for websocket in self.active_connections[user_id]:
                await websocket.send_text(message)

    async def broadcast(self, message: str):
        for user_id in self.active_connections:
            for websocket in self.active_connections[user_id]:
                await websocket.send_text(message)

    async def broadcast_to_channel(self, message: str, channel: str):
        if channel in self.subscriptions:
            user_ids_in_channel = self.subscriptions[channel]
            for user_id in user_ids_in_channel:
                if user_id in self.active_connections:
                    for websocket in self.active_connections[user_id]:
                        await websocket.send_text(message)

# Create a single instance of the manager to be used across the application
manager = WebSocketManager() 