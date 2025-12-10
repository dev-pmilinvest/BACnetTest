"""
Database Manager
Handles local SQLite storage for sensor readings
"""

import sqlite3
import json
from datetime import datetime, timedelta
from typing import List, Dict, Optional
from pathlib import Path
from src.config import Config
from src.logger import setup_logger
from src.utils import check

logger = setup_logger(__name__)

class Database:
    """SQLite database manager for local sensor data storage"""

    def __init__(self, db_path: Optional[str] = None):
        self.db_path = db_path or Config.DB_PATH
        Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)
        self.conn = None
        self.init_database()

    def init_database(self):
        """Initialize database and create tables"""
        try:
            self.conn = sqlite3.connect(self.db_path)
            self.conn.row_factory = sqlite3.Row
            cursor = self.conn.cursor()

            # Create sensor_readings table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS sensor_readings (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT NOT NULL,
                    sensor_name TEXT NOT NULL,
                    value REAL NOT NULL,
                    unit TEXT,
                    priority_array TEXT,
                    active_priority INTEGER,
                    posted INTEGER DEFAULT 0,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            ''')

            # Add new columns if they don't exist (for migration)
            try:
                cursor.execute('ALTER TABLE sensor_readings ADD COLUMN priority_array TEXT')
            except sqlite3.OperationalError:
                pass  # Column already exists

            try:
                cursor.execute('ALTER TABLE sensor_readings ADD COLUMN active_priority INTEGER')
            except sqlite3.OperationalError:
                pass  # Column already exists

            # Create indexes
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_posted 
                ON sensor_readings(posted)
            ''')

            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_timestamp 
                ON sensor_readings(timestamp)
            ''')

            self.conn.commit()
            logger.info(f"✓ Database initialized: {self.db_path}")

        except sqlite3.Error as e:
            logger.error(f"Database initialization failed: {e}")
            raise

    def store_readings(self, readings: List[Dict]) -> int:
        """
        Store sensor readings in database

        Args:
            readings: List of reading dictionaries

        Returns:
            Number of readings stored
        """
        if not readings:
            return 0

        try:
            cursor = self.conn.cursor()

            for reading in readings:
                # Serialize priority_array as JSON if present
                priority_array = reading.get('priority_array')
                priority_array_json = json.dumps(priority_array) if priority_array is not None else None

                cursor.execute('''
                    INSERT INTO sensor_readings (timestamp, sensor_name, value, unit, priority_array, active_priority)
                    VALUES (?, ?, ?, ?, ?, ?)
                ''', (
                    reading['timestamp'],
                    reading['sensor_name'],
                    reading['value'],
                    reading.get('unit', ''),
                    priority_array_json,
                    reading.get('active_priority')
                ))

            self.conn.commit()
            logger.debug(f"Stored {len(readings)} readings locally")
            return len(readings)

        except sqlite3.Error as e:
            logger.error(f"Failed to store readings: {e}")
            self.conn.rollback()
            return 0

    def get_unposted_readings(self) -> List[Dict]:
        """
        Get all readings that haven't been posted to API

        Returns:
            List of unposted readings
        """
        try:
            cursor = self.conn.cursor()
            cursor.execute('''
                SELECT id, timestamp, sensor_name, value, unit, priority_array, active_priority
                FROM sensor_readings
                WHERE posted = 0
                ORDER BY timestamp ASC
            ''')

            rows = cursor.fetchall()
            results = []
            for row in rows:
                reading = dict(row)
                # Deserialize priority_array from JSON
                if reading.get('priority_array'):
                    reading['priority_array'] = json.loads(reading['priority_array'])
                results.append(reading)
            return results

        except sqlite3.Error as e:
            logger.error(f"Failed to fetch unposted readings: {e}")
            return []

    def mark_as_posted(self, reading_ids: List[int]) -> bool:
        """
        Mark readings as posted to API

        Args:
            reading_ids: List of reading IDs to mark

        Returns:
            True if successful
        """
        if not reading_ids:
            return True

        try:
            cursor = self.conn.cursor()
            placeholders = ','.join('?' * len(reading_ids))
            cursor.execute(
                f'UPDATE sensor_readings SET posted = 1 WHERE id IN ({placeholders})',
                reading_ids
            )
            self.conn.commit()
            logger.debug(f"Marked {len(reading_ids)} readings as posted")
            return True

        except sqlite3.Error as e:
            logger.error(f"Failed to mark readings as posted: {e}")
            self.conn.rollback()
            return False

    def cleanup_old_data(self, days: int = 7) -> int:
        """
        Delete old posted readings

        Args:
            days: Keep data from last N days

        Returns:
            Number of deleted records
        """
        try:
            cutoff_date = (datetime.now() - timedelta(days=days)).isoformat()
            cursor = self.conn.cursor()

            cursor.execute('''
                DELETE FROM sensor_readings
                WHERE posted = 1 AND timestamp < ?
            ''', (cutoff_date,))

            deleted = cursor.rowcount
            self.conn.commit()

            if deleted > 0:
                logger.info(f"Cleaned up {deleted} old readings")

            return deleted

        except sqlite3.Error as e:
            logger.error(f"Failed to cleanup old data: {e}")
            return 0

    def get_stats(self) -> Dict:
        """Get database statistics"""
        try:
            cursor = self.conn.cursor()

            cursor.execute('SELECT COUNT(*) as total FROM sensor_readings')
            total = cursor.fetchone()['total']

            cursor.execute('SELECT COUNT(*) as unposted FROM sensor_readings WHERE posted = 0')
            unposted = cursor.fetchone()['unposted']

            return {
                'total_readings': total,
                'unposted_readings': unposted,
                'posted_readings': total - unposted
            }

        except sqlite3.Error as e:
            logger.error(f"Failed to get stats: {e}")
            return {}

    def close(self):
        """Close database connection"""
        if self.conn:
            self.conn.close()
            logger.debug("Database connection closed")