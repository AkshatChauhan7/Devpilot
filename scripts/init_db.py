#!/usr/bin/env python3
"""Database initialization script."""
import asyncio
import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent / "backend"))

from app.core.config import settings
from app.core.database import init_db, engine
from app.models import *  # noqa: F403,F401


async def main():
    """Initialize database tables."""
    print(f"Initializing database: {settings.DATABASE_URL}")

    try:
        await init_db()
        print("Database tables created successfully!")
    except Exception as e:
        print(f"Error initializing database: {e}")
        sys.exit(1)
    finally:
        await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())