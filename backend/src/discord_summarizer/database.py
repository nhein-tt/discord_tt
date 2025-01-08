# database.py
import sqlite3
from datetime import datetime, timezone, timedelta
from typing import List, Dict, Optional
import logging

class DiscordDB:
    def __init__(self, db_path: str = "discord_messages.db"):
        """
        Initializes the Discord database connection and ensures tables exist.

        The database structure includes:
        - channels: Stores channel information and metadata
        - messages: Stores individual messages with their timestamps and authors
        - sync_status: Tracks when each channel was last synchronized
        """
        self.db_path = db_path
        self.setup_database()

    def get_db(self):
        """Creates a database connection with row factory for dict-like access."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def setup_database(self):
        """
        Creates the necessary database tables if they don't exist.
        Each table is designed for efficient querying of recent messages.
        """
        with self.get_db() as conn:
            conn.executescript("""
                CREATE TABLE IF NOT EXISTS channels (
                    channel_id TEXT PRIMARY KEY,
                    server_id TEXT NOT NULL,
                    name TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );

                CREATE TABLE IF NOT EXISTS messages (
                    message_id TEXT PRIMARY KEY,
                    channel_id TEXT NOT NULL,
                    author TEXT NOT NULL,
                    content TEXT NOT NULL,
                    timestamp TIMESTAMP NOT NULL,
                    FOREIGN KEY (channel_id) REFERENCES channels (channel_id)
                );

                CREATE TABLE IF NOT EXISTS sync_status (
                    channel_id TEXT PRIMARY KEY,
                    last_synced TIMESTAMP NOT NULL,
                    FOREIGN KEY (channel_id) REFERENCES channels (channel_id)
                );

                CREATE TABLE IF NOT EXISTS channel_summaries (
                    channel_id TEXT NOT NULL,
                    summary TEXT NOT NULL,
                    message_count INTEGER NOT NULL,
                    total_participants INTEGER NOT NULL,
                    last_active TIMESTAMP NOT NULL,
                    generated_at TIMESTAMP NOT NULL,
                    message_window_start TIMESTAMP NOT NULL,
                    message_window_end TIMESTAMP NOT NULL,
                    PRIMARY KEY (channel_id),
                    FOREIGN KEY (channel_id) REFERENCES channels (channel_id)
                );

                -- Indexes for faster querying
                CREATE INDEX IF NOT EXISTS idx_messages_timestamp
                ON messages (timestamp);

                CREATE INDEX IF NOT EXISTS idx_messages_channel
                ON messages (channel_id, timestamp);
            """)

    def add_channel(self, channel_id: str, server_id: str, name: str):
        """Records a Discord channel in the database."""
        with self.get_db() as conn:
            conn.execute("""
                INSERT OR REPLACE INTO channels (channel_id, server_id, name)
                VALUES (?, ?, ?)
            """, (channel_id, server_id, name))

    def add_messages(self, channel_id: str, messages: List[Dict]):
        """
        Stores multiple Discord messages in the database.
        Handles duplicate messages gracefully using INSERT OR REPLACE.
        """
        with self.get_db() as conn:
            conn.executemany("""
                INSERT OR REPLACE INTO messages
                (message_id, channel_id, author, content, timestamp)
                VALUES (?, ?, ?, ?, ?)
            """, [(
                msg['id'],
                channel_id,
                msg['author']['username'],
                msg['content'],
                msg['timestamp']
            ) for msg in messages])

    def update_sync_status(self, channel_id: str):
        """Records when a channel was last synchronized."""
        with self.get_db() as conn:
            conn.execute("""
                INSERT OR REPLACE INTO sync_status (channel_id, last_synced)
                VALUES (?, datetime('now'))
            """, (channel_id,))

    def get_recent_messages(self, channel_id: str, days: int = 7) -> List[Dict]:
        """
        Retrieves messages from the specified channel within the last N days.
        Returns them in a format compatible with our existing summary logic.
        """
        with self.get_db() as conn:
            rows = conn.execute("""
                SELECT author, content, timestamp
                FROM messages
                WHERE channel_id = ?
                AND timestamp > datetime('now', ?)
                ORDER BY timestamp DESC
            """, (channel_id, f'-{days} days')).fetchall()

            return [dict(row) for row in rows]

    def get_channel_info(self, server_id: str) -> List[Dict]:
        """Retrieves all channels for a given server."""
        with self.get_db() as conn:
            rows = conn.execute("""
                SELECT channel_id, name
                FROM channels
                WHERE server_id = ?
            """, (server_id,)).fetchall()

            return [dict(row) for row in rows]

    def needs_sync(self, channel_id: str, max_age_hours: int = 1) -> bool:
        """
        Determines if a channel needs to be synchronized based on its last sync time.
        This helps prevent too frequent Discord API calls.
        """
        with self.get_db() as conn:
            row = conn.execute("""
                SELECT last_synced
                FROM sync_status
                WHERE channel_id = ?
                AND last_synced > datetime('now', ?)
            """, (channel_id, f'-{max_age_hours} hours')).fetchone()

            return row is None

    def get_server_channels(self, server_id: str) -> List[Dict]:
            """
            Retrieves all known channels for a server from our database.
            This replaces the Discord API call to fetch channels.
            """
            with self.get_db() as conn:
                rows = conn.execute("""
                    SELECT channel_id, name,
                           (SELECT last_synced FROM sync_status
                            WHERE sync_status.channel_id = channels.channel_id) as last_synced
                    FROM channels
                    WHERE server_id = ?
                    ORDER BY name
                """, (server_id,)).fetchall()

                return [dict(row) for row in rows]

    def get_cached_summary(self, channel_id: str, max_age_hours: int = 24) -> Optional[Dict]:
            """
            Retrieves a cached summary if it exists and isn't too old.
            The cache is considered valid if:
            1. It's not older than max_age_hours
            2. No new messages have been synced since the cache was generated
            """
            with self.get_db() as conn:
                row = conn.execute("""
                    SELECT
                        cs.*,
                        s.last_synced
                    FROM channel_summaries cs
                    JOIN sync_status s ON cs.channel_id = s.channel_id
                    WHERE cs.channel_id = ?
                    AND cs.generated_at > datetime('now', ?)
                    AND cs.generated_at > s.last_synced
                """, (channel_id, f'-{max_age_hours} hours')).fetchone()

                return dict(row) if row else None

    def cache_summary(self, channel_id: str, summary_data: Dict):
        """
        Stores a generated summary in the cache.
        """
        with self.get_db() as conn:
            now = datetime.now(timezone.utc)
            window_start = now - timedelta(days=7)  # Assuming 7-day window

            conn.execute("""
                INSERT OR REPLACE INTO channel_summaries
                (channel_id, summary, message_count, total_participants,
                    last_active, generated_at, message_window_start, message_window_end)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                channel_id,
                summary_data['summary'],
                summary_data['message_count'],
                summary_data['total_participants'],
                summary_data['last_active'],
                now.isoformat(),
                window_start.isoformat(),
                now.isoformat()
            ))
