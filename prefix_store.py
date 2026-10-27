import os
import sqlite3
from contextlib import closing
from constants import DEFAULT_PREFIX


# Command prefixes per guild, kept in the SQLite settings table (the same schema the ai_test branch used, so either
# version can run against the same marcie.db) and cached in memory so lookups don't touch the database.

class PrefixStore:
    def __init__(self, path):
        self.path = path
        self.prefixes = {}

    def _execute(self, sql, params=()):
        with closing(sqlite3.connect(self.path)) as conn, conn:
            return conn.execute(sql, params).fetchall()

    def load(self):
        os.makedirs(os.path.dirname(self.path) or '.', exist_ok=True)

        self._execute(f'''
            CREATE TABLE IF NOT EXISTS settings (
                guildid INTEGER PRIMARY KEY,
                prefix TEXT NOT NULL DEFAULT '{DEFAULT_PREFIX}',
                name TEXT NOT NULL
            )
        ''')
        self.prefixes = dict(self._execute("SELECT guildid, prefix FROM settings"))

        return self

    def get(self, guildid):
        return self.prefixes.get(guildid, DEFAULT_PREFIX)

    # Adds a guild with the default prefix, keeping its current prefix if it already has a row
    def add(self, guildid, name):
        self._execute("INSERT INTO settings (guildid, prefix, name) VALUES (?, ?, ?) "
                      "ON CONFLICT(guildid) DO UPDATE SET name = excluded.name", (guildid, DEFAULT_PREFIX, name))
        self.prefixes.setdefault(guildid, DEFAULT_PREFIX)

    def set(self, guildid, prefix, name):
        self._execute("INSERT INTO settings (guildid, prefix, name) VALUES (?, ?, ?) "
                      "ON CONFLICT(guildid) DO UPDATE SET prefix = excluded.prefix, name = excluded.name",
                      (guildid, prefix, name))
        self.prefixes[guildid] = prefix

    def remove(self, guildid):
        self._execute("DELETE FROM settings WHERE guildid = ?", (guildid,))
        self.prefixes.pop(guildid, None)
