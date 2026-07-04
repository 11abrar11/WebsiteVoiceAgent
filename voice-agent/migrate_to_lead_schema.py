"""
One-time migration script: Drop old UUID-based schema and recreate with
the new lead-centric integer-PK schema.

Usage:
    python migrate_to_lead_schema.py

WARNING: This destroys ALL data in conversations, messages, leads,
         conversation_summaries, and meetings tables.
         The 'admins' table is preserved.

After running this script once, delete it from the repository.
"""
import asyncio
import sys
from sqlalchemy import text
from app.database.connection import engine
from app.database.base import Base

# Import all models so Base.metadata registers them
from app.models.admin import Admin  # noqa: F401
from app.models.lead import Lead  # noqa: F401
from app.models.conversation import Conversation  # noqa: F401
from app.models.message import Message  # noqa: F401
from app.models.conversation_summary import ConversationSummary  # noqa: F401
from app.models.meeting import Meeting  # noqa: F401

# Tables to drop (order matters: children before parents)
TABLES_TO_DROP = [
    "conversation_summaries",
    "messages",
    "meetings",
    "leads",
    "conversations",
]

# Also drop any enum types left behind by the old schema
ENUM_TYPES_TO_DROP = [
    "conversationstatus",
    "meetingstatus",
]


async def migrate():
    print("=" * 60)
    print("  Lead-Centric Schema Migration")
    print("=" * 60)
    print()
    print("This will DROP and RECREATE the following tables:")
    for t in TABLES_TO_DROP:
        print(f"  - {t}")
    print()
    print("The 'admins' table will NOT be touched.")
    print()

    confirm = input("Type 'yes' to proceed: ").strip().lower()
    if confirm != "yes":
        print("Migration cancelled.")
        sys.exit(0)

    async with engine.begin() as conn:
        # Drop old tables (CASCADE handles FK dependencies)
        for table_name in TABLES_TO_DROP:
            await conn.execute(text(f"DROP TABLE IF EXISTS {table_name} CASCADE"))
            print(f"  Dropped: {table_name}")

        # Drop orphaned enum types from old schema
        for enum_type in ENUM_TYPES_TO_DROP:
            await conn.execute(text(f"DROP TYPE IF EXISTS {enum_type} CASCADE"))
            print(f"  Dropped type: {enum_type}")

        # Recreate all tables with new schema
        await conn.run_sync(Base.metadata.create_all)
        print()
        print("  All tables recreated with new schema.")

    await engine.dispose()
    print()
    print("Migration complete. You can now delete this script.")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(migrate())
