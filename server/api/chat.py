import json
from typing import List
from fastapi import HTTPException, Depends
from fastapi.responses import StreamingResponse
import os
from anthropic import Anthropic
from api import api
from models.bigtable_chat import BigtableChatService
from models.chat import Chat, ChatMessage, ChatCreate, ChatMessageCreate
from auth import get_current_user

client = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
chat_service = BigtableChatService()


@api.get("/chats", response_model=List[dict], operation_id="chat_all")
async def get_chats(current_user=Depends(get_current_user)):
    """Get list of chats (id and title only) for the current user"""
    chats = chat_service.get_chats_by_user_id(current_user.id)
    return [{"id": chat.id, "title": chat.title} for chat in chats]


@api.get("/chats/{chat_id}", operation_id="chat_by_id")
async def get_chat_with_messages(chat_id: str, current_user=Depends(get_current_user)):
    """Get a specific chat and all of its messages"""
    chat = chat_service.get_chat_by_id(chat_id)
    if not chat or chat.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Chat not found")

    messages = chat_service.get_messages_by_chat_id(chat_id)
    return {"chat": chat, "messages": messages}


@api.post("/chats/{chat_id}", operation_id="chat_message")
async def send_message_to_chat(
    chat_id: str, request: dict, current_user=Depends(get_current_user)
):
    """Send a message to a chat. Creates chat if it doesn't exist, otherwise appends to existing chat."""
    user_message = request.get("message", "")
    if not user_message.strip():
        raise HTTPException(status_code=400, detail="Message cannot be empty")

    # Check if chat exists
    chat = chat_service.get_chat_by_id(chat_id)

    if chat:
        # Chat exists - verify ownership
        if chat.user_id != current_user.id:
            raise HTTPException(status_code=403, detail="Access denied")

        # Get conversation history for existing chat
        messages = chat_service.get_messages_by_chat_id(chat_id)
        conversation_history = []
        for msg in messages:
            role = "user" if msg.message_type == "user" else "assistant"
            conversation_history.append({"role": role, "content": msg.content})

        # Add current message to history
        conversation_history.append({"role": "user", "content": user_message})

        is_new_chat = False
    else:
        # Chat doesn't exist - create new one
        title = request.get(
            "title",
            user_message[:50] + "..." if len(user_message) > 50 else user_message,
        )
        chat = chat_service.create_chat(
            title=title, user_id=current_user.id, chat_id=chat_id
        )
        conversation_history = [{"role": "user", "content": user_message}]
        is_new_chat = True

    # Create user message
    chat_service.create_message(
        chat_id=chat.id,
        user_id=current_user.id,
        message_type="user",
        content=user_message,
    )

    def generate():
        if is_new_chat:
            yield json.dumps({"chat_id": chat.id, "type": "chat_created"}) + "\n"

        with client.messages.stream(
            model="claude-sonnet-4-20250514",
            max_tokens=1024,
            messages=conversation_history,
        ) as stream:
            assistant_content = ""
            for text in stream.text_stream:
                assistant_content += text
                yield json.dumps({"content": text, "type": "content"}) + "\n"

        # Save assistant response
        chat_service.create_message(
            chat_id=chat.id,
            user_id=current_user.id,
            message_type="assistant",
            content=assistant_content,
            model="claude-sonnet-4-20250514",
        )

        yield json.dumps({"type": "done"}) + "\n"

    return StreamingResponse(generate(), media_type="application/x-ndjson")
