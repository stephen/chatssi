from .user import User, UserSchema, UserCreate
from .bigtable_user import BigtableUserService

# For backward compatibility during migration
get_db = lambda: BigtableUserService()