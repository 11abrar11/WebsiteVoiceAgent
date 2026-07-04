"""
Authentication router – login endpoint for admin users.
"""
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.connection import get_session
from app.models.admin import Admin
from app.services.auth_service import verify_password, create_access_token

router = APIRouter()


class LoginRequest(BaseModel):
    username: str
    password: str


class LoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


@router.post("/login", response_model=LoginResponse)
async def admin_login(body: LoginRequest, session: AsyncSession = Depends(get_session)):
    """Authenticate an admin and return a JWT."""
    result = await session.execute(
        select(Admin).where(Admin.username == body.username)
    )
    admin = result.scalar_one_or_none()

    if not admin or not verify_password(body.password, admin.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password",
        )

    token = create_access_token(data={"sub": admin.username, "role": admin.role})
    return LoginResponse(access_token=token)
