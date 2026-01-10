"""
PostgreSQL Checkpointer for LangGraph
Provides persistent state storage for long-running workflows
"""

import os
from typing import Optional
from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver


async def create_checkpointer() -> AsyncPostgresSaver:
    """
    Create PostgreSQL checkpointer for LangGraph state persistence

    This enables:
    1. Workflows to pause and resume (Human-in-the-Loop)
    2. State recovery after crashes
    3. Multi-hour/multi-day workflows
    4. Concurrent meeting processing

    Connection string format:
        postgresql+asyncpg://user:password@host:port/database
    """
    connection_string = os.getenv(
        "DATABASE_URL",
        "postgresql+asyncpg://moa:moa@localhost:5432/moa"
    )

    # Convert psycopg2 connection string to asyncpg if needed
    if "postgresql://" in connection_string and "asyncpg" not in connection_string:
        connection_string = connection_string.replace(
            "postgresql://",
            "postgresql+asyncpg://"
        )

    # Create checkpointer
    checkpointer = AsyncPostgresSaver.from_conn_string(connection_string)

    # Setup schema (creates checkpoint tables if they don't exist)
    await checkpointer.setup()

    return checkpointer


# Singleton instance
_checkpointer: Optional[AsyncPostgresSaver] = None


async def get_checkpointer() -> AsyncPostgresSaver:
    """
    Get or create the global checkpointer instance

    Returns:
        Configured AsyncPostgresSaver instance
    """
    global _checkpointer

    if _checkpointer is None:
        _checkpointer = await create_checkpointer()

    return _checkpointer
