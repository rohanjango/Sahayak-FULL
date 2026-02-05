"""
Phase 7: Memory System Implementation
Stores user information and preferences using SQLite
"""

import sqlite3
import json
from typing import Dict, List, Any, Optional
from datetime import datetime
import aiosqlite
import os

class MemoryManager:
    def __init__(self, db_path: str = "sahayak_memory.db"):
        self.db_path = db_path
        self.db = None
    
    async def initialize(self):
        """Initialize database and create tables"""
        self.db = await aiosqlite.connect(self.db_path)
        await self._create_tables()
        print(f"Memory system initialized: {self.db_path}")
    
    async def _create_tables(self):
        """Create necessary database tables"""
        
        # User preferences table
        await self.db.execute('''
            CREATE TABLE IF NOT EXISTS user_preferences (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT NOT NULL,
                key TEXT NOT NULL,
                value TEXT NOT NULL,
                category TEXT DEFAULT 'general',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(user_id, key)
            )
        ''')
        
        # Execution history table
        await self.db.execute('''
            CREATE TABLE IF NOT EXISTS execution_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT NOT NULL,
                command TEXT NOT NULL,
                steps_data TEXT,
                status TEXT,
                execution_time REAL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Learned patterns table
        await self.db.execute('''
            CREATE TABLE IF NOT EXISTS learned_patterns (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT NOT NULL,
                pattern_type TEXT NOT NULL,
                pattern_data TEXT,
                frequency INTEGER DEFAULT 1,
                last_used TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Auto-fill data table
        await self.db.execute('''
            CREATE TABLE IF NOT EXISTS autofill_data (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT NOT NULL,
                field_type TEXT NOT NULL,
                field_value TEXT NOT NULL,
                encrypted BOOLEAN DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(user_id, field_type)
            )
        ''')
        
        await self.db.commit()
    
    async def save_item(self, user_id: str, key: str, value: str, category: str = "general"):
        """Save a user preference item"""
        try:
            await self.db.execute('''
                INSERT INTO user_preferences (user_id, key, value, category, updated_at)
                VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP)
                ON CONFLICT(user_id, key) DO UPDATE SET
                    value = excluded.value,
                    updated_at = CURRENT_TIMESTAMP
            ''', (user_id, key, value, category))
            await self.db.commit()
        except Exception as e:
            print(f"Save item error: {e}")
    
    async def get_item(self, user_id: str, key: str) -> Optional[str]:
        """Get a specific user preference"""
        try:
            async with self.db.execute(
                'SELECT value FROM user_preferences WHERE user_id = ? AND key = ?',
                (user_id, key)
            ) as cursor:
                row = await cursor.fetchone()
                return row[0] if row else None
        except Exception as e:
            print(f"Get item error: {e}")
            return None
    
    async def get_all_memories(self, user_id: str) -> Dict[str, Any]:
        """Get all memories for a user"""
        memories = {}
        
        try:
            # Get preferences
            async with self.db.execute(
                'SELECT key, value, category FROM user_preferences WHERE user_id = ?',
                (user_id,)
            ) as cursor:
                async for row in cursor:
                    key, value, category = row
                    if category not in memories:
                        memories[category] = {}
                    memories[category][key] = value
            
            # Get autofill data
            async with self.db.execute(
                'SELECT field_type, field_value FROM autofill_data WHERE user_id = ?',
                (user_id,)
            ) as cursor:
                autofill = {}
                async for row in cursor:
                    field_type, field_value = row
                    autofill[field_type] = field_value
                if autofill:
                    memories['autofill'] = autofill
            
        except Exception as e:
            print(f"Get all memories error: {e}")
        
        return memories
    
    async def get_user_context(self, user_id: str) -> Dict[str, Any]:
        """Get comprehensive user context for AI decision making"""
        
        context = {
            'user_id': user_id,
            'preferences': {},
            'recent_history': [],
            'learned_patterns': [],
            'autofill': {}
        }
        
        try:
            # Get preferences
            async with self.db.execute(
                'SELECT key, value FROM user_preferences WHERE user_id = ?',
                (user_id,)
            ) as cursor:
                async for row in cursor:
                    key, value = row
                    context['preferences'][key] = value
            
            # Get recent execution history
            async with self.db.execute(
                '''SELECT command, status FROM execution_history 
                   WHERE user_id = ? ORDER BY created_at DESC LIMIT 5''',
                (user_id,)
            ) as cursor:
                async for row in cursor:
                    command, status = row
                    context['recent_history'].append({'command': command, 'status': status})
            
            # Get autofill data
            async with self.db.execute(
                'SELECT field_type, field_value FROM autofill_data WHERE user_id = ?',
                (user_id,)
            ) as cursor:
                async for row in cursor:
                    field_type, field_value = row
                    context['autofill'][field_type] = field_value
            
        except Exception as e:
            print(f"Get user context error: {e}")
        
        return context
    
    async def save_execution(self, user_id: str, command: str, steps: List[Any]):
        """Save command execution to history"""
        try:
            steps_json = json.dumps([s.__dict__ if hasattr(s, '__dict__') else str(s) for s in steps])
            status = "success" if all(hasattr(s, 'status') and s.status == 'success' for s in steps) else "partial"
            
            await self.db.execute('''
                INSERT INTO execution_history (user_id, command, steps_data, status)
                VALUES (?, ?, ?, ?)
            ''', (user_id, command, steps_json, status))
            await self.db.commit()
        except Exception as e:
            print(f"Save execution error: {e}")
    
    async def save_autofill_data(self, user_id: str, field_type: str, value: str, encrypted: bool = False):
        """Save auto-fill data for future use"""
        try:
            await self.db.execute('''
                INSERT INTO autofill_data (user_id, field_type, field_value, encrypted)
                VALUES (?, ?, ?, ?)
                ON CONFLICT(user_id, field_type) DO UPDATE SET
                    field_value = excluded.field_value,
                    encrypted = excluded.encrypted
            ''', (user_id, field_type, value, encrypted))
            await self.db.commit()
        except Exception as e:
            print(f"Save autofill error: {e}")
    
    async def get_autofill_value(self, user_id: str, field_type: str) -> Optional[str]:
        """Get auto-fill value for a field type"""
        try:
            async with self.db.execute(
                'SELECT field_value FROM autofill_data WHERE user_id = ? AND field_type = ?',
                (user_id, field_type)
            ) as cursor:
                row = await cursor.fetchone()
                return row[0] if row else None
        except Exception as e:
            print(f"Get autofill error: {e}")
            return None
    
    async def learn_pattern(self, user_id: str, pattern_type: str, pattern_data: Dict):
        """Learn and store usage patterns"""
        try:
            pattern_json = json.dumps(pattern_data)
            
            # Check if pattern exists
            async with self.db.execute(
                'SELECT id, frequency FROM learned_patterns WHERE user_id = ? AND pattern_type = ?',
                (user_id, pattern_type)
            ) as cursor:
                row = await cursor.fetchone()
            
            if row:
                # Update existing pattern
                pattern_id, frequency = row
                await self.db.execute(
                    'UPDATE learned_patterns SET frequency = ?, last_used = CURRENT_TIMESTAMP WHERE id = ?',
                    (frequency + 1, pattern_id)
                )
            else:
                # Insert new pattern
                await self.db.execute('''
                    INSERT INTO learned_patterns (user_id, pattern_type, pattern_data)
                    VALUES (?, ?, ?)
                ''', (user_id, pattern_type, pattern_json))
            
            await self.db.commit()
        except Exception as e:
            print(f"Learn pattern error: {e}")
    
    async def close(self):
        """Close database connection"""
        if self.db:
            await self.db.close()
