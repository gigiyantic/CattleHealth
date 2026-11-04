"""SQLite storage. One file, no server — fine for thousands of cows per instance."""
import sqlite3
import threading
from contextlib import contextmanager

SCHEMA = """
CREATE TABLE IF NOT EXISTS farms (
  id INTEGER PRIMARY KEY,
  name TEXT NOT NULL,
  owner_phone TEXT,               -- WhatsApp number in E.164 without '+', e.g. 919876543210
  language TEXT NOT NULL DEFAULT 'en'
);
CREATE TABLE IF NOT EXISTS gateways (
  id TEXT PRIMARY KEY,
  farm_id INTEGER REFERENCES farms(id),
  last_seen TEXT
);
CREATE TABLE IF NOT EXISTS cows (
  tag_id INTEGER PRIMARY KEY,
  farm_id INTEGER REFERENCES farms(id),
  name TEXT,
  breed TEXT,
  last_insemination TEXT,
  created_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ','now'))
);
CREATE TABLE IF NOT EXISTS readings (
  tag_id INTEGER NOT NULL,
  seq INTEGER,
  ts TEXT NOT NULL,
  temp_c REAL,
  rumination_min INTEGER,
  activity_mg INTEGER,
  battery_mv INTEGER,
  flags INTEGER DEFAULT 0,
  rssi INTEGER,
  gateway_id TEXT,
  UNIQUE(tag_id, ts)
);
CREATE INDEX IF NOT EXISTS ix_readings_tag_ts ON readings(tag_id, ts);
CREATE TABLE IF NOT EXISTS alerts (
  id INTEGER PRIMARY KEY,
  tag_id INTEGER NOT NULL,
  kind TEXT NOT NULL,             -- fever | rumination | heat | low_battery | tamper | offline
  severity TEXT NOT NULL,         -- info | warning | critical
  message TEXT NOT NULL,
  value REAL,
  created_at TEXT NOT NULL,
  acknowledged INTEGER NOT NULL DEFAULT 0,
  sent_whatsapp INTEGER NOT NULL DEFAULT 0
);
CREATE INDEX IF NOT EXISTS ix_alerts_tag_kind ON alerts(tag_id, kind, created_at);
"""


class DB:
    def __init__(self, path: str):
        self.path = path
        self._lock = threading.RLock()
        self.conn = sqlite3.connect(path, check_same_thread=False)
        self.conn.row_factory = sqlite3.Row
        self.conn.execute("PRAGMA journal_mode=WAL")
        self.conn.executescript(SCHEMA)
        self.conn.commit()

    @contextmanager
    def tx(self):
        with self._lock:
            try:
                yield self.conn
                self.conn.commit()
            except Exception:
                self.conn.rollback()
                raise

    def query(self, sql, args=()):
        with self._lock:
            return [dict(r) for r in self.conn.execute(sql, args).fetchall()]

    def one(self, sql, args=()):
        rows = self.query(sql, args)
        return rows[0] if rows else None
