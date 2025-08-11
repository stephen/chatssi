import json
from datetime import datetime
from typing import Optional, List, Dict, Any
from google.cloud.bigtable.row import DirectRow
from google.cloud.bigtable.row_filters import FamilyNameRegexFilter, ColumnQualifierRegexFilter
from bigtable_client import get_users_table, CHAT_DATA_FAMILY, MESSAGE_DATA_FAMILY, METADATA_FAMILY
from .chat import Chat, ChatMessage

class BigtableChatService:
    """Service class for chat operations with Bigtable"""
    
    def __init__(self):
        self.table = get_users_table()
    
    def _row_to_chat(self, row_key: str, row_data: Dict[str, Any]) -> Chat:
        """Convert Bigtable row data to Chat object"""
        chat_data = {}
        
        # Parse row data similar to user parsing
        for full_column_name, cell_list in row_data.items():
            if isinstance(full_column_name, bytes):
                full_column_name = full_column_name.decode('utf-8')
            
            if cell_list and isinstance(cell_list, list) and cell_list:
                cell = cell_list[0]
                value = cell.value
                if isinstance(value, bytes):
                    value = value.decode('utf-8')
                
                clean_column = full_column_name.split(':')[-1]
                chat_data[clean_column] = value
        
        # Parse datetime fields
        if "created_at" in chat_data:
            chat_data["created_at"] = datetime.fromisoformat(chat_data["created_at"])
        if "updated_at" in chat_data and chat_data["updated_at"]:
            chat_data["updated_at"] = datetime.fromisoformat(chat_data["updated_at"])
        
        # Convert row key to chat ID
        chat_data["id"] = row_key.replace("chat#", "")
        
        return Chat(**chat_data)
    
    def _row_to_message(self, row_key: str, row_data: Dict[str, Any]) -> ChatMessage:
        """Convert Bigtable row data to ChatMessage object"""
        message_data = {}
        
        # Parse row data
        for full_column_name, cell_list in row_data.items():
            if isinstance(full_column_name, bytes):
                full_column_name = full_column_name.decode('utf-8')
            
            if cell_list and isinstance(cell_list, list) and cell_list:
                cell = cell_list[0]
                value = cell.value
                if isinstance(value, bytes):
                    value = value.decode('utf-8')
                
                clean_column = full_column_name.split(':')[-1]
                message_data[clean_column] = value
        
        # Parse datetime fields
        if "created_at" in message_data:
            message_data["created_at"] = datetime.fromisoformat(message_data["created_at"])
        
        # Parse integer fields
        if "tokens_used" in message_data and message_data["tokens_used"]:
            message_data["tokens_used"] = int(message_data["tokens_used"])
        
        # Convert row key to message ID
        message_data["id"] = int(row_key.replace("message#", ""))
        
        return ChatMessage(**message_data)
    
    def create_chat(self, title: str, user_id: int, chat_id: str = None) -> Chat:
        """Create a new chat with optional client-provided ID"""
        if chat_id is None:
            import time
            chat_id = str(int(time.time() * 1000000))  # microsecond timestamp as string
        
        row_key = f"chat#{chat_id}"
        row = self.table.direct_row(row_key)
        
        now = datetime.utcnow().isoformat()
        
        # Set chat data
        row.set_cell(CHAT_DATA_FAMILY, "title", title)
        row.set_cell(CHAT_DATA_FAMILY, "user_id", str(user_id))
        
        # Set metadata
        row.set_cell(METADATA_FAMILY, "created_at", now)
        row.set_cell(METADATA_FAMILY, "updated_at", now)
        
        # Write to Bigtable
        row.commit()
        
        return Chat(
            id=chat_id,
            title=title,
            user_id=user_id,
            created_at=datetime.fromisoformat(now),
            updated_at=datetime.fromisoformat(now)
        )
    
    def get_chat_by_id(self, chat_id: str) -> Optional[Chat]:
        """Get chat by ID"""
        row_key = f"chat#{chat_id}"
        row = self.table.read_row(row_key)
        
        if row:
            return self._row_to_chat(row_key, row.to_dict())
        return None
    
    def get_chats_by_user_id(self, user_id: int) -> List[Chat]:
        """Get all chats for a user"""
        # This is a scan operation - in production you might want secondary indexes
        row_filter = FamilyNameRegexFilter(f"{CHAT_DATA_FAMILY}")
        rows = self.table.read_rows(filter_=row_filter)
        
        chats = []
        for row_key, row_data in rows.rows.items():
            if row_key.decode('utf-8').startswith('chat#'):
                user_data = row_data.to_dict()
                # Check if this chat belongs to the user
                user_id_cells = user_data.get(b'chat_data:user_id', [])
                if user_id_cells and int(user_id_cells[0].value.decode('utf-8')) == user_id:
                    chats.append(self._row_to_chat(row_key.decode('utf-8'), user_data))
        
        # Sort by created_at descending
        chats.sort(key=lambda x: x.created_at, reverse=True)
        return chats
    
    def update_chat(self, chat_id: str, title: Optional[str] = None) -> Optional[Chat]:
        """Update chat information"""
        row_key = f"chat#{chat_id}"
        row = self.table.direct_row(row_key)
        
        # Check if chat exists
        existing_row = self.table.read_row(row_key)
        if not existing_row:
            return None
        
        now = datetime.utcnow().isoformat()
        
        # Update provided fields
        if title is not None:
            row.set_cell(CHAT_DATA_FAMILY, "title", title)
        
        # Update timestamp
        row.set_cell(METADATA_FAMILY, "updated_at", now)
        
        # Write to Bigtable
        row.commit()
        
        return self.get_chat_by_id(chat_id)
    
    def create_message(self, chat_id: str, user_id: int, message_type: str, content: str, 
                      tokens_used: Optional[int] = None, model: Optional[str] = None) -> ChatMessage:
        """Create a new chat message"""
        import time
        message_id = int(time.time() * 1000000)  # microsecond timestamp
        
        row_key = f"message#{message_id}"
        row = self.table.direct_row(row_key)
        
        now = datetime.utcnow().isoformat()
        
        # Set message data
        row.set_cell(MESSAGE_DATA_FAMILY, "chat_id", chat_id)
        row.set_cell(MESSAGE_DATA_FAMILY, "user_id", str(user_id))
        row.set_cell(MESSAGE_DATA_FAMILY, "message_type", message_type)
        row.set_cell(MESSAGE_DATA_FAMILY, "content", content)
        
        if tokens_used is not None:
            row.set_cell(MESSAGE_DATA_FAMILY, "tokens_used", str(tokens_used))
        if model is not None:
            row.set_cell(MESSAGE_DATA_FAMILY, "model", model)
        
        # Set metadata
        row.set_cell(METADATA_FAMILY, "created_at", now)
        
        # Write to Bigtable
        row.commit()
        
        # Update chat's updated_at timestamp
        self.update_chat(chat_id)
        
        return ChatMessage(
            id=message_id,
            chat_id=chat_id,
            user_id=user_id,
            message_type=message_type,
            content=content,
            tokens_used=tokens_used,
            model=model,
            created_at=datetime.fromisoformat(now)
        )
    
    def get_messages_by_chat_id(self, chat_id: str) -> List[ChatMessage]:
        """Get all messages for a chat"""
        row_filter = FamilyNameRegexFilter(f"{MESSAGE_DATA_FAMILY}")
        rows = self.table.read_rows(filter_=row_filter)
        
        messages = []
        for row_key, row_data in rows.rows.items():
            if row_key.decode('utf-8').startswith('message#'):
                message_data = row_data.to_dict()
                # Check if this message belongs to the chat
                chat_id_cells = message_data.get(b'message_data:chat_id', [])
                if chat_id_cells and chat_id_cells[0].value.decode('utf-8') == chat_id:
                    messages.append(self._row_to_message(row_key.decode('utf-8'), message_data))
        
        # Sort by created_at ascending (chronological order)
        messages.sort(key=lambda x: x.created_at)
        return messages