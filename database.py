"""Database utility functions for SQLite operations."""

import sqlite3
from typing import Optional, Dict, Any, List
from config import get_config


class DatabaseManager:
    """Manager class for SQLite database operations."""
    
    def __init__(self):
        self.config = get_config()
    
    def _get_connection(self) -> sqlite3.Connection:
        """Get a database connection."""
        return self.config.get_database_connection()
    
    # Settings table operations (equivalent to MongoDB 'settings' collection)
    
    def find_one_setting(self, guildid: int) -> Optional[Dict[str, Any]]:
        """Find one setting by guild ID (equivalent to MongoDB find_one)."""
        with self._get_connection() as conn:
            cursor = conn.execute(
                "SELECT guildid, prefix, name FROM settings WHERE guildid = ?",
                (guildid,)
            )
            row = cursor.fetchone()
            if row:
                return dict(row)  # Convert sqlite3.Row to dict
            return None
    
    def find_all_settings(self) -> List[Dict[str, Any]]:
        """Find all settings (equivalent to MongoDB find)."""
        with self._get_connection() as conn:
            cursor = conn.execute("SELECT guildid, prefix, name FROM settings")
            return [dict(row) for row in cursor.fetchall()]
    
    def delete_one_setting(self, guildid: int) -> bool:
        """Delete one setting by guild ID (equivalent to MongoDB delete_one)."""
        with self._get_connection() as conn:
            cursor = conn.execute("DELETE FROM settings WHERE guildid = ?", (guildid,))
            return cursor.rowcount > 0
    
    def upsert_setting(self, guildid: int, prefix: str = '?', name: str = '') -> None:
        """Insert or update setting (equivalent to MongoDB find_one_and_update with upsert)."""
        with self._get_connection() as conn:
            conn.execute('''
                INSERT OR REPLACE INTO settings (guildid, prefix, name)
                VALUES (?, ?, ?)
            ''', (guildid, prefix, name))
    
    def update_setting_prefix(self, guildid: int, prefix: str) -> bool:
        """Update only the prefix for a guild."""
        with self._get_connection() as conn:
            cursor = conn.execute(
                "UPDATE settings SET prefix = ? WHERE guildid = ?",
                (prefix, guildid)
            )
            return cursor.rowcount > 0


# Global database manager instance
db_manager = DatabaseManager()