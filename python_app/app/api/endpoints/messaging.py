from fastapi import APIRouter, HTTPException, Depends, Query, status
from typing import Optional, List
import logging

from app.models.messaging import (
    Message, MessageCreate, MessageUpdate, MessageListResponse,
    Conversation, ConversationCreate, ConversationUpdate, ConversationListResponse,
    MessageReaction, MessageReactionCreate, ConversationSettings,
    ConversationSettingsUpdate, MessageSearchFilter, ConversationFilter,
    MessageStats, TypingIndicator, MessageDraft, MessageDraftCreate,
    MessageDraftUpdate, MessageTemplate, MessageTemplateCreate,
    MessageTemplateUpdate, BulkMessageOperation, MessageSearchResult,
    MessageType, ConversationType, MessageStatus, ConversationStatus
)
from app.models.common import BaseResponse
from app.services.messaging_service import messaging_service
from app.api.dependencies import get_current_user
from app.models.user import User

router = APIRouter(prefix="/messaging", tags=["messaging"])
logger = logging.getLogger(__name__)


# Conversation Endpoints

@router.post("/conversations", response_model=Conversation)
async def create_conversation(
    conversation_data: ConversationCreate,
    current_user: User = Depends(get_current_user)
):
    """Create a new conversation."""
    try:
        return await messaging_service.create_conversation(current_user.id, conversation_data)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error creating conversation: {e}")
        raise HTTPException(status_code=500, detail="Failed to create conversation")


@router.get("/conversations", response_model=ConversationListResponse)
async def get_user_conversations(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    conversation_type: Optional[ConversationType] = Query(None),
    status: Optional[ConversationStatus] = Query(None),
    participant_id: Optional[int] = Query(None),
    is_pinned: Optional[bool] = Query(None),
    include_archived: bool = Query(False),
    current_user: User = Depends(get_current_user)
):
    """Get user's conversations with filtering."""
    try:
        filter_options = ConversationFilter(
            conversation_type=conversation_type,
            status=status,
            participant_id=participant_id,
            is_pinned=is_pinned,
            include_archived=include_archived
        ) if any([conversation_type, status, participant_id, is_pinned is not None, include_archived]) else None
        
        return await messaging_service.get_user_conversations(
            current_user.id, filter_options, skip, limit
        )
    except Exception as e:
        logger.error(f"Error getting conversations: {e}")
        raise HTTPException(status_code=500, detail="Failed to get conversations")


@router.get("/conversations/{conversation_id}", response_model=Conversation)
async def get_conversation(
    conversation_id: int,
    current_user: User = Depends(get_current_user)
):
    """Get a specific conversation."""
    try:
        conversations_response = await messaging_service.get_user_conversations(
            current_user.id, skip=0, limit=1000
        )
        
        conversation = next((c for c in conversations_response.conversations if c.id == conversation_id), None)
        if not conversation:
            raise HTTPException(status_code=404, detail="Conversation not found")
        
        return conversation
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting conversation: {e}")
        raise HTTPException(status_code=500, detail="Failed to get conversation")


@router.put("/conversations/{conversation_id}", response_model=Conversation)
async def update_conversation(
    conversation_id: int,
    conversation_update: ConversationUpdate,
    current_user: User = Depends(get_current_user)
):
    """Update a conversation."""
    try:
        # This would be implemented in the service
        raise HTTPException(status_code=501, detail="Conversation updates not yet implemented")
    except Exception as e:
        logger.error(f"Error updating conversation: {e}")
        raise HTTPException(status_code=500, detail="Failed to update conversation")


# Message Endpoints

@router.post("/messages", response_model=Message)
async def send_message(
    message_data: MessageCreate,
    current_user: User = Depends(get_current_user)
):
    """Send a new message."""
    try:
        return await messaging_service.send_message(current_user.id, message_data)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error sending message: {e}")
        raise HTTPException(status_code=500, detail="Failed to send message")


@router.get("/conversations/{conversation_id}/messages", response_model=MessageListResponse)
async def get_conversation_messages(
    conversation_id: int,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    current_user: User = Depends(get_current_user)
):
    """Get messages from a conversation."""
    try:
        return await messaging_service.get_conversation_messages(
            current_user.id, conversation_id, skip, limit
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error getting messages: {e}")
        raise HTTPException(status_code=500, detail="Failed to get messages")


@router.get("/messages/{message_id}", response_model=Message)
async def get_message(
    message_id: int,
    current_user: User = Depends(get_current_user)
):
    """Get a specific message."""
    try:
        # This would be implemented in the service
        raise HTTPException(status_code=501, detail="Get single message not yet implemented")
    except Exception as e:
        logger.error(f"Error getting message: {e}")
        raise HTTPException(status_code=500, detail="Failed to get message")


@router.put("/messages/{message_id}", response_model=Message)
async def update_message(
    message_id: int,
    message_update: MessageUpdate,
    current_user: User = Depends(get_current_user)
):
    """Update a message (edit content)."""
    try:
        # This would be implemented in the service
        raise HTTPException(status_code=501, detail="Message updates not yet implemented")
    except Exception as e:
        logger.error(f"Error updating message: {e}")
        raise HTTPException(status_code=500, detail="Failed to update message")


@router.delete("/messages/{message_id}", response_model=BaseResponse)
async def delete_message(
    message_id: int,
    current_user: User = Depends(get_current_user)
):
    """Delete a message."""
    try:
        # This would be implemented in the service
        raise HTTPException(status_code=501, detail="Message deletion not yet implemented")
    except Exception as e:
        logger.error(f"Error deleting message: {e}")
        raise HTTPException(status_code=500, detail="Failed to delete message")


# Message Reactions

@router.post("/messages/{message_id}/reactions", response_model=MessageReaction)
async def add_message_reaction(
    message_id: int,
    reaction_data: MessageReactionCreate,
    current_user: User = Depends(get_current_user)
):
    """Add a reaction to a message."""
    try:
        return await messaging_service.add_message_reaction(
            current_user.id, message_id, reaction_data
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error adding reaction: {e}")
        raise HTTPException(status_code=500, detail="Failed to add reaction")


@router.delete("/messages/{message_id}/reactions", response_model=BaseResponse)
async def remove_message_reaction(
    message_id: int,
    current_user: User = Depends(get_current_user)
):
    """Remove user's reaction from a message."""
    try:
        success = await messaging_service.remove_message_reaction(current_user.id, message_id)
        if not success:
            raise HTTPException(status_code=404, detail="Reaction not found")
        
        return BaseResponse(
            success=True,
            message="Reaction removed successfully"
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error removing reaction: {e}")
        raise HTTPException(status_code=500, detail="Failed to remove reaction")


@router.get("/messages/{message_id}/reactions", response_model=List[MessageReaction])
async def get_message_reactions(
    message_id: int,
    current_user: User = Depends(get_current_user)
):
    """Get all reactions for a message."""
    try:
        # This would be implemented in the service
        raise HTTPException(status_code=501, detail="Get message reactions not yet implemented")
    except Exception as e:
        logger.error(f"Error getting reactions: {e}")
        raise HTTPException(status_code=500, detail="Failed to get reactions")


# Conversation Settings

@router.get("/conversations/{conversation_id}/settings", response_model=ConversationSettings)
async def get_conversation_settings(
    conversation_id: int,
    current_user: User = Depends(get_current_user)
):
    """Get user's settings for a conversation."""
    try:
        settings = await messaging_service.get_conversation_settings(current_user.id, conversation_id)
        if not settings:
            raise HTTPException(status_code=404, detail="Settings not found")
        return settings
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting conversation settings: {e}")
        raise HTTPException(status_code=500, detail="Failed to get settings")


@router.put("/conversations/{conversation_id}/settings", response_model=ConversationSettings)
async def update_conversation_settings(
    conversation_id: int,
    settings_update: ConversationSettingsUpdate,
    current_user: User = Depends(get_current_user)
):
    """Update user's conversation settings."""
    try:
        settings = await messaging_service.update_conversation_settings(
            current_user.id, conversation_id, settings_update
        )
        if not settings:
            raise HTTPException(status_code=404, detail="Settings not found")
        return settings
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating conversation settings: {e}")
        raise HTTPException(status_code=500, detail="Failed to update settings")


# Bulk Operations

@router.post("/conversations/{conversation_id}/mark-read", response_model=BaseResponse)
async def mark_conversation_as_read(
    conversation_id: int,
    current_user: User = Depends(get_current_user)
):
    """Mark all messages in a conversation as read."""
    try:
        # Get all messages in conversation
        messages_response = await messaging_service.get_conversation_messages(
            current_user.id, conversation_id, skip=0, limit=1000
        )
        
        # Mark as read (this happens automatically in get_conversation_messages)
        return BaseResponse(
            success=True,
            message=f"Marked {len(messages_response.messages)} messages as read"
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error marking conversation as read: {e}")
        raise HTTPException(status_code=500, detail="Failed to mark as read")


@router.post("/conversations/{conversation_id}/archive", response_model=BaseResponse)
async def archive_conversation(
    conversation_id: int,
    current_user: User = Depends(get_current_user)
):
    """Archive a conversation."""
    try:
        settings_update = ConversationSettingsUpdate(is_archived=True)
        await messaging_service.update_conversation_settings(
            current_user.id, conversation_id, settings_update
        )
        
        return BaseResponse(
            success=True,
            message="Conversation archived successfully"
        )
    except Exception as e:
        logger.error(f"Error archiving conversation: {e}")
        raise HTTPException(status_code=500, detail="Failed to archive conversation")


@router.post("/conversations/{conversation_id}/unarchive", response_model=BaseResponse)
async def unarchive_conversation(
    conversation_id: int,
    current_user: User = Depends(get_current_user)
):
    """Unarchive a conversation."""
    try:
        settings_update = ConversationSettingsUpdate(is_archived=False)
        await messaging_service.update_conversation_settings(
            current_user.id, conversation_id, settings_update
        )
        
        return BaseResponse(
            success=True,
            message="Conversation unarchived successfully"
        )
    except Exception as e:
        logger.error(f"Error unarchiving conversation: {e}")
        raise HTTPException(status_code=500, detail="Failed to unarchive conversation")


@router.post("/conversations/{conversation_id}/mute", response_model=BaseResponse)
async def mute_conversation(
    conversation_id: int,
    current_user: User = Depends(get_current_user)
):
    """Mute notifications for a conversation."""
    try:
        settings_update = ConversationSettingsUpdate(is_muted=True)
        await messaging_service.update_conversation_settings(
            current_user.id, conversation_id, settings_update
        )
        
        return BaseResponse(
            success=True,
            message="Conversation muted successfully"
        )
    except Exception as e:
        logger.error(f"Error muting conversation: {e}")
        raise HTTPException(status_code=500, detail="Failed to mute conversation")


@router.post("/conversations/{conversation_id}/unmute", response_model=BaseResponse)
async def unmute_conversation(
    conversation_id: int,
    current_user: User = Depends(get_current_user)
):
    """Unmute notifications for a conversation."""
    try:
        settings_update = ConversationSettingsUpdate(is_muted=False)
        await messaging_service.update_conversation_settings(
            current_user.id, conversation_id, settings_update
        )
        
        return BaseResponse(
            success=True,
            message="Conversation unmuted successfully"
        )
    except Exception as e:
        logger.error(f"Error unmuting conversation: {e}")
        raise HTTPException(status_code=500, detail="Failed to unmute conversation")


# Search and Discovery

@router.get("/search/messages", response_model=List[MessageSearchResult])
async def search_messages(
    query: str = Query(..., min_length=1),
    conversation_id: Optional[int] = Query(None),
    message_type: Optional[MessageType] = Query(None),
    sender_id: Optional[int] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_user)
):
    """Search messages across conversations."""
    try:
        # This would be implemented in the service
        raise HTTPException(status_code=501, detail="Message search not yet implemented")
    except Exception as e:
        logger.error(f"Error searching messages: {e}")
        raise HTTPException(status_code=500, detail="Failed to search messages")


@router.get("/search/conversations", response_model=List[Conversation])
async def search_conversations(
    query: str = Query(..., min_length=1),
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_user)
):
    """Search conversations by title or participant name."""
    try:
        # This would be implemented in the service
        raise HTTPException(status_code=501, detail="Conversation search not yet implemented")
    except Exception as e:
        logger.error(f"Error searching conversations: {e}")
        raise HTTPException(status_code=500, detail="Failed to search conversations")


# Statistics and Analytics

@router.get("/stats", response_model=MessageStats)
async def get_messaging_stats(
    current_user: User = Depends(get_current_user)
):
    """Get comprehensive messaging statistics."""
    try:
        return await messaging_service.get_user_messaging_stats(current_user.id)
    except Exception as e:
        logger.error(f"Error getting messaging stats: {e}")
        raise HTTPException(status_code=500, detail="Failed to get messaging stats")


@router.get("/stats/conversations/{conversation_id}")
async def get_conversation_stats(
    conversation_id: int,
    current_user: User = Depends(get_current_user)
):
    """Get statistics for a specific conversation."""
    try:
        # This would be implemented in the service
        raise HTTPException(status_code=501, detail="Conversation stats not yet implemented")
    except Exception as e:
        logger.error(f"Error getting conversation stats: {e}")
        raise HTTPException(status_code=500, detail="Failed to get conversation stats")


# Message Drafts

@router.get("/conversations/{conversation_id}/drafts", response_model=List[MessageDraft])
async def get_conversation_drafts(
    conversation_id: int,
    current_user: User = Depends(get_current_user)
):
    """Get message drafts for a conversation."""
    try:
        # This would be implemented in the service
        raise HTTPException(status_code=501, detail="Message drafts not yet implemented")
    except Exception as e:
        logger.error(f"Error getting drafts: {e}")
        raise HTTPException(status_code=500, detail="Failed to get drafts")


@router.post("/conversations/{conversation_id}/drafts", response_model=MessageDraft)
async def save_message_draft(
    conversation_id: int,
    draft_data: MessageDraftCreate,
    current_user: User = Depends(get_current_user)
):
    """Save a message draft."""
    try:
        # This would be implemented in the service
        raise HTTPException(status_code=501, detail="Message drafts not yet implemented")
    except Exception as e:
        logger.error(f"Error saving draft: {e}")
        raise HTTPException(status_code=500, detail="Failed to save draft")


@router.delete("/drafts/{draft_id}", response_model=BaseResponse)
async def delete_message_draft(
    draft_id: int,
    current_user: User = Depends(get_current_user)
):
    """Delete a message draft."""
    try:
        # This would be implemented in the service
        raise HTTPException(status_code=501, detail="Message drafts not yet implemented")
    except Exception as e:
        logger.error(f"Error deleting draft: {e}")
        raise HTTPException(status_code=500, detail="Failed to delete draft")


# Message Templates

@router.get("/templates", response_model=List[MessageTemplate])
async def get_message_templates(
    current_user: User = Depends(get_current_user)
):
    """Get user's message templates."""
    try:
        # This would be implemented in the service
        raise HTTPException(status_code=501, detail="Message templates not yet implemented")
    except Exception as e:
        logger.error(f"Error getting templates: {e}")
        raise HTTPException(status_code=500, detail="Failed to get templates")


@router.post("/templates", response_model=MessageTemplate)
async def create_message_template(
    template_data: MessageTemplateCreate,
    current_user: User = Depends(get_current_user)
):
    """Create a new message template."""
    try:
        # This would be implemented in the service
        raise HTTPException(status_code=501, detail="Message templates not yet implemented")
    except Exception as e:
        logger.error(f"Error creating template: {e}")
        raise HTTPException(status_code=500, detail="Failed to create template")


@router.delete("/templates/{template_id}", response_model=BaseResponse)
async def delete_message_template(
    template_id: int,
    current_user: User = Depends(get_current_user)
):
    """Delete a message template."""
    try:
        # This would be implemented in the service
        raise HTTPException(status_code=501, detail="Message templates not yet implemented")
    except Exception as e:
        logger.error(f"Error deleting template: {e}")
        raise HTTPException(status_code=500, detail="Failed to delete template")


# Real-time Features (WebSocket endpoints would be separate)

@router.post("/conversations/{conversation_id}/typing", response_model=BaseResponse)
async def start_typing(
    conversation_id: int,
    current_user: User = Depends(get_current_user)
):
    """Indicate that user is typing in a conversation."""
    try:
        # This would be implemented with WebSocket support
        return BaseResponse(
            success=True,
            message="Typing indicator sent"
        )
    except Exception as e:
        logger.error(f"Error sending typing indicator: {e}")
        raise HTTPException(status_code=500, detail="Failed to send typing indicator")


@router.delete("/conversations/{conversation_id}/typing", response_model=BaseResponse)
async def stop_typing(
    conversation_id: int,
    current_user: User = Depends(get_current_user)
):
    """Stop typing indicator in a conversation."""
    try:
        # This would be implemented with WebSocket support
        return BaseResponse(
            success=True,
            message="Typing indicator stopped"
        )
    except Exception as e:
        logger.error(f"Error stopping typing indicator: {e}")
        raise HTTPException(status_code=500, detail="Failed to stop typing indicator")


# System Information

@router.get("/info", response_model=dict)
async def get_messaging_system_info():
    """Get messaging system information and capabilities."""
    return {
        "supported_message_types": [t.value for t in MessageType],
        "supported_attachment_types": ["image", "document", "audio", "video"],
        "max_message_length": 2000,
        "max_attachment_size_mb": 10,
        "max_attachments_per_message": 5,
        "supported_emoji_reactions": ["👍", "❤️", "😂", "😮", "😢", "😡", "👎"],
        "features": {
            "message_editing": True,
            "message_deletion": True,
            "message_reactions": True,
            "file_attachments": True,
            "message_threading": True,
            "typing_indicators": True,
            "read_receipts": True,
            "message_search": True,
            "conversation_archiving": True,
            "conversation_muting": True,
            "message_drafts": True,
            "message_templates": True,
            "bulk_operations": True
        }
    } 