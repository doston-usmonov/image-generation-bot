import asyncpg
from typing import Optional
from datetime import datetime
import os
from dotenv import load_dotenv

load_dotenv()

class Database:
    def __init__(self):
        self.pool: Optional[asyncpg.Pool] = None

    async def create_pool(self):
        """Create database connection pool"""
        self.pool = await asyncpg.create_pool(
            os.getenv("DATABASE_URL"),
            min_size=2,
            max_size=10
        )
        await self.init_db()

    async def init_db(self):
        """Initialize database tables"""
        async with self.pool.acquire() as conn:
            # Create users table if not exists
            await conn.execute('''
                CREATE TABLE IF NOT EXISTS users (
                    id SERIAL PRIMARY KEY,
                    telegram_id BIGINT UNIQUE,
                    username VARCHAR(255),
                    first_name VARCHAR(255),
                    last_name VARCHAR(255),
                    is_admin BOOLEAN DEFAULT FALSE,
                    is_blocked BOOLEAN DEFAULT FALSE,
                    created_at TIMESTAMP DEFAULT NOW()
                )
            ''')
            
            # Create images table if not exists
            await conn.execute('''
                CREATE TABLE IF NOT EXISTS images (
                    id SERIAL PRIMARY KEY,
                    user_id BIGINT REFERENCES users(telegram_id),
                    prompt TEXT,
                    url TEXT,
                    created_at TIMESTAMP DEFAULT NOW()
                )
            ''')

    async def add_user(self, telegram_id: int, username: str, first_name: str, last_name: str) -> bool:
        async with self.pool.acquire() as conn:
            try:
                await conn.execute('''
                    INSERT INTO users (telegram_id, username, first_name, last_name)
                    VALUES ($1, $2, $3, $4)
                    ON CONFLICT (telegram_id) 
                    DO UPDATE SET username = $2, first_name = $3, last_name = $4
                ''', telegram_id, username, first_name, last_name)
                return True
            except Exception as e:
                print(f"Error adding user: {e}")
                return False

    async def get_user(self, telegram_id: int):
        async with self.pool.acquire() as conn:
            return await conn.fetchrow(
                'SELECT * FROM users WHERE telegram_id = $1',
                telegram_id
            )

    async def add_image(self, file_id: str, user_id: int, prompt: str):
        async with self.pool.acquire() as conn:
            return await conn.execute('''
                INSERT INTO images (file_id, user_id, prompt)
                VALUES ($1, $2, $3)
            ''', file_id, user_id, prompt)

    async def get_user_images(self, user_id: int):
        async with self.pool.acquire() as conn:
            return await conn.fetch('''
                SELECT * FROM images 
                WHERE user_id = $1 
                ORDER BY created_at DESC
            ''', user_id)

    async def search_images_by_prompt(self, prompt: str):
        async with self.pool.acquire() as conn:
            return await conn.fetch('''
                SELECT * FROM images 
                WHERE prompt ILIKE $1
                ORDER BY created_at DESC
            ''', f'%{prompt}%')

    async def set_admin(self, telegram_id: int, is_admin: bool = True):
        async with self.pool.acquire() as conn:
            try:
                await conn.execute('''
                    UPDATE users 
                    SET is_admin = $2 
                    WHERE telegram_id = $1
                ''', telegram_id, is_admin)
                return True
            except Exception as e:
                print(f"Error setting admin status: {e}")
                return False

    async def get_user_by_username(self, username: str):
        async with self.pool.acquire() as conn:
            return await conn.fetchrow('''
                SELECT * FROM users 
                WHERE username = $1
            ''', username)

    async def get_all_admins(self):
        async with self.pool.acquire() as conn:
            return await conn.fetch('''
                SELECT * FROM users 
                WHERE is_admin = TRUE 
                ORDER BY id ASC
            ''')

    async def get_admins(self):
        async with self.pool.acquire() as conn:
            return await conn.fetch('''
                SELECT * FROM users 
                WHERE is_admin = TRUE 
                ORDER BY created_at DESC
            ''')

    async def toggle_user_block(self, telegram_id: int, block_status: bool):
        async with self.pool.acquire() as conn:
            await conn.execute('''
                UPDATE users 
                SET is_blocked = $2 
                WHERE telegram_id = $1
            ''', telegram_id, block_status)

    async def is_user_blocked(self, telegram_id: int) -> bool:
        async with self.pool.acquire() as conn:
            result = await conn.fetchval('''
                SELECT is_blocked FROM users 
                WHERE telegram_id = $1
            ''', telegram_id)
            return result or False

    async def set_blocked(self, telegram_id: int, is_blocked: bool):
        async with self.pool.acquire() as conn:
            await conn.execute('''
                UPDATE users 
                SET is_blocked = $2 
                WHERE telegram_id = $1
            ''', telegram_id, is_blocked)

    async def get_stats(self):
        async with self.pool.acquire() as conn:
            stats = {}
            
            # Total users
            stats['total_users'] = await conn.fetchval(
                'SELECT COUNT(*) FROM users'
            )
            
            # Active users (who have generated images)
            stats['active_users'] = await conn.fetchval(
                'SELECT COUNT(DISTINCT user_id) FROM images'
            )
            
            # Total images
            stats['total_images'] = await conn.fetchval(
                'SELECT COUNT(*) FROM images'
            )
            
            # Images created today
            stats['images_today'] = await conn.fetchval('''
                SELECT COUNT(*) FROM images 
                WHERE DATE(created_at) = CURRENT_DATE
            ''')
            
            # Blocked users
            stats['blocked_users'] = await conn.fetchval(
                'SELECT COUNT(*) FROM users WHERE is_blocked = TRUE'
            )
            
            # Admin count
            stats['admin_count'] = await conn.fetchval(
                'SELECT COUNT(*) FROM users WHERE is_admin = TRUE'
            )
            
            return stats

    async def get_users_paginated(self, offset: int = 0, limit: int = 25):
        async with self.pool.acquire() as conn:
            # Get total count
            total_count = await conn.fetchval('SELECT COUNT(*) FROM users')
            
            # Get users for current page
            users = await conn.fetch('''
                SELECT * FROM users 
                ORDER BY created_at DESC
                LIMIT $1 OFFSET $2
            ''', limit, offset)
            
            return users, total_count

    async def get_all_users(self):
        """Get all users from the database"""
        async with self.pool.acquire() as conn:
            users = await conn.fetch("""
                SELECT telegram_id, username, first_name, last_name, is_admin, is_blocked 
                FROM users 
                ORDER BY created_at DESC
            """)
            return users

db = Database()
