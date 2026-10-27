import datetime
import logging
import os
import sqlite3
from collections import Counter
from contextlib import closing
from constants import ACTIVITY_DAILY_DAYS, ACTIVITY_MONTHLY_MONTHS, MONTHS_PER_YEAR

log = logging.getLogger(__name__)


def utcToday():
    return datetime.datetime.now(datetime.timezone.utc).date()


# Month string ("2026-10") a number of months before the given date
def monthsBefore(day, months):
    index = day.year * MONTHS_PER_YEAR + (day.month - 1) - months
    return f"{index // MONTHS_PER_YEAR:04d}-{index % MONTHS_PER_YEAR + 1:02d}"


# Counts how many commands each guild uses, with no information about who ran them.  Counts are tallied in memory and
# added to activity_daily by flush().  cleanup() rolls daily counts older than ACTIVITY_DAILY_DAYS into monthly totals
# in activity_monthly, and deletes monthly totals older than ACTIVITY_MONTHLY_MONTHS.

class ActivityStore:
    def __init__(self, path):
        self.path = path
        self.pending = Counter()

    def _connect(self):
        return closing(sqlite3.connect(self.path))

    def load(self):
        os.makedirs(os.path.dirname(self.path) or '.', exist_ok=True)

        with self._connect() as conn, conn:
            conn.execute('''
                CREATE TABLE IF NOT EXISTS activity_daily (
                    guildid INTEGER NOT NULL,
                    day TEXT NOT NULL,
                    commands INTEGER NOT NULL,
                    PRIMARY KEY (guildid, day)
                )
            ''')
            conn.execute('''
                CREATE TABLE IF NOT EXISTS activity_monthly (
                    guildid INTEGER NOT NULL,
                    month TEXT NOT NULL,
                    commands INTEGER NOT NULL,
                    PRIMARY KEY (guildid, month)
                )
            ''')

        return self

    def record(self, guildid, day=None):
        self.pending[(guildid, (day or utcToday()).isoformat())] += 1

    def flush(self):
        if not self.pending:
            return

        rows = [(guildid, day, count) for (guildid, day), count in self.pending.items()]
        with self._connect() as conn, conn:
            conn.executemany("INSERT INTO activity_daily (guildid, day, commands) VALUES (?, ?, ?) "
                             "ON CONFLICT(guildid, day) DO UPDATE SET commands = commands + excluded.commands", rows)
        self.pending.clear()

    def cleanup(self, today=None):
        today = today or utcToday()
        daily_cutoff = (today - datetime.timedelta(days=ACTIVITY_DAILY_DAYS)).isoformat()
        monthly_cutoff = monthsBefore(today, ACTIVITY_MONTHLY_MONTHS)

        with self._connect() as conn, conn:
            rolled = conn.execute("INSERT INTO activity_monthly (guildid, month, commands) "
                                  "SELECT guildid, substr(day, 1, 7), SUM(commands) FROM activity_daily "
                                  "WHERE day < ? GROUP BY guildid, substr(day, 1, 7) "
                                  "ON CONFLICT(guildid, month) DO UPDATE SET commands = commands + excluded.commands",
                                  (daily_cutoff,)).rowcount
            conn.execute("DELETE FROM activity_daily WHERE day < ?", (daily_cutoff,))
            expired = conn.execute("DELETE FROM activity_monthly WHERE month < ?", (monthly_cutoff,)).rowcount

        if rolled or expired:
            log.info(f"Activity cleanup: rolled {rolled} monthly totals, deleted {expired} expired months")

    # A guild that removes Marcie has its activity deleted along with its settings
    def remove(self, guildid):
        for key in [key for key in self.pending if key[0] == guildid]:
            del self.pending[key]

        with self._connect() as conn, conn:
            conn.execute("DELETE FROM activity_daily WHERE guildid = ?", (guildid,))
            conn.execute("DELETE FROM activity_monthly WHERE guildid = ?", (guildid,))
