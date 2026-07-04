import uvicorn
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routers import voice, auth, dashboard


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Runs on startup: create all DB tables and seed a default admin."""
    from app.database.connection import engine
    from app.database.base import Base

    # Import all models so Base.metadata knows about them
    from app.models.admin import Admin  # noqa: F401
    from app.models.lead import Lead  # noqa: F401
    from app.models.conversation import Conversation  # noqa: F401
    from app.models.message import Message  # noqa: F401
    from app.models.conversation_summary import ConversationSummary  # noqa: F401
    from app.models.meeting import Meeting  # noqa: F401

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    # Seed a default admin if none exists
    from app.database.connection import AsyncSessionLocal
    from app.services.auth_service import hash_password
    from sqlalchemy import select

    async with AsyncSessionLocal() as session:
        result = await session.execute(select(Admin))
        if not result.scalar_one_or_none():
            admin = Admin(
                username="admin",
                password_hash=hash_password("admin123"),
                role="admin",
            )
            session.add(admin)
            await session.commit()
            print(">>> Default admin created: username='admin', password='admin123'")

    print(">>> Database tables ready.")
    yield

    # Shutdown: dispose the engine
    await engine.dispose()


app = FastAPI(title="PP5 Voice Agent API", version="2.0.0", lifespan=lifespan)

# Allow requests from the React frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routers
app.include_router(voice.router, prefix="/api/voice", tags=["Voice"])
app.include_router(auth.router, prefix="/api/admin", tags=["Auth"])
app.include_router(dashboard.router, prefix="/api/admin", tags=["Dashboard"])

@app.get("/health")
def health_check():
    return {"status": "ok", "service": "Voice Agent Backend"}

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8001, reload=False)
