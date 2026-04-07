"""
Migration script to update token item IDs in inventory.
Changes:
- token_uncommon_roll -> uncommon
- token_rare_roll -> rare
- token_epic_roll -> epic
"""

from sqlalchemy import text

from src.database.db import get_session


def migrate_token_ids():
    updates = [
        ("token_uncommon_roll", "uncommon"),
        ("token_rare_roll", "rare"),
        ("token_epic_roll", "epic"),
    ]

    with get_session() as session:
        try:
            for old_id, new_id in updates:
                session.execute(
                    text(
                        """
                        UPDATE inventory
                        SET item_id = :new_id
                        WHERE item_id = :old_id
                        """
                    ),
                    {"new_id": new_id, "old_id": old_id},
                )

            session.commit()
            print("Token item IDs migrated successfully.")
        except Exception:
            session.rollback()
            raise


if __name__ == "__main__":
    migrate_token_ids()
