import sqlite3
from pathlib import Path
import json
from datetime import datetime, timezone
import aiosqlite

DB_PATH = Path(__file__).parent / "sahayak.db"

async def init_db():
    """Initialize the SQLite database with required tables"""
    async with aiosqlite.connect(DB_PATH) as db:
        # User memory table
        await db.execute("""
            CREATE TABLE IF NOT EXISTS user_memory (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT NOT NULL,
                key TEXT NOT NULL,
                value TEXT NOT NULL,
                created_at TEXT NOT NULL,
                UNIQUE(user_id, key)
            )
        """)
        
        # Execution history table
        await db.execute("""
            CREATE TABLE IF NOT EXISTS execution_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT NOT NULL,
                command TEXT NOT NULL,
                steps TEXT NOT NULL,
                status TEXT NOT NULL,
                result TEXT,
                created_at TEXT NOT NULL
            )
        """)
        
        # Session data table
        await db.execute("""
            CREATE TABLE IF NOT EXISTS sessions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT UNIQUE NOT NULL,
                user_id TEXT NOT NULL,
                state TEXT NOT NULL,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )
        """)
        
        await db.commit()

async def save_memory(user_id: str, key: str, value: str):
    """Save or update user memory"""
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
            INSERT INTO user_memory (user_id, key, value, created_at)
            VALUES (?, ?, ?, ?)
            ON CONFLICT(user_id, key) DO UPDATE SET
                value = excluded.value,
                created_at = excluded.created_at
        """, (user_id, key, value, datetime.now(timezone.utc).isoformat()))
        await db.commit()

async def get_memory(user_id: str, key: str = None):
    """Get user memory by key or all memories"""
    async with aiosqlite.connect(DB_PATH) as db:
        if key:
            async with db.execute(
                "SELECT value FROM user_memory WHERE user_id = ? AND key = ?",
                (user_id, key)
            ) as cursor:
                row = await cursor.fetchone()
                return row[0] if row else None
        else:
            async with db.execute(
                "SELECT key, value FROM user_memory WHERE user_id = ?",
                (user_id,)
            ) as cursor:
                rows = await cursor.fetchall()
                return {row[0]: row[1] for row in rows}

async def save_execution(user_id: str, command: str, steps: list, status: str, result: str = None):
    """Save execution history"""
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
            INSERT INTO execution_history (user_id, command, steps, status, result, created_at)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (user_id, command, json.dumps(steps), status, result, datetime.now(timezone.utc).isoformat()))
        await db.commit()

async def get_execution_history(user_id: str, limit: int = 10):
    """Get execution history for user"""
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute("""
            SELECT command, steps, status, result, created_at
            FROM execution_history
            WHERE user_id = ?
            ORDER BY created_at DESC
            LIMIT ?
        """, (user_id, limit)) as cursor:
            rows = await cursor.fetchall()
            return [
                {
                    "command": row[0],
                    "steps": json.loads(row[1]),
                    "status": row[2],
                    "result": row[3],
                    "created_at": row[4]
                }
                for row in rows
            ]