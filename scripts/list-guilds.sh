#!/usr/bin/env bash
# Lists the servers in a Marcie database with their prefix and activity, most recently active first.
# Runs in a throwaway python:3.12-slim container (Marcie's base image, so usually already downloaded) that only sees
# the database file, read-only, with no network, and is deleted when it finishes.
#   Marcie/scripts/list-guilds.sh                 data/marcie.db in the current directory
#   Marcie/scripts/list-guilds.sh path/to/file.db any marcie.db file, e.g. a backup
# Activity is saved every few minutes, so the last few minutes of commands may not show yet.
set -euo pipefail

IMAGE=python:3.12-slim

db_file=$(realpath -m -- "${1:-data/marcie.db}")
[ -f "$db_file" ] || { echo "No such file: $db_file" >&2; exit 1; }

docker run --rm -i --network none --read-only --cap-drop ALL --security-opt no-new-privileges \
    -v "$db_file:/marcie.db:ro" -e DB_LABEL="$db_file" "$IMAGE" python - <<'EOF'
import datetime, os, sqlite3

RECENT_DAYS = 30
YEAR_MONTHS = 12
MONTHS_PER_YEAR = 12

conn = sqlite3.connect('file:/marcie.db?mode=ro', uri=True)
tables = {row[0] for row in conn.execute("SELECT name FROM sqlite_master WHERE type = 'table'")}
has_activity = {'activity_daily', 'activity_monthly'} <= tables

today = datetime.datetime.now(datetime.timezone.utc).date()
recent_start = (today - datetime.timedelta(days=RECENT_DAYS - 1)).isoformat()
year_index = today.year * MONTHS_PER_YEAR + today.month - 1 - (YEAR_MONTHS - 1)
year_month = f"{year_index // MONTHS_PER_YEAR:04d}-{year_index % MONTHS_PER_YEAR + 1:02d}"

rows = []
for guildid, prefix, name in conn.execute('SELECT guildid, prefix, name FROM settings'):
    last, recent, year = '-', 0, 0
    if has_activity:
        last_day = conn.execute('SELECT MAX(day) FROM activity_daily WHERE guildid = ?', (guildid,)).fetchone()[0]
        last_month = conn.execute('SELECT MAX(month) FROM activity_monthly WHERE guildid = ?', (guildid,)).fetchone()[0]
        last = last_day or last_month or 'never'
        recent = conn.execute('SELECT COALESCE(SUM(commands), 0) FROM activity_daily WHERE guildid = ? AND day >= ?',
                              (guildid, recent_start)).fetchone()[0]
        # Each day's count is in exactly one table: daily while recent, monthly once rolled up
        year = (conn.execute('SELECT COALESCE(SUM(commands), 0) FROM activity_daily WHERE guildid = ? AND day >= ?',
                             (guildid, year_month + '-01')).fetchone()[0]
                + conn.execute('SELECT COALESCE(SUM(commands), 0) FROM activity_monthly WHERE guildid = ? AND month >= ?',
                               (guildid, year_month)).fetchone()[0])
    rows.append((guildid, prefix, name, last, recent, year))

rows.sort(key=lambda r: r[3] if r[3] not in ('-', 'never') else '', reverse=True)

print(f"{'Server ID':<20} {'Prefix':<6} {'Last active':<11} {'30 days':>7} {'12 months':>9}  Name")
for guildid, prefix, name, last, recent, year in rows:
    print(f"{guildid:<20} {prefix:<6} {last:<11} {recent:>7} {year:>9}  {name}")

print(f"{len(rows)} guilds in {os.environ['DB_LABEL']}")
if not has_activity:
    print('No activity yet: this database is from before activity counting was added.')
EOF
