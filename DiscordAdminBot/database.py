import aiosqlite
import asyncio
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Any

class Database:
    def __init__(self, db_path: str = "admin_bot.db"):
        self.db_path = db_path
        self.db = None
    
    async def initialize(self):
        """Initialize database and create tables"""
        self.db = await aiosqlite.connect(self.db_path)
        await self.create_tables()
        logging.info("Database initialized successfully")
    
    async def create_tables(self):
        """Create all necessary database tables"""
        tables = [
            # Warnings table
            """
            CREATE TABLE IF NOT EXISTS warnings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                guild_id INTEGER NOT NULL,
                user_id INTEGER NOT NULL,
                moderator_id INTEGER NOT NULL,
                reason TEXT NOT NULL,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
            )
            """,
            
            # Mutes table
            """
            CREATE TABLE IF NOT EXISTS mutes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                guild_id INTEGER NOT NULL,
                user_id INTEGER NOT NULL,
                moderator_id INTEGER NOT NULL,
                reason TEXT,
                start_time DATETIME DEFAULT CURRENT_TIMESTAMP,
                end_time DATETIME,
                active BOOLEAN DEFAULT 1
            )
            """,
            
            # Moderation logs table
            """
            CREATE TABLE IF NOT EXISTS mod_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                guild_id INTEGER NOT NULL,
                action_type TEXT NOT NULL,
                moderator_id INTEGER NOT NULL,
                target_id INTEGER,
                reason TEXT,
                details TEXT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
            )
            """,
            
            # Guild settings table
            """
            CREATE TABLE IF NOT EXISTS guild_settings (
                guild_id INTEGER PRIMARY KEY,
                mod_log_channel INTEGER,
                mute_role_id INTEGER,
                settings_json TEXT DEFAULT '{}'
            )
            """
        ]
        
        for table_sql in tables:
            await self.db.execute(table_sql)
        
        await self.db.commit()
    
    async def close(self):
        """Close database connection"""
        if self.db:
            await self.db.close()
    
    # Warning system methods
    async def add_warning(self, guild_id: int, user_id: int, moderator_id: int, reason: str) -> int:
        """Add a warning to the database"""
        cursor = await self.db.execute(
            "INSERT INTO warnings (guild_id, user_id, moderator_id, reason) VALUES (?, ?, ?, ?)",
            (guild_id, user_id, moderator_id, reason)
        )
        await self.db.commit()
        return cursor.lastrowid
    
    async def get_warnings(self, guild_id: int, user_id: int) -> List[Dict[str, Any]]:
        """Get all warnings for a user"""
        cursor = await self.db.execute(
            "SELECT * FROM warnings WHERE guild_id = ? AND user_id = ? ORDER BY timestamp DESC",
            (guild_id, user_id)
        )
        rows = await cursor.fetchall()
        
        warnings = []
        for row in rows:
            warnings.append({
                'id': row[0],
                'guild_id': row[1],
                'user_id': row[2],
                'moderator_id': row[3],
                'reason': row[4],
                'timestamp': row[5]
            })
        
        return warnings
    
    async def clear_warnings(self, guild_id: int, user_id: int) -> int:
        """Clear all warnings for a user"""
        cursor = await self.db.execute(
            "DELETE FROM warnings WHERE guild_id = ? AND user_id = ?",
            (guild_id, user_id)
        )
        await self.db.commit()
        return cursor.rowcount
    
    async def get_warning_count(self, guild_id: int, user_id: int) -> int:
        """Get warning count for a user"""
        cursor = await self.db.execute(
            "SELECT COUNT(*) FROM warnings WHERE guild_id = ? AND user_id = ?",
            (guild_id, user_id)
        )
        result = await cursor.fetchone()
        return result[0] if result else 0
    
    # Mute system methods
    async def add_mute(self, guild_id: int, user_id: int, moderator_id: int, reason: str, duration: timedelta = None) -> int:
        """Add a mute to the database"""
        end_time = datetime.now() + duration if duration else None
        
        cursor = await self.db.execute(
            "INSERT INTO mutes (guild_id, user_id, moderator_id, reason, end_time) VALUES (?, ?, ?, ?, ?)",
            (guild_id, user_id, moderator_id, reason, end_time)
        )
        await self.db.commit()
        return cursor.lastrowid
    
    async def remove_mute(self, guild_id: int, user_id: int) -> bool:
        """Remove active mute for a user"""
        cursor = await self.db.execute(
            "UPDATE mutes SET active = 0 WHERE guild_id = ? AND user_id = ? AND active = 1",
            (guild_id, user_id)
        )
        await self.db.commit()
        return cursor.rowcount > 0
    
    async def get_active_mute(self, guild_id: int, user_id: int) -> Optional[Dict[str, Any]]:
        """Get active mute for a user"""
        cursor = await self.db.execute(
            "SELECT * FROM mutes WHERE guild_id = ? AND user_id = ? AND active = 1 ORDER BY start_time DESC LIMIT 1",
            (guild_id, user_id)
        )
        row = await cursor.fetchone()
        
        if row:
            return {
                'id': row[0],
                'guild_id': row[1],
                'user_id': row[2],
                'moderator_id': row[3],
                'reason': row[4],
                'start_time': row[5],
                'end_time': row[6],
                'active': row[7]
            }
        return None
    
    async def get_expired_mutes(self) -> List[Dict[str, Any]]:
        """Get all expired mutes that are still active"""
        cursor = await self.db.execute(
            "SELECT * FROM mutes WHERE active = 1 AND end_time IS NOT NULL AND end_time <= datetime('now')"
        )
        rows = await cursor.fetchall()
        
        mutes = []
        for row in rows:
            mutes.append({
                'id': row[0],
                'guild_id': row[1],
                'user_id': row[2],
                'moderator_id': row[3],
                'reason': row[4],
                'start_time': row[5],
                'end_time': row[6],
                'active': row[7]
            })
        
        return mutes
    
    # Moderation logs methods
    async def log_action(self, guild_id: int, action_type: str, moderator_id: int, target_id: int = None, reason: str = None, details: str = None):
        """Log a moderation action"""
        await self.db.execute(
            "INSERT INTO mod_logs (guild_id, action_type, moderator_id, target_id, reason, details) VALUES (?, ?, ?, ?, ?, ?)",
            (guild_id, action_type, moderator_id, target_id, reason, details)
        )
        await self.db.commit()
    
    # Guild settings methods
    async def setup_guild(self, guild_id: int):
        """Initialize guild settings"""
        await self.db.execute(
            "INSERT OR IGNORE INTO guild_settings (guild_id) VALUES (?)",
            (guild_id,)
        )
        await self.db.commit()
    
    async def set_mod_log_channel(self, guild_id: int, channel_id: int):
        """Set moderation log channel for a guild"""
        await self.setup_guild(guild_id)
        await self.db.execute(
            "UPDATE guild_settings SET mod_log_channel = ? WHERE guild_id = ?",
            (channel_id, guild_id)
        )
        await self.db.commit()
    
    async def get_mod_log_channel(self, guild_id: int) -> Optional[int]:
        """Get moderation log channel for a guild"""
        cursor = await self.db.execute(
            "SELECT mod_log_channel FROM guild_settings WHERE guild_id = ?",
            (guild_id,)
        )
        result = await cursor.fetchone()
        return result[0] if result and result[0] else None
    
    async def set_mute_role(self, guild_id: int, role_id: int):
        """Set mute role for a guild"""
        await self.setup_guild(guild_id)
        await self.db.execute(
            "UPDATE guild_settings SET mute_role_id = ? WHERE guild_id = ?",
            (role_id, guild_id)
        )
        await self.db.commit()
    
    async def get_mute_role(self, guild_id: int) -> Optional[int]:
        """Get mute role for a guild"""
        cursor = await self.db.execute(
            "SELECT mute_role_id FROM guild_settings WHERE guild_id = ?",
            (guild_id,)
        )
        result = await cursor.fetchone()
        return result[0] if result and result[0] else None
