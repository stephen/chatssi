import json
from datetime import datetime
from typing import Optional, Dict, Any
from google.cloud.bigtable.row import DirectRow
from google.cloud.bigtable.row_filters import FamilyNameRegexFilter
from bigtable_client import get_users_table, USER_DATA_FAMILY, METADATA_FAMILY
from .user import User


class BigtableUserService:
    """Service class for user operations with Bigtable"""

    def __init__(self):
        self.table = get_users_table()

    def _row_to_user(self, row_key: str, row_data: Dict[str, Any]) -> User:
        """Convert Bigtable row data to User object"""
        user_data = {}
        
        # The row_data has full column names as keys (e.g., b'user_data:name')
        # Each value is a list of Cell objects
        for full_column_name, cell_list in row_data.items():
            if isinstance(full_column_name, bytes):
                full_column_name = full_column_name.decode('utf-8')
            
            if cell_list and isinstance(cell_list, list) and cell_list:
                # Get the most recent cell value
                cell = cell_list[0]
                value = cell.value
                if isinstance(value, bytes):
                    value = value.decode('utf-8')
                
                # Extract just the column name (remove family prefix)
                # e.g., 'user_data:name' -> 'name'
                clean_column = full_column_name.split(':')[-1]
                user_data[clean_column] = value
        
        # Parse datetime fields if they exist
        if "created_at" in user_data:
            user_data["created_at"] = datetime.fromisoformat(user_data["created_at"])
        if "updated_at" in user_data and user_data["updated_at"]:
            user_data["updated_at"] = datetime.fromisoformat(user_data["updated_at"])
        
        # Convert row key to user ID
        user_data["id"] = int(row_key.replace("user#", ""))
        
        return User(**user_data)

    def get_user_by_id(self, user_id: int) -> Optional[User]:
        """Get user by ID"""
        row_key = f"user#{user_id}"
        row = self.table.read_row(row_key)

        if row:
            return self._row_to_user(row_key, row.to_dict())
        return None

    def get_user_by_google_id(self, google_id: str) -> Optional[User]:
        """Get user by Google ID"""
        # Use a filter to find user by google_id
        row_filter = FamilyNameRegexFilter(f"{USER_DATA_FAMILY}")
        rows = self.table.read_rows(filter_=row_filter)

        for row_key, row_data in rows.rows.items():
            user_data = row_data.to_dict()
            # Check if this row has the matching google_id
            google_id_cells = user_data.get(b'user_data:google_id', [])
            if (
                google_id_cells
                and google_id_cells[0].value.decode("utf-8") == google_id
            ):
                return self._row_to_user(row_key, user_data)

        return None

    def get_user_by_email(self, email: str) -> Optional[User]:
        """Get user by email"""
        # Use a filter to find user by email
        row_filter = FamilyNameRegexFilter(f"{USER_DATA_FAMILY}")
        rows = self.table.read_rows(filter_=row_filter)

        for row_key, row_data in rows.rows.items():
            user_data = row_data.to_dict()
            # Check if this row has the matching email
            email_cells = user_data.get(b'user_data:email', [])
            if email_cells and email_cells[0].value.decode("utf-8") == email:
                return self._row_to_user(row_key, user_data)

        return None

    def create_user(
        self, name: str, email: str, google_id: str, picture: Optional[str] = None
    ) -> User:
        """Create a new user"""
        # Generate user ID (in production, use a proper ID generation strategy)
        import time

        user_id = int(time.time() * 1000000)  # microsecond timestamp

        row_key = f"user#{user_id}"
        row = self.table.direct_row(row_key)

        now = datetime.utcnow().isoformat()

        # Set user data - ensure all values are strings and not None
        row.set_cell(USER_DATA_FAMILY, "name", str(name) if name is not None else "")
        row.set_cell(USER_DATA_FAMILY, "email", str(email) if email is not None else "")
        row.set_cell(USER_DATA_FAMILY, "google_id", str(google_id) if google_id is not None else "")
        if picture is not None:
            row.set_cell(USER_DATA_FAMILY, "picture", str(picture))

        # Set metadata
        row.set_cell(METADATA_FAMILY, "created_at", now)
        row.set_cell(METADATA_FAMILY, "updated_at", now)

        # Write to Bigtable
        row.commit()

        return User(
            id=user_id,
            name=name,
            email=email,
            google_id=google_id,
            picture=picture,
            created_at=datetime.fromisoformat(now),
            updated_at=datetime.fromisoformat(now),
        )

    def update_user(
        self, user_id: int, name: Optional[str] = None, picture: Optional[str] = None
    ) -> Optional[User]:
        """Update user information"""
        row_key = f"user#{user_id}"
        row = self.table.direct_row(row_key)

        # Check if user exists
        existing_row = self.table.read_row(row_key)
        if not existing_row:
            return None

        now = datetime.utcnow().isoformat()

        # Update provided fields - ensure values are strings
        if name is not None:
            row.set_cell(USER_DATA_FAMILY, "name", str(name))
        if picture is not None:
            row.set_cell(USER_DATA_FAMILY, "picture", str(picture))

        # Update timestamp
        row.set_cell(METADATA_FAMILY, "updated_at", now)

        # Write to Bigtable
        row.commit()

        # Return updated user
        return self.get_user_by_id(user_id)