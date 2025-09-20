from ssl import SSLContext
import asyncpg
import ssl
from typing import Optional
from app.config import settings

db_pool: Optional[asyncpg.Pool] = None  # global pool variable

async def init_db_pool() -> None:
    global db_pool
    if db_pool is None:
        ssl_context: SSLContext = ssl.create_default_context()
        ssl_context.check_hostname = False  # Supabase doesn't need hostname validation
        ssl_context.verify_mode = ssl.CERT_NONE  # Accept Supabase's cert

        # Explicitly assign to typed variable first
        # noinspection PyUnresolvedReferences
        pool: asyncpg.Pool = await asyncpg.create_pool(
            dsn=settings.SUPABASE_DB_DSN,
            min_size=settings.SUPABASE_DB_MIN_SIZE,
            max_size=settings.SUPABASE_DB_MAX_SIZE,
            ssl=ssl_context
        )

        db_pool = pool  # assign to global

async def close_db_pool():
    global db_pool
    if db_pool:
        await db_pool.close()
        db_pool = None