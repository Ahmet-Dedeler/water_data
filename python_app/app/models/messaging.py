from pydantic import BaseModel, Field, validator
from typing import Optional, List, Dict, Any, Union
from datetime import datetime
from enum import Enum


class MessageType(str, Enum):
    """Types of messages that can be sent."""
    TEXT = "text"                    # Plain text message
    IMAGE = "image"                  # Image attachment
    EMOJI = "emoji"                  # Emoji reaction
    SYSTEM = "system"                # System-generated message
    WATER_LOG = "water_log"          # Shared water log
    ACHIEVEMENT = "achievement"      # Shared achievement
    CHALLENGE_INVITE = "challenge_invite"  # Challenge invitation
    FRIEND_REQUEST = "friend_request"      # Friend request notification
    LOCATION = "location"            # Location sharing
    VOICE_NOTE = "voice_note"        # Voice message
    STICKER = "sticker"              # Sticker/GIF
    POLL = "poll"                    # Poll message


class MessageStatus(str, Enum):
    """Status of a message."""
    SENT = "sent"                    # Message sent successfully
    DELIVERED = "delivered"          # Message delivered to recipient
    READ = "read"                    # Message read by recipient
    FAILED = "failed"                # Message failed to send
    DELETED = "deleted"              # Message deleted


class ConversationType(str, Enum):
    """Types of conversations."""
    DIRECT = "direct"                # Direct message between two users
    GROUP = "group"                  # Group conversation (future feature)


class ConversationStatus(str, Enum):
    """Status of a conversation."""
    ACTIVE = "active"                # Active conversation
    ARCHIVED = "archived"            # Archived conversation
    MUTED = "muted"                  # Muted conversation
    BLOCKED = "blocked"              # Blocked conversation


class AttachmentType(str, Enum):
    """Types of message attachments."""
    IMAGE = "image"
    VIDEO = "video"
    AUDIO = "audio"
    DOCUMENT = "document"
    WATER_LOG = "water_log"
    ACHIEVEMENT = "achievement"
    LOCATION = "location"


class Message(BaseModel):
    """Core model for messages."""
    id: Optional[int] = Field(None, description="Message ID")
    conversation_id: int = Field(..., description="Conversation ID")
    sender_id: int = Field(..., description="User ID of message sender")
    recipient_id: Optional[int] = Field(None, description="User ID of message recipient (for direct messages)")
    
    # Message content
    message_type: MessageType = Field(MessageType.TEXT, description="Type of message")
    content: Optional[str] = Field(None, max_length=2000, description="Message text content")
    
    # Attachments and media
    attachments: List[Dict[str, Any]] = Field(default_factory=list, description="Message attachments")
    
    # Message metadata
    status: MessageStatus = Field(MessageStatus.SENT, description="Message status")
    is_edited: bool = Field(False, description="Whether message was edited")
    edit_count: int = Field(0, description="Number of times message was edited")
    
    # Reactions and engagement
    reactions: Dict[str, List[int]] = Field(default_factory=dict, description="Emoji reactions with user IDs")
    
    # Message threading
    reply_to_message_id: Optional[int] = Field(None, description="ID of message being replied to")
    thread_count: int = Field(0, description="Number of replies to this message")
    
    # Delivery tracking
    sent_at: datetime = Field(default_factory=datetime.utcnow, description="When message was sent")
    delivered_at: Optional[datetime] = Field(None, description="When message was delivered")
    read_at: Optional[datetime] = Field(None, description="When message was read")
    
    # Message lifecycle
    created_at: datetime = Field(default_factory=datetime.utcnow, description="Message creation time")
    updated_at: Optional[datetime] = Field(None, description="Last update time")
    deleted_at: Optional[datetime] = Field(None, description="When message was deleted")
    
    # Temporary/ephemeral messages
    expires_at: Optional[datetime] = Field(None, description="When message expires (for temporary messages)")
    
    # System message data
    system_data: Optional[Dict[str, Any]] = Field(None, description="Data for system messages")


class MessageAttachment(BaseModel):
    """Model for message attachments."""
    id: Optional[int] = Field(None, description="Attachment ID")
    message_id: int = Field(..., description="Message ID")
    attachment_type: AttachmentType = Field(..., description="Type of attachment")
    
    # File information
    file_url: Optional[str] = Field(None, description="URL to the attachment file")
    file_name: Optional[str] = Field(None, description="Original filename")
    file_size: Optional[int] = Field(None, description="File size in bytes")
    mime_type: Optional[str] = Field(None, description="MIME type of the file")
    
    # Media metadata
    thumbnail_url: Optional[str] = Field(None, description="Thumbnail URL for media files")
    duration: Optional[int] = Field(None, description="Duration in seconds for audio/video")
    dimensions: Optional[Dict[str, int]] = Field(None, description="Width/height for images/videos")
    
    # Structured data attachments
    data: Optional[Dict[str, Any]] = Field(None, description="Structured data for special attachments")
    
    # Metadata
    created_at: datetime = Field(default_factory=datetime.utcnow, description="Attachment creation time")


class Conversation(BaseModel):
    """Model for conversations between users."""
    id: Optional[int] = Field(None, description="Conversation ID")
    conversation_type: ConversationType = Field(ConversationType.DIRECT, description="Type of conversation")
    
    # Participants
    participants: List[int] = Field(..., min_items=2, description="User IDs of conversation participants")
    created_by: int = Field(..., description="User ID who created the conversation")
    
    # Conversation metadata
    title: Optional[str] = Field(None, max_length=100, description="Conversation title (for group chats)")
    description: Optional[str] = Field(None, max_length=500, description="Conversation description")
    
    # Status and settings
    status: ConversationStatus = Field(ConversationStatus.ACTIVE, description="Conversation status")
    is_pinned: bool = Field(False, description="Whether conversation is pinned")
    
    # Message statistics
    total_messages: int = Field(0, description="Total number of messages")
    last_message_id: Optional[int] = Field(None, description="ID of the last message")
    last_message_at: Optional[datetime] = Field(None, description="Timestamp of last message")
    
    # Participant settings
    participant_settings: Dict[int, Dict[str, Any]] = Field(
        default_factory=dict, 
        description="Per-participant settings (muted, notifications, etc.)"
    )
    
    # Timestamps
    created_at: datetime = Field(default_factory=datetime.utcnow, description="Conversation creation time")
    updated_at: Optional[datetime] = Field(None, description="Last update time")
    archived_at: Optional[datetime] = Field(None, description="When conversation was archived")


class MessageCreate(BaseModel):
    """Model for creating new messages."""
    recipient_id: Optional[int] = Field(None, description="Recipient user ID (for new conversations)")
    conversation_id: Optional[int] = Field(None, description="Existing conversation ID")
    message_type: MessageType = Field(MessageType.TEXT, description="Type of message")
    content: Optional[str] = Field(None, max_length=2000, description="Message content")
    reply_to_message_id: Optional[int] = Field(None, description="ID of message being replied to")
    attachments: Optional[List[Dict[str, Any]]] = Field(None, description="Message attachments")
    expires_at: Optional[datetime] = Field(None, description="When message expires")
    system_data: Optional[Dict[str, Any]] = Field(None, description="System message data")
    
    @validator('content')
    def validate_content(cls, v, values):
        message_type = values.get('message_type')
        if message_type == MessageType.TEXT and not v:
            raise ValueError('Text messages must have content')
        return v


class MessageUpdate(BaseModel):
    """Model for updating messages."""
    content: Optional[str] = Field(None, max_length=2000, description="Updated message content")
    status: Optional[MessageStatus] = Field(None, description="Updated message status")


class MessageReaction(BaseModel):
    """Model for message reactions."""
    id: Optional[int] = Field(None, description="Reaction ID")
    message_id: int = Field(..., description="Message ID")
    user_id: int = Field(..., description="User who reacted")
    emoji: str = Field(..., max_length=50, description="Emoji reaction")
    created_at: datetime = Field(default_factory=datetime.utcnow, description="Reaction creation time")


class MessageReactionCreate(BaseModel):
    """Model for creating message reactions."""
    emoji: str = Field(..., max_length=50, description="Emoji reaction")


class ConversationCreate(BaseModel):
    """Model for creating conversations."""
    participant_ids: List[int] = Field(..., min_items=1, description="User IDs to add to conversation")
    conversation_type: ConversationType = Field(ConversationType.DIRECT, description="Type of conversation")
    title: Optional[str] = Field(None, max_length=100, description="Conversation title")
    description: Optional[str] = Field(None, max_length=500, description="Conversation description")
    initial_message: Optional[MessageCreate] = Field(None, description="Initial message to send")


class ConversationUpdate(BaseModel):
    """Model for updating conversations."""
    title: Optional[str] = Field(None, max_length=100, description="Updated conversation title")
    description: Optional[str] = Field(None, max_length=500, description="Updated conversation description")
    status: Optional[ConversationStatus] = Field(None, description="Updated conversation status")
    is_pinned: Optional[bool] = Field(None, description="Whether conversation is pinned")


class ConversationSettings(BaseModel):
    """Model for user-specific conversation settings."""
    conversation_id: int = Field(..., description="Conversation ID")
    user_id: int = Field(..., description="User ID")
    is_muted: bool = Field(False, description="Whether conversation is muted")
    notifications_enabled: bool = Field(True, description="Whether notifications are enabled")
    custom_name: Optional[str] = Field(None, max_length=100, description="Custom name for the conversation")
    is_archived: bool = Field(False, description="Whether conversation is archived for this user")
    last_read_message_id: Optional[int] = Field(None, description="ID of last read message")
    last_read_at: Optional[datetime] = Field(None, description="When user last read messages")


class ConversationSettingsUpdate(BaseModel):
    """Model for updating conversation settings."""
    is_muted: Optional[bool] = Field(None, description="Whether conversation is muted")
    notifications_enabled: Optional[bool] = Field(None, description="Whether notifications are enabled")
    custom_name: Optional[str] = Field(None, max_length=100, description="Custom name for the conversation")
    is_archived: Optional[bool] = Field(None, description="Whether conversation is archived")


class MessageListResponse(BaseModel):
    """Response model for message lists."""
    messages: List[Message] = Field(..., description="List of messages")
    total_count: int = Field(..., description="Total number of messages")
    unread_count: int = Field(0, description="Number of unread messages")
    
    # Pagination
    page: int = Field(..., description="Current page")
    page_size: int = Field(..., description="Items per page")
    has_next: bool = Field(..., description="Whether there are more pages")
    has_previous: bool = Field(..., description="Whether there are previous pages")
    
    # Conversation context
    conversation: Optional[Conversation] = Field(None, description="Conversation details")


class ConversationListResponse(BaseModel):
    """Response model for conversation lists."""
    conversations: List[Conversation] = Field(..., description="List of conversations")
    total_count: int = Field(..., description="Total number of conversations")
    unread_conversations: int = Field(0, description="Number of conversations with unread messages")
    
    # Pagination
    page: int = Field(..., description="Current page")
    page_size: int = Field(..., description="Items per page")
    has_next: bool = Field(..., description="Whether there are more pages")


class MessageSearchFilter(BaseModel):
    """Filter options for message search."""
    conversation_id: Optional[int] = Field(None, description="Filter by conversation")
    sender_id: Optional[int] = Field(None, description="Filter by sender")
    message_types: Optional[List[MessageType]] = Field(None, description="Filter by message types")
    date_from: Optional[datetime] = Field(None, description="Filter from date")
    date_to: Optional[datetime] = Field(None, description="Filter to date")
    has_attachments: Optional[bool] = Field(None, description="Filter messages with attachments")
    is_unread: Optional[bool] = Field(None, description="Filter unread messages")


class ConversationFilter(BaseModel):
    """Filter options for conversations."""
    conversation_type: Optional[ConversationType] = Field(None, description="Filter by conversation type")
    status: Optional[ConversationStatus] = Field(None, description="Filter by status")
    participant_id: Optional[int] = Field(None, description="Filter by participant")
    has_unread: Optional[bool] = Field(None, description="Filter conversations with unread messages")
    is_pinned: Optional[bool] = Field(None, description="Filter pinned conversations")


class MessageStats(BaseModel):
    """Statistics about user's messaging activity."""
    total_messages_sent: int = Field(..., description="Total messages sent")
    total_messages_received: int = Field(..., description="Total messages received")
    total_conversations: int = Field(..., description="Total number of conversations")
    active_conversations: int = Field(..., description="Number of active conversations")
    
    # Time-based stats
    messages_today: int = Field(..., description="Messages sent today")
    messages_this_week: int = Field(..., description="Messages sent this week")
    messages_this_month: int = Field(..., description="Messages sent this month")
    
    # Engagement stats
    average_response_time_minutes: float = Field(..., description="Average response time in minutes")
    most_active_conversation_id: Optional[int] = Field(None, description="Most active conversation")
    favorite_emoji_reactions: List[str] = Field(default_factory=list, description="Most used emoji reactions")
    
    # Message type breakdown
    messages_by_type: Dict[str, int] = Field(default_factory=dict, description="Message count by type")
    
    # Social stats
    most_messaged_friend: Optional[str] = Field(None, description="Friend with most messages")
    longest_conversation_days: Optional[int] = Field(None, description="Longest active conversation in days")


class TypingIndicator(BaseModel):
    """Model for typing indicators."""
    conversation_id: int = Field(..., description="Conversation ID")
    user_id: int = Field(..., description="User who is typing")
    started_at: datetime = Field(default_factory=datetime.utcnow, description="When typing started")
    expires_at: datetime = Field(..., description="When typing indicator expires")


class MessageDeliveryReceipt(BaseModel):
    """Model for message delivery receipts."""
    message_id: int = Field(..., description="Message ID")
    user_id: int = Field(..., description="User who received/read the message")
    status: MessageStatus = Field(..., description="Delivery status")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Status timestamp")


class MessageDraft(BaseModel):
    """Model for message drafts."""
    id: Optional[int] = Field(None, description="Draft ID")
    conversation_id: int = Field(..., description="Conversation ID")
    user_id: int = Field(..., description="User who created the draft")
    content: str = Field(..., max_length=2000, description="Draft content")
    message_type: MessageType = Field(MessageType.TEXT, description="Type of message")
    attachments: List[Dict[str, Any]] = Field(default_factory=list, description="Draft attachments")
    created_at: datetime = Field(default_factory=datetime.utcnow, description="Draft creation time")
    updated_at: Optional[datetime] = Field(None, description="Last update time")


class MessageDraftCreate(BaseModel):
    """Model for creating message drafts."""
    conversation_id: int = Field(..., description="Conversation ID")
    content: str = Field(..., max_length=2000, description="Draft content")
    message_type: MessageType = Field(MessageType.TEXT, description="Type of message")
    attachments: Optional[List[Dict[str, Any]]] = Field(None, description="Draft attachments")


class MessageDraftUpdate(BaseModel):
    """Model for updating message drafts."""
    content: Optional[str] = Field(None, max_length=2000, description="Updated draft content")
    attachments: Optional[List[Dict[str, Any]]] = Field(None, description="Updated draft attachments")


class BulkMessageOperation(BaseModel):
    """Model for bulk message operations."""
    message_ids: List[int] = Field(..., min_items=1, max_items=100, description="Message IDs to operate on")
    operation: str = Field(..., description="Operation to perform (delete, mark_read, etc.)")
    operation_data: Optional[Dict[str, Any]] = Field(None, description="Additional operation data")


class MessageTemplate(BaseModel):
    """Model for message templates."""
    id: Optional[int] = Field(None, description="Template ID")
    user_id: int = Field(..., description="User who created the template")
    name: str = Field(..., max_length=100, description="Template name")
    content: str = Field(..., max_length=2000, description="Template content")
    message_type: MessageType = Field(MessageType.TEXT, description="Type of message")
    category: Optional[str] = Field(None, description="Template category")
    usage_count: int = Field(0, description="Number of times template was used")
    is_public: bool = Field(False, description="Whether template is publicly available")
    created_at: datetime = Field(default_factory=datetime.utcnow, description="Template creation time")
    updated_at: Optional[datetime] = Field(None, description="Last update time")


class MessageTemplateCreate(BaseModel):
    """Model for creating message templates."""
    name: str = Field(..., max_length=100, description="Template name")
    content: str = Field(..., max_length=2000, description="Template content")
    message_type: MessageType = Field(MessageType.TEXT, description="Type of message")
    category: Optional[str] = Field(None, description="Template category")
    is_public: bool = Field(False, description="Whether template is publicly available")


class MessageTemplateUpdate(BaseModel):
    """Model for updating message templates."""
    name: Optional[str] = Field(None, max_length=100, description="Updated template name")
    content: Optional[str] = Field(None, max_length=2000, description="Updated template content")
    category: Optional[str] = Field(None, description="Updated template category")
    is_public: Optional[bool] = Field(None, description="Whether template is publicly available")


class ConversationParticipant(BaseModel):
    """Model for conversation participants."""
    user_id: int = Field(..., description="User ID")
    username: str = Field(..., description="Username")
    display_name: Optional[str] = Field(None, description="Display name")
    avatar_url: Optional[str] = Field(None, description="Avatar URL")
    is_online: bool = Field(False, description="Whether user is currently online")
    last_seen: Optional[datetime] = Field(None, description="When user was last seen")
    role: Optional[str] = Field(None, description="Role in conversation (for group chats)")
    joined_at: datetime = Field(..., description="When user joined the conversation")


class MessageSearchResult(BaseModel):
    """Model for message search results."""
    message: Message = Field(..., description="Found message")
    conversation: Conversation = Field(..., description="Conversation containing the message")
    context_messages: List[Message] = Field(default_factory=list, description="Surrounding messages for context")
    relevance_score: float = Field(..., description="Search relevance score")
    highlighted_content: Optional[str] = Field(None, description="Content with search terms highlighted") 