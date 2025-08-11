import os
from google.cloud import bigtable
from typing import Optional

PROJECT_ID = os.getenv("GOOGLE_CLOUD_PROJECT")
BIGTABLE_INSTANCE_ID = os.getenv("BIGTABLE_INSTANCE_ID", "chatssi-csdb")
BIGTABLE_TABLE_ID = os.getenv("BIGTABLE_TABLE_ID", "users")

if not PROJECT_ID:
    raise ValueError("GOOGLE_CLOUD_PROJECT environment variable must be set")

# Initialize Bigtable client
client = bigtable.Client(project=PROJECT_ID)
instance = client.instance(BIGTABLE_INSTANCE_ID)
table = instance.table(BIGTABLE_TABLE_ID)

# Column family names
USER_DATA_FAMILY = "user_data"
METADATA_FAMILY = "metadata"


def get_bigtable_client():
    """Get Bigtable client instance"""
    return client


def get_users_table():
    """Get users table instance"""
    return table


async def ensure_table_exists():
    """Ensure the users table and column families exist"""
    try:
        # Use admin client for table operations
        admin_client = bigtable.Client(project=PROJECT_ID, admin=True)
        admin_instance = admin_client.instance(BIGTABLE_INSTANCE_ID)
        admin_table = admin_instance.table(BIGTABLE_TABLE_ID)

        if not admin_table.exists():
            # Create table with column families
            from google.cloud.bigtable import column_family

            # Create column families with max versions = 1
            user_data_cf = column_family.MaxVersionsGCRule(1)
            metadata_cf = column_family.MaxVersionsGCRule(1)

            column_families = {
                USER_DATA_FAMILY: user_data_cf,
                METADATA_FAMILY: metadata_cf,
            }

            admin_table.create(column_families=column_families)
            print(f"Created Bigtable table '{BIGTABLE_TABLE_ID}'")
        else:
            print(f"Bigtable table '{BIGTABLE_TABLE_ID}' already exists")

    except Exception as e:
        print(f"Error ensuring table exists: {e}")
        # Don't raise - allow app to continue if table creation fails
        # The table might already exist or need to be created manually
