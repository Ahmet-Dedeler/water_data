import json
import logging
from typing import Optional, List, Dict, Any, Tuple
from datetime import datetime, timedelta
from pathlib import Path
from collections import defaultdict, Counter
import asyncio

from app.models.messaging import (
    Message, MessageAttachment, Conversation, MessageCreate, MessageUpdate,
    MessageReaction, MessageReactionCreate, ConversationCreate, ConversationUpdate,
    ConversationSettings, ConversationSettingsUpdate, MessageListResponse,
    ConversationListResponse, MessageSearchFilter, ConversationFilter,
    MessageStats, TypingIndicator, MessageDeliveryReceipt, MessageDraft,
    MessageDraftCreate, MessageDraftUpdate, BulkMessageOperation,
    MessageTemplate, MessageTemplateCreate, MessageTemplateUpdate,
    ConversationParticipant, MessageSearchResult, MessageType, MessageStatus,
    ConversationType, ConversationStatus, AttachmentType
)
from app.models.common import BaseResponse
from app.services.friend_service import friend_service
from app.services.user_service import user_service

logger = logging.getLogger(__name__)


class MessagingService:
    """Comprehensive messaging service for direct messages and conversations."""
    
    def __init__(self):
        self.messages_file = Path(__file__).parent.parent / "data" / "messages.json"
        self.conversations_file = Path(__file__).parent.parent / "data" / "conversations.json"
        self.attachments_file = Path(__file__).parent.parent / "data" / "message_attachments.json"
        self.reactions_file = Path(__file__).parent.parent / "data" / "message_reactions.json"
        self.settings_file = Path(__file__).parent.parent / "data" / "conversation_settings.json"
        self.drafts_file = Path(__file__).parent.parent / "data" / "message_drafts.json"
        self.templates_file = Path(__file__).parent.parent / "data" / "message_templates.json"
        self.typing_file = Path(__file__).parent.parent / "data" / "typing_indicators.json"
        self._ensure_data_files()
        self._messages_cache = None
        self._conversations_cache = None
        self._attachments_cache = None
        self._reactions_cache = None
        self._settings_cache = None
        self._drafts_cache = None
        self._templates_cache = None
        self._typing_cache = None
        self._next_message_id = 1
        self._next_conversation_id = 1
        self._next_attachment_id = 1
        self._next_reaction_id = 1
        self._next_draft_id = 1
        self._next_template_id = 1
    
    def _ensure_data_files(self):
        """Ensure messaging data files exist."""
        data_dir = self.messages_file.parent
        data_dir.mkdir(exist_ok=True)
        
        for file_path in [
            self.messages_file, self.conversations_file, self.attachments_file,
            self.reactions_file, self.settings_file, self.drafts_file,
            self.templates_file, self.typing_file
        ]:
            if not file_path.exists():
                with open(file_path, 'w') as f:
                    json.dump([], f)
    
    async def _load_messages(self) -> List[Dict]:
        """Load messages from file."""
        if self._messages_cache is None:
            try:
                with open(self.messages_file, 'r') as f:
                    self._messages_cache = json.load(f)
                    
                # Update next ID
                if self._messages_cache:
                    self._next_message_id = max(m['id'] for m in self._messages_cache) + 1
            except Exception as e:
                logger.error(f"Error loading messages: {e}")
                self._messages_cache = []
        return self._messages_cache
    
    async def _save_messages(self, messages: List[Dict]):
        """Save messages to file."""
        try:
            with open(self.messages_file, 'w') as f:
                json.dump(messages, f, indent=2, default=str)
            self._messages_cache = messages
        except Exception as e:
            logger.error(f"Error saving messages: {e}")
            raise
    
    async def _load_conversations(self) -> List[Dict]:
        """Load conversations from file."""
        if self._conversations_cache is None:
            try:
                with open(self.conversations_file, 'r') as f:
                    self._conversations_cache = json.load(f)
                    
                # Update next ID
                if self._conversations_cache:
                    self._next_conversation_id = max(c['id'] for c in self._conversations_cache) + 1
            except Exception as e:
                logger.error(f"Error loading conversations: {e}")
                self._conversations_cache = []
        return self._conversations_cache
    
    async def _save_conversations(self, conversations: List[Dict]):
        """Save conversations to file."""
        try:
            with open(self.conversations_file, 'w') as f:
                json.dump(conversations, f, indent=2, default=str)
            self._conversations_cache = conversations
        except Exception as e:
            logger.error(f"Error saving conversations: {e}")
            raise
    
    async def _load_reactions(self) -> List[Dict]:
        """Load message reactions from file."""
        if self._reactions_cache is None:
            try:
                with open(self.reactions_file, 'r') as f:
                    self._reactions_cache = json.load(f)
                    
                # Update next ID
                if self._reactions_cache:
                    self._next_reaction_id = max(r['id'] for r in self._reactions_cache) + 1
            except Exception as e:
                logger.error(f"Error loading reactions: {e}")
                self._reactions_cache = []
        return self._reactions_cache
    
    async def _save_reactions(self, reactions: List[Dict]):
        """Save message reactions to file."""
        try:
            with open(self.reactions_file, 'w') as f:
                json.dump(reactions, f, indent=2, default=str)
            self._reactions_cache = reactions
        except Exception as e:
            logger.error(f"Error saving reactions: {e}")
            raise
    
    async def _load_settings(self) -> List[Dict]:
        """Load conversation settings from file."""
        if self._settings_cache is None:
            try:
                with open(self.settings_file, 'r') as f:
                    self._settings_cache = json.load(f)
            except Exception as e:
                logger.error(f"Error loading settings: {e}")
                self._settings_cache = []
        return self._settings_cache
    
    async def _save_settings(self, settings: List[Dict]):
        """Save conversation settings to file."""
        try:
            with open(self.settings_file, 'w') as f:
                json.dump(settings, f, indent=2, default=str)
            self._settings_cache = settings
        except Exception as e:
            logger.error(f"Error saving settings: {e}")
            raise
    
    async def _load_drafts(self) -> List[Dict]:
        """Load message drafts from file."""
        if self._drafts_cache is None:
            try:
                with open(self.drafts_file, 'r') as f:
                    self._drafts_cache = json.load(f)
                    
                # Update next ID
                if self._drafts_cache:
                    self._next_draft_id = max(d['id'] for d in self._drafts_cache) + 1
            except Exception as e:
                logger.error(f"Error loading drafts: {e}")
                self._drafts_cache = []
        return self._drafts_cache
    
    async def _save_drafts(self, drafts: List[Dict]):
        """Save message drafts to file."""
        try:
            with open(self.drafts_file, 'w') as f:
                json.dump(drafts, f, indent=2, default=str)
            self._drafts_cache = drafts
        except Exception as e:
            logger.error(f"Error saving drafts: {e}")
            raise
    
    # Conversation Management
    
    async def create_conversation(
        self,
        user_id: int,
        conversation_data: ConversationCreate
    ) -> Conversation:
        """Create a new conversation."""
        try:
            conversations = await self._load_conversations()
            
            # Validate participants are friends
            for participant_id in conversation_data.participant_ids:
                if participant_id != user_id:
                    # Check if they are friends
                    friends_response = await friend_service.get_friends(user_id, skip=0, limit=1000)
                    friend_ids = {f.user_id for f in friends_response.friends}
                    
                    if participant_id not in friend_ids:
                        raise ValueError(f"User {participant_id} is not a friend")
            
            # For direct messages, check if conversation already exists
            if conversation_data.conversation_type == ConversationType.DIRECT:
                if len(conversation_data.participant_ids) != 1:
                    raise ValueError("Direct conversations must have exactly one other participant")
                
                other_user_id = conversation_data.participant_ids[0]
                participants = sorted([user_id, other_user_id])
                
                # Check for existing conversation
                existing_conversation = next((
                    c for c in conversations
                    if c['conversation_type'] == ConversationType.DIRECT.value
                    and sorted(c['participants']) == participants
                ), None)
                
                if existing_conversation:
                    return Conversation(**existing_conversation)
            
            # Create new conversation
            participants = [user_id] + conversation_data.participant_ids
            conversation_dict = {
                "id": self._next_conversation_id,
                "conversation_type": conversation_data.conversation_type.value,
                "participants": list(set(participants)),  # Remove duplicates
                "created_by": user_id,
                "title": conversation_data.title,
                "description": conversation_data.description,
                "status": ConversationStatus.ACTIVE.value,
                "is_pinned": False,
                "total_messages": 0,
                "last_message_id": None,
                "last_message_at": None,
                "participant_settings": {},
                "created_at": datetime.utcnow().isoformat(),
                "updated_at": None,
                "archived_at": None
            }
            
            conversations.append(conversation_dict)
            await self._save_conversations(conversations)
            
            self._next_conversation_id += 1
            
            # Send initial message if provided
            if conversation_data.initial_message:
                conversation_data.initial_message.conversation_id = conversation_dict["id"]
                await self.send_message(user_id, conversation_data.initial_message)
            
            logger.info(f"Created conversation {conversation_dict['id']} with {len(participants)} participants")
            return Conversation(**conversation_dict)
            
        except Exception as e:
            logger.error(f"Error creating conversation: {e}")
            raise
    
    async def get_user_conversations(
        self,
        user_id: int,
        filter_options: Optional[ConversationFilter] = None,
        skip: int = 0,
        limit: int = 20
    ) -> ConversationListResponse:
        """Get conversations for a user."""
        try:
            conversations = await self._load_conversations()
            messages = await self._load_messages()
            settings = await self._load_settings()
            
            # Filter conversations where user is a participant
            user_conversations = [
                c for c in conversations
                if user_id in c['participants']
            ]
            
            # Apply filters
            if filter_options:
                user_conversations = self._filter_conversations(user_conversations, filter_options)
            
            # Apply user-specific settings (archived, etc.)
            user_settings_map = {
                s['conversation_id']: s for s in settings
                if s['user_id'] == user_id
            }
            
            filtered_conversations = []
            for conv in user_conversations:
                conv_settings = user_settings_map.get(conv['id'], {})
                
                # Skip archived conversations unless specifically requested
                if conv_settings.get('is_archived', False) and not (
                    filter_options and hasattr(filter_options, 'include_archived') and filter_options.include_archived
                ):
                    continue
                
                # Enrich conversation with user-specific data
                enriched_conv = await self._enrich_conversation_for_user(conv, user_id, messages, conv_settings)
                filtered_conversations.append(enriched_conv)
            
            # Sort by last message time (most recent first)
            filtered_conversations.sort(
                key=lambda x: x.get('last_message_at') or x['created_at'],
                reverse=True
            )
            
            # Apply pagination
            total_count = len(filtered_conversations)
            paginated_conversations = filtered_conversations[skip:skip + limit]
            
            # Count unread conversations
            unread_conversations = sum(
                1 for c in filtered_conversations
                if c.get('unread_count', 0) > 0
            )
            
            return ConversationListResponse(
                conversations=[Conversation(**c) for c in paginated_conversations],
                total_count=total_count,
                unread_conversations=unread_conversations,
                page=skip // limit + 1,
                page_size=limit,
                has_next=skip + limit < total_count
            )
            
        except Exception as e:
            logger.error(f"Error getting user conversations: {e}")
            return ConversationListResponse(
                conversations=[],
                total_count=0,
                unread_conversations=0,
                page=1,
                page_size=limit,
                has_next=False
            )
    
    def _filter_conversations(self, conversations: List[Dict], filter_options: ConversationFilter) -> List[Dict]:
        """Apply filters to conversations."""
        filtered = conversations
        
        if filter_options.conversation_type:
            filtered = [c for c in filtered if c['conversation_type'] == filter_options.conversation_type.value]
        
        if filter_options.status:
            filtered = [c for c in filtered if c['status'] == filter_options.status.value]
        
        if filter_options.participant_id:
            filtered = [c for c in filtered if filter_options.participant_id in c['participants']]
        
        if filter_options.is_pinned is not None:
            filtered = [c for c in filtered if c['is_pinned'] == filter_options.is_pinned]
        
        return filtered
    
    async def _enrich_conversation_for_user(
        self,
        conversation: Dict,
        user_id: int,
        messages: List[Dict],
        user_settings: Dict
    ) -> Dict:
        """Enrich conversation with user-specific data."""
        # Get conversation messages
        conv_messages = [m for m in messages if m['conversation_id'] == conversation['id']]
        
        # Calculate unread count
        last_read_message_id = user_settings.get('last_read_message_id', 0)
        unread_count = len([m for m in conv_messages if m['id'] > last_read_message_id])
        
        # Add user-specific fields
        enriched = conversation.copy()
        enriched['unread_count'] = unread_count
        enriched['is_muted'] = user_settings.get('is_muted', False)
        enriched['custom_name'] = user_settings.get('custom_name')
        
        # For direct conversations, set other participant info
        if conversation['conversation_type'] == ConversationType.DIRECT.value:
            other_user_id = next(p for p in conversation['participants'] if p != user_id)
            try:
                other_user = await user_service.get_user_by_id(other_user_id)
                if other_user:
                    enriched['other_user'] = {
                        "user_id": other_user.id,
                        "username": other_user.username,
                        "display_name": getattr(other_user, 'display_name', None),
                        "avatar_url": getattr(other_user, 'avatar_url', None)
                    }
            except Exception as e:
                logger.warning(f"Could not get other user info: {e}")
        
        return enriched
    
    # Message Management
    
    async def send_message(
        self,
        user_id: int,
        message_data: MessageCreate
    ) -> Message:
        """Send a new message."""
        try:
            messages = await self._load_messages()
            conversations = await self._load_conversations()
            
            # Determine conversation
            conversation_id = message_data.conversation_id
            
            if not conversation_id and message_data.recipient_id:
                # Create or find direct conversation
                conversation_create = ConversationCreate(
                    participant_ids=[message_data.recipient_id],
                    conversation_type=ConversationType.DIRECT
                )
                conversation = await self.create_conversation(user_id, conversation_create)
                conversation_id = conversation.id
            
            if not conversation_id:
                raise ValueError("Must specify either conversation_id or recipient_id")
            
            # Find conversation
            conversation = next((c for c in conversations if c['id'] == conversation_id), None)
            if not conversation:
                raise ValueError("Conversation not found")
            
            # Check if user is participant
            if user_id not in conversation['participants']:
                raise ValueError("User is not a participant in this conversation")
            
            # Determine recipient for direct messages
            recipient_id = None
            if conversation['conversation_type'] == ConversationType.DIRECT.value:
                recipient_id = next(p for p in conversation['participants'] if p != user_id)
            
            # Create message
            message_dict = {
                "id": self._next_message_id,
                "conversation_id": conversation_id,
                "sender_id": user_id,
                "recipient_id": recipient_id,
                "message_type": message_data.message_type.value,
                "content": message_data.content,
                "attachments": message_data.attachments or [],
                "status": MessageStatus.SENT.value,
                "is_edited": False,
                "edit_count": 0,
                "reactions": {},
                "reply_to_message_id": message_data.reply_to_message_id,
                "thread_count": 0,
                "sent_at": datetime.utcnow().isoformat(),
                "delivered_at": None,
                "read_at": None,
                "created_at": datetime.utcnow().isoformat(),
                "updated_at": None,
                "deleted_at": None,
                "expires_at": message_data.expires_at.isoformat() if message_data.expires_at else None,
                "system_data": message_data.system_data
            }
            
            messages.append(message_dict)
            await self._save_messages(messages)
            
            # Update conversation
            conversation['total_messages'] += 1
            conversation['last_message_id'] = self._next_message_id
            conversation['last_message_at'] = message_dict['created_at']
            conversation['updated_at'] = datetime.utcnow().isoformat()
            
            # Update thread count if this is a reply
            if message_data.reply_to_message_id:
                await self._update_thread_count(message_data.reply_to_message_id)
            
            await self._save_conversations(conversations)
            
            self._next_message_id += 1
            
            # Mark message as delivered for direct messages
            if recipient_id:
                await self._update_message_status(message_dict['id'], MessageStatus.DELIVERED)
            
            # Send notifications (would be implemented with real notification system)
            await self._send_message_notifications(message_dict, conversation)
            
            logger.info(f"Sent message {message_dict['id']} in conversation {conversation_id}")
            return Message(**message_dict)
            
        except Exception as e:
            logger.error(f"Error sending message: {e}")
            raise
    
    async def get_conversation_messages(
        self,
        user_id: int,
        conversation_id: int,
        skip: int = 0,
        limit: int = 50
    ) -> MessageListResponse:
        """Get messages from a conversation."""
        try:
            messages = await self._load_messages()
            conversations = await self._load_conversations()
            reactions = await self._load_reactions()
            
            # Find conversation
            conversation = next((c for c in conversations if c['id'] == conversation_id), None)
            if not conversation:
                raise ValueError("Conversation not found")
            
            # Check if user is participant
            if user_id not in conversation['participants']:
                raise ValueError("User is not a participant in this conversation")
            
            # Get conversation messages
            conv_messages = [
                m for m in messages
                if m['conversation_id'] == conversation_id and not m.get('deleted_at')
            ]
            
            # Sort by creation time (oldest first for messages)
            conv_messages.sort(key=lambda x: x['created_at'])
            
            # Apply pagination
            total_count = len(conv_messages)
            paginated_messages = conv_messages[skip:skip + limit]
            
            # Enrich messages with reactions and user context
            enriched_messages = []
            for message in paginated_messages:
                enriched_message = await self._enrich_message_with_reactions(message, user_id, reactions)
                enriched_messages.append(Message(**enriched_message))
            
            # Mark messages as read
            await self._mark_messages_as_read(user_id, conversation_id, [m.id for m in enriched_messages])
            
            # Count unread messages
            settings = await self._load_settings()
            user_settings = next((
                s for s in settings
                if s['conversation_id'] == conversation_id and s['user_id'] == user_id
            ), {})
            
            last_read_message_id = user_settings.get('last_read_message_id', 0)
            unread_count = len([m for m in conv_messages if m['id'] > last_read_message_id])
            
            return MessageListResponse(
                messages=enriched_messages,
                total_count=total_count,
                unread_count=unread_count,
                page=skip // limit + 1,
                page_size=limit,
                has_next=skip + limit < total_count,
                has_previous=skip > 0,
                conversation=Conversation(**conversation)
            )
            
        except Exception as e:
            logger.error(f"Error getting conversation messages: {e}")
            raise
    
    async def _enrich_message_with_reactions(
        self,
        message: Dict,
        user_id: int,
        reactions: List[Dict]
    ) -> Dict:
        """Enrich message with reaction data."""
        message_reactions = [r for r in reactions if r['message_id'] == message['id']]
        
        # Group reactions by emoji
        reaction_groups = defaultdict(list)
        for reaction in message_reactions:
            reaction_groups[reaction['emoji']].append(reaction['user_id'])
        
        # Check if current user has reacted
        user_reaction = next((r['emoji'] for r in message_reactions if r['user_id'] == user_id), None)
        
        # Update message with reaction data
        enriched = message.copy()
        enriched['reactions'] = dict(reaction_groups)
        enriched['user_reaction'] = user_reaction
        enriched['total_reactions'] = len(message_reactions)
        
        return enriched
    
    async def _update_thread_count(self, parent_message_id: int):
        """Update thread count for a parent message."""
        try:
            messages = await self._load_messages()
            
            # Find parent message
            parent_index = next((i for i, m in enumerate(messages) if m['id'] == parent_message_id), None)
            if parent_index is None:
                return
            
            # Count replies
            reply_count = sum(1 for m in messages if m.get('reply_to_message_id') == parent_message_id)
            
            # Update parent message
            messages[parent_index]['thread_count'] = reply_count
            messages[parent_index]['updated_at'] = datetime.utcnow().isoformat()
            
            await self._save_messages(messages)
            
        except Exception as e:
            logger.error(f"Error updating thread count: {e}")
    
    async def _update_message_status(self, message_id: int, status: MessageStatus):
        """Update message status."""
        try:
            messages = await self._load_messages()
            
            # Find message
            message_index = next((i for i, m in enumerate(messages) if m['id'] == message_id), None)
            if message_index is None:
                return
            
            # Update status
            messages[message_index]['status'] = status.value
            
            if status == MessageStatus.DELIVERED:
                messages[message_index]['delivered_at'] = datetime.utcnow().isoformat()
            elif status == MessageStatus.READ:
                messages[message_index]['read_at'] = datetime.utcnow().isoformat()
            
            messages[message_index]['updated_at'] = datetime.utcnow().isoformat()
            
            await self._save_messages(messages)
            
        except Exception as e:
            logger.error(f"Error updating message status: {e}")
    
    async def _mark_messages_as_read(self, user_id: int, conversation_id: int, message_ids: List[int]):
        """Mark messages as read for a user."""
        try:
            settings = await self._load_settings()
            
            # Find or create user settings for conversation
            settings_index = next((
                i for i, s in enumerate(settings)
                if s['conversation_id'] == conversation_id and s['user_id'] == user_id
            ), None)
            
            if settings_index is None:
                # Create new settings
                new_settings = {
                    "conversation_id": conversation_id,
                    "user_id": user_id,
                    "is_muted": False,
                    "notifications_enabled": True,
                    "custom_name": None,
                    "is_archived": False,
                    "last_read_message_id": max(message_ids) if message_ids else 0,
                    "last_read_at": datetime.utcnow().isoformat()
                }
                settings.append(new_settings)
            else:
                # Update existing settings
                if message_ids:
                    current_last_read = settings[settings_index].get('last_read_message_id', 0)
                    settings[settings_index]['last_read_message_id'] = max(current_last_read, max(message_ids))
                    settings[settings_index]['last_read_at'] = datetime.utcnow().isoformat()
            
            await self._save_settings(settings)
            
            # Update message status to READ
            for message_id in message_ids:
                await self._update_message_status(message_id, MessageStatus.READ)
            
        except Exception as e:
            logger.error(f"Error marking messages as read: {e}")
    
    # Message Reactions
    
    async def add_message_reaction(
        self,
        user_id: int,
        message_id: int,
        reaction_data: MessageReactionCreate
    ) -> MessageReaction:
        """Add a reaction to a message."""
        try:
            messages = await self._load_messages()
            reactions = await self._load_reactions()
            
            # Find message
            message = next((m for m in messages if m['id'] == message_id), None)
            if not message:
                raise ValueError("Message not found")
            
            # Check if user can access this message
            if not await self._can_user_access_message(user_id, message):
                raise ValueError("Message not accessible")
            
            # Check if user already reacted with this emoji
            existing_reaction = next((
                r for r in reactions
                if r['message_id'] == message_id and r['user_id'] == user_id and r['emoji'] == reaction_data.emoji
            ), None)
            
            if existing_reaction:
                return MessageReaction(**existing_reaction)
            
            # Remove any existing reaction from this user
            reactions = [
                r for r in reactions
                if not (r['message_id'] == message_id and r['user_id'] == user_id)
            ]
            
            # Add new reaction
            reaction_dict = {
                "id": self._next_reaction_id,
                "message_id": message_id,
                "user_id": user_id,
                "emoji": reaction_data.emoji,
                "created_at": datetime.utcnow().isoformat()
            }
            
            reactions.append(reaction_dict)
            await self._save_reactions(reactions)
            
            self._next_reaction_id += 1
            
            logger.info(f"Added reaction {reaction_data.emoji} to message {message_id} by user {user_id}")
            return MessageReaction(**reaction_dict)
            
        except Exception as e:
            logger.error(f"Error adding message reaction: {e}")
            raise
    
    async def remove_message_reaction(self, user_id: int, message_id: int) -> bool:
        """Remove user's reaction from a message."""
        try:
            reactions = await self._load_reactions()
            
            # Find and remove user's reaction
            original_count = len(reactions)
            reactions = [
                r for r in reactions
                if not (r['message_id'] == message_id and r['user_id'] == user_id)
            ]
            
            if len(reactions) == original_count:
                return False  # No reaction found
            
            await self._save_reactions(reactions)
            
            logger.info(f"Removed reaction from message {message_id} by user {user_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error removing message reaction: {e}")
            return False
    
    async def _can_user_access_message(self, user_id: int, message: Dict) -> bool:
        """Check if user can access a message."""
        try:
            conversations = await self._load_conversations()
            
            # Find conversation
            conversation = next((c for c in conversations if c['id'] == message['conversation_id']), None)
            if not conversation:
                return False
            
            # Check if user is participant
            return user_id in conversation['participants']
            
        except Exception as e:
            logger.error(f"Error checking message access: {e}")
            return False
    
    # Conversation Settings
    
    async def get_conversation_settings(self, user_id: int, conversation_id: int) -> Optional[ConversationSettings]:
        """Get user's settings for a conversation."""
        try:
            settings = await self._load_settings()
            
            user_settings = next((
                s for s in settings
                if s['conversation_id'] == conversation_id and s['user_id'] == user_id
            ), None)
            
            if not user_settings:
                # Create default settings
                return await self.create_default_conversation_settings(user_id, conversation_id)
            
            return ConversationSettings(**user_settings)
            
        except Exception as e:
            logger.error(f"Error getting conversation settings: {e}")
            return None
    
    async def create_default_conversation_settings(self, user_id: int, conversation_id: int) -> ConversationSettings:
        """Create default conversation settings for a user."""
        try:
            settings = await self._load_settings()
            
            default_settings = {
                "conversation_id": conversation_id,
                "user_id": user_id,
                "is_muted": False,
                "notifications_enabled": True,
                "custom_name": None,
                "is_archived": False,
                "last_read_message_id": None,
                "last_read_at": None
            }
            
            settings.append(default_settings)
            await self._save_settings(settings)
            
            return ConversationSettings(**default_settings)
            
        except Exception as e:
            logger.error(f"Error creating default conversation settings: {e}")
            raise
    
    async def update_conversation_settings(
        self,
        user_id: int,
        conversation_id: int,
        settings_update: ConversationSettingsUpdate
    ) -> Optional[ConversationSettings]:
        """Update user's conversation settings."""
        try:
            settings = await self._load_settings()
            
            # Find user's settings
            settings_index = next((
                i for i, s in enumerate(settings)
                if s['conversation_id'] == conversation_id and s['user_id'] == user_id
            ), None)
            
            if settings_index is None:
                # Create default settings first
                await self.create_default_conversation_settings(user_id, conversation_id)
                settings = await self._load_settings()
                settings_index = next((
                    i for i, s in enumerate(settings)
                    if s['conversation_id'] == conversation_id and s['user_id'] == user_id
                ), None)
            
            # Update settings
            update_dict = settings_update.dict(exclude_unset=True)
            settings[settings_index].update(update_dict)
            
            await self._save_settings(settings)
            
            return ConversationSettings(**settings[settings_index])
            
        except Exception as e:
            logger.error(f"Error updating conversation settings: {e}")
            return None
    
    # Messaging Statistics
    
    async def get_user_messaging_stats(self, user_id: int) -> MessageStats:
        """Get comprehensive messaging statistics for a user."""
        try:
            messages = await self._load_messages()
            conversations = await self._load_conversations()
            reactions = await self._load_reactions()
            
            # Filter user's messages
            sent_messages = [m for m in messages if m['sender_id'] == user_id]
            received_messages = [m for m in messages if m.get('recipient_id') == user_id]
            
            # Filter user's conversations
            user_conversations = [c for c in conversations if user_id in c['participants']]
            active_conversations = [c for c in user_conversations if c['status'] == ConversationStatus.ACTIVE.value]
            
            # Time-based stats
            now = datetime.utcnow()
            today = now.replace(hour=0, minute=0, second=0, microsecond=0)
            week_ago = now - timedelta(days=7)
            month_ago = now - timedelta(days=30)
            
            messages_today = len([
                m for m in sent_messages
                if datetime.fromisoformat(m['created_at']) >= today
            ])
            
            messages_this_week = len([
                m for m in sent_messages
                if datetime.fromisoformat(m['created_at']) >= week_ago
            ])
            
            messages_this_month = len([
                m for m in sent_messages
                if datetime.fromisoformat(m['created_at']) >= month_ago
            ])
            
            # Message type breakdown
            messages_by_type = defaultdict(int)
            for message in sent_messages:
                messages_by_type[message['message_type']] += 1
            
            # Reaction stats
            user_reactions = [r for r in reactions if r['user_id'] == user_id]
            favorite_emoji_reactions = [
                emoji for emoji, count in Counter(r['emoji'] for r in user_reactions).most_common(5)
            ]
            
            # Response time calculation (simplified)
            response_times = []
            for conv in user_conversations:
                conv_messages = [m for m in messages if m['conversation_id'] == conv['id']]
                conv_messages.sort(key=lambda x: x['created_at'])
                
                for i in range(1, len(conv_messages)):
                    prev_msg = conv_messages[i-1]
                    curr_msg = conv_messages[i]
                    
                    if prev_msg['sender_id'] != user_id and curr_msg['sender_id'] == user_id:
                        prev_time = datetime.fromisoformat(prev_msg['created_at'])
                        curr_time = datetime.fromisoformat(curr_msg['created_at'])
                        response_time = (curr_time - prev_time).total_seconds() / 60  # minutes
                        response_times.append(response_time)
            
            avg_response_time = sum(response_times) / len(response_times) if response_times else 0
            
            # Most active conversation
            conv_message_counts = defaultdict(int)
            for message in sent_messages:
                conv_message_counts[message['conversation_id']] += 1
            
            most_active_conversation_id = max(conv_message_counts.items(), key=lambda x: x[1])[0] if conv_message_counts else None
            
            return MessageStats(
                total_messages_sent=len(sent_messages),
                total_messages_received=len(received_messages),
                total_conversations=len(user_conversations),
                active_conversations=len(active_conversations),
                messages_today=messages_today,
                messages_this_week=messages_this_week,
                messages_this_month=messages_this_month,
                average_response_time_minutes=round(avg_response_time, 2),
                most_active_conversation_id=most_active_conversation_id,
                favorite_emoji_reactions=favorite_emoji_reactions,
                messages_by_type=dict(messages_by_type),
                most_messaged_friend=None,  # Would analyze friend messaging patterns
                longest_conversation_days=None  # Would calculate conversation duration
            )
            
        except Exception as e:
            logger.error(f"Error getting messaging stats: {e}")
            raise
    
    # Notification helpers
    
    async def _send_message_notifications(self, message: Dict, conversation: Dict):
        """Send notifications for new message."""
        try:
            # Get conversation participants except sender
            recipients = [p for p in conversation['participants'] if p != message['sender_id']]
            
            for recipient_id in recipients:
                # Check if notifications are enabled for this user/conversation
                settings = await self.get_conversation_settings(recipient_id, conversation['id'])
                
                if settings and settings.notifications_enabled and not settings.is_muted:
                    # In a real implementation, this would send actual notifications
                    logger.info(f"Would notify user {recipient_id} about message {message['id']}")
            
        except Exception as e:
            logger.error(f"Error sending message notifications: {e}")


# Global service instance
messaging_service = MessagingService() 