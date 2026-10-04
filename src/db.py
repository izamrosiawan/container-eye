import sqlite3
import os
import time

class InspectionDatabase:
    def __init__(self, db_path=None):
        if db_path is None:
            base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            db_path = os.path.join(base_dir, "logs", "inspections.db")
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        self.db_path = db_path
        self._init_db()

    def _init_db(self):
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS inspections (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT NOT NULL,
                    feed_name TEXT NOT NULL,
                    status TEXT NOT NULL,
                    defect_count INTEGER NOT NULL,
                    defects_detail TEXT,
                    latency_ms REAL,
                    snapshot_path TEXT
                )
            ''')
            conn.commit()

    def log_record(self, feed_name, status, defect_count, defects_detail, latency_ms, snapshot_path):
        timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO inspections (timestamp, feed_name, status, defect_count, defects_detail, latency_ms, snapshot_path)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (timestamp, feed_name, status, defect_count, defects_detail, latency_ms, snapshot_path))
            conn.commit()

    def get_recent(self, limit=15):
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT timestamp, feed_name, status, defect_count, snapshot_path
                FROM inspections ORDER BY id DESC LIMIT ?
            ''', (limit,))
            return cursor.fetchall()
