import json
import logging
import os
import sqlite3
from constants import DEFAULT_PREFIX


# Custom command prefixes per guild, kept in a small JSON file.  Guilds using the default prefix aren't stored.

class PrefixStore:
    def __init__(self, path):
        self.path = path
        self.prefixes = {}

    def load(self):
        try:
            with open(self.path, encoding='utf-8') as f:
                self.prefixes = {int(guildid): prefix for guildid, prefix in json.load(f).items()}
        except FileNotFoundError:
            self.prefixes = {}

        return self

    def get(self, guildid):
        return self.prefixes.get(guildid, DEFAULT_PREFIX)

    def set(self, guildid, prefix):
        if prefix == DEFAULT_PREFIX:
            self.prefixes.pop(guildid, None)
        else:
            self.prefixes[guildid] = prefix
        self.save()

    def remove(self, guildid):
        if self.prefixes.pop(guildid, None) is not None:
            self.save()

    # Writes to a temp file first so a crash mid-write can't leave a half written prefixes file
    def save(self):
        os.makedirs(os.path.dirname(self.path) or '.', exist_ok=True)

        tmp_path = self.path + '.tmp'
        with open(tmp_path, 'w', encoding='utf-8') as f:
            json.dump({str(guildid): prefix for guildid, prefix in self.prefixes.items()}, f, indent=2)
        os.replace(tmp_path, self.path)

    # One time import of custom prefixes from the SQLite settings table used on the ai_test branch
    def importSqlite(self, db_path):
        with sqlite3.connect(db_path) as conn:
            rows = conn.execute("SELECT guildid, prefix FROM settings WHERE prefix != ?", (DEFAULT_PREFIX,)).fetchall()
        conn.close()

        self.prefixes.update({int(guildid): prefix for guildid, prefix in rows})
        self.save()
        logging.info(f"Imported {len(rows)} custom prefixes from {db_path}")
