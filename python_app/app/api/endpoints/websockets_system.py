import json
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends
from pydantic import ValidationError
from datetime import datetime
from typing import Optional

from app.services.websockets_manager import manager
from app.api.dependencies import get_current_user_from_token
from app.models.websockets_system import (
    ClientMessage,
    ServerMessage,
    WebSocketMessageType,
    AuthenticatePayload,
    SubscriptionPayload,
    ChatMessagePayload,
    AuthenticationStatusPayload,
    SubscriptionStatusPayload,
    SystemMessagePayload,
    ChatMessageBroadcastPayload
)
from app.db.database import get_db_session

router = APIRouter()

async def send_error(websocket: WebSocket, message: str, request_id: Optional[str] = None):
    error_payload = SystemMessagePayload(message=message, level="error")
    server_message = ServerMessage(type=WebSocketMessageType.ERROR, payload=error_payload.dict(), request_id=request_id)
    await websocket.send_text(server_message.json())

@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    # This connection is not yet authenticated
    user = None
    
    await websocket.accept()

    try:
        while True:
            data = await websocket.receive_text()
            
            try:
                client_message = ClientMessage.parse_raw(data)
                request_id = client_message.request_id
                
                # --- Handle Authentication ---
                if client_message.type == WebSocketMessageType.AUTHENTICATE:
                    if user:
                        await send_error(websocket, "Already authenticated.", request_id)
                        continue
                    
                    try:
                        auth_payload = AuthenticatePayload(**client_message.payload)
                        async with get_db_session() as db:
                            # This is a simplified auth flow. In a real app, you might have more robust validation.
                            user = await get_current_user_from_token(token=auth_payload.token, db=db)
                        
                        if user:
                            await manager.connect(websocket, user.id)
                            auth_status = AuthenticationStatusPayload(success=True, user_id=user.id)
                            response = ServerMessage(type=WebSocketMessageType.AUTHENTICATION_STATUS, payload=auth_status.dict(), request_id=request_id)
                            await websocket.send_text(response.json())
                        else:
                            raise ValueError("Invalid token")
                    
                    except (ValidationError, ValueError) as e:
                        auth_status = AuthenticationStatusPayload(success=False, error=str(e))
                        response = ServerMessage(type=WebSocketMessageType.AUTHENTICATION_STATUS, payload=auth_status.dict(), request_id=request_id)
                        await websocket.send_text(response.json())
                        await websocket.close(code=4001)
                        return

                # --- Routes requiring authentication ---
                elif not user:
                    await send_error(websocket, "Authentication required.", request_id)
                    continue

                elif client_message.type == WebSocketMessageType.SUBSCRIBE:
                    try:
                        sub_payload = SubscriptionPayload(**client_message.payload)
                        # Here you would add logic to verify if the user can subscribe to this channel
                        success = manager.subscribe(user.id, sub_payload.channel)
                        sub_status = SubscriptionStatusPayload(channel=sub_payload.channel, success=success)
                        response = ServerMessage(type=WebSocketMessageType.SUBSCRIPTION_STATUS, payload=sub_status.dict(), request_id=request_id)
                        await websocket.send_text(response.json())
                    except ValidationError as e:
                        await send_error(websocket, f"Invalid subscription payload: {e}", request_id)
                
                elif client_message.type == WebSocketMessageType.UNSUBSCRIBE:
                    # Implementation for unsubscribe...
                    pass
                
                elif client_message.type == WebSocketMessageType.SEND_MESSAGE:
                    try:
                        chat_payload = ChatMessagePayload(**client_message.payload)
                        # In a real app, you'd verify the user is in the chat room
                        broadcast_payload = ChatMessageBroadcastPayload(
                            room_id=chat_payload.room_id,
                            sender_id=user.id,
                            sender_username=user.username,
                            text=chat_payload.text,
                            timestamp=datetime.utcnow().isoformat()
                        )
                        response = ServerMessage(type=WebSocketMessageType.CHAT_MESSAGE, payload=broadcast_payload.dict())
                        channel = f"chat:{chat_payload.room_id}"
                        await manager.broadcast_to_channel(response.json(), channel)
                    except ValidationError as e:
                        await send_error(websocket, f"Invalid chat payload: {e}", request_id)
                        
                else:
                    await send_error(websocket, f"Unknown message type: {client_message.type}", request_id)

            except ValidationError as e:
                await send_error(websocket, f"Invalid message format: {e}")
            except Exception as e:
                await send_error(websocket, f"An unexpected error occurred: {e}")

    except WebSocketDisconnect:
        if user:
            manager.disconnect(websocket, user.id)
            print(f"User {user.id}'s connection closed.")
    except Exception as e:
        print(f"Unhandled exception in WebSocket: {e}")
        if user:
            manager.disconnect(websocket, user.id)
        # Ensure the connection is closed on error
        if not websocket.client_state == 'DISCONNECTED':
            await websocket.close() 