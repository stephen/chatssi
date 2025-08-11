from .user import User, UserSchema, UserCreate
from .chat import Chat, ChatSchema, ChatCreate, ChatMessage, ChatMessageSchema, ChatMessageCreate
from .bigtable_user import BigtableUserService
from .bigtable_chat import BigtableChatService

# For backward compatibility during migration
get_db = lambda: BigtableUserService()
get_chat_db = lambda: BigtableChatService()