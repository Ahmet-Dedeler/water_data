from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field
import enum

# --- Enums for WebSocket Communication ---

class WebSocketMessageType(str, enum.Enum):
    # Client to Server
    AUTHENTICATE = "authenticate"
    SUBSCRIBE = "subscribe"
    UNSUBSCRIBE = "unsubscribe"
    SEND_MESSAGE = "send_message"
    
    # Server to Client
    SYSTEM_MESSAGE = "system_message"
    AUTHENTICATION_STATUS = "authentication_status"
    SUBSCRIPTION_STATUS = "subscription_status"
    NEW_NOTIFICATION = "new_notification"
    USER_ACTIVITY_UPDATE = "user_activity_update"
    LEADERBOARD_UPDATE = "leaderboard_update"
    CHAT_MESSAGE = "chat_message"
    ERROR = "error"

class SubscriptionChannel(str, enum.Enum):
    GENERAL = "general"
    USER_NOTIFICATIONS = "user:{user_id}:notifications"
    LEADERBOARD = "leaderboard:{leaderboard_id}"
    CHAT_ROOM = "chat:{room_id}"
    USER_STATUS = "user:{user_id}:status"


# --- Pydantic Models for WebSocket Payloads ---

# Base model for all incoming messages from a client
class ClientMessage(BaseModel):
    type: WebSocketMessageType
    payload: Dict[str, Any] = Field(default_factory=dict)
    request_id: Optional[str] = None

# Base model for all outgoing messages from the server
class ServerMessage(BaseModel):
    type: WebSocketMessageType
    payload: Dict[str, Any]
    request_id: Optional[str] = None # Correlates with a client's request_id

# --- Specific Payload Schemas ---

# AUTHENTICATE
class AuthenticatePayload(BaseModel):
    token: str

# SUBSCRIBE / UNSUBSCRIBE
class SubscriptionPayload(BaseModel):
    channel: str # e.g., "leaderboard:global" or "user:123:notifications"

# SEND_MESSAGE (for chat)
class ChatMessagePayload(BaseModel):
    room_id: str
    text: str

# --- Server-Sent Payload Schemas ---

class SystemMessagePayload(BaseModel):
    message: str
    level: str = "info" # info, warn, error

class AuthenticationStatusPayload(BaseModel):
    success: bool
    user_id: Optional[int] = None
    error: Optional[str] = None

class SubscriptionStatusPayload(BaseModel):
    channel: str
    success: bool
    error: Optional[str] = None

class NotificationPayload(BaseModel):
    id: int
    title: str
    message: str
    read: bool

class LeaderboardUpdatePayload(BaseModel):
    leaderboard_id: str
    rankings: List[Dict[str, Any]]

class ChatMessageBroadcastPayload(BaseModel):
    room_id: str
    sender_id: int
    sender_username: str
    text: str
    timestamp: str 