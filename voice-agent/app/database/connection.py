"""
Database connection module.
Provides async SQLAlchemy engine and session factory for PostgreSQL.
"""
import os
from dotenv import load_dotenv
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession

load_dotenv()

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql+asyncpg://admin:adminpassword@localhost:5432/voiceagentdb"
)

engine = create_async_engine(DATABASE_URL, echo=True)

AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
)

import time
from sqlalchemy import event
from contextvars import ContextVar

PERFORMANCE_PROFILING = os.getenv("PERFORMANCE_PROFILING", "False").lower() in ("true", "1")
sql_metrics = ContextVar("sql_metrics", default={"queries": 0, "transactions": 0, "time": 0.0})

if PERFORMANCE_PROFILING:
    @event.listens_for(engine.sync_engine, "before_cursor_execute")
    def before_cursor_execute(conn, cursor, statement, parameters, context, executemany):
        conn.info.setdefault("query_start_time", []).append(time.perf_counter())

    @event.listens_for(engine.sync_engine, "after_cursor_execute")
    def after_cursor_execute(conn, cursor, statement, parameters, context, executemany):
        times = conn.info.get("query_start_time", [])
        if times:
            t0 = times.pop(-1)
            metrics = sql_metrics.get()
            metrics["queries"] += 1
            metrics["time"] += (time.perf_counter() - t0)
            
    @event.listens_for(engine.sync_engine, "commit")
    def receive_commit(conn):
        metrics = sql_metrics.get()
        metrics["transactions"] += 1


async def get_session() -> AsyncSession:
    """Dependency that provides an async database session."""
    async with AsyncSessionLocal() as session:
        yield session
