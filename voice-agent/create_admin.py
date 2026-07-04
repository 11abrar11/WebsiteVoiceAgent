import asyncio
import os
import sys
import bcrypt
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from dotenv import load_dotenv

# Add the app directory to the sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.models.admin import Admin
from app.database.connection import DATABASE_URL

load_dotenv()

async def create_admin(username, password):
    engine = create_async_engine(DATABASE_URL, echo=False)
    Session = async_sessionmaker(engine)

    async with Session() as session:
        from sqlalchemy import select
        result = await session.execute(select(Admin).where(Admin.username == username))
        existing_admin = result.scalar_one_or_none()

        if existing_admin:
            print(f"Admin '{username}' already exists!")
            return

        salt = bcrypt.gensalt()
        hashed_password = bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')

        admin = Admin(
            username=username,
            password_hash=hashed_password,
            role="superadmin"
        )
        session.add(admin)
        await session.commit()
        print(f"Successfully created admin user: {username}")

    await engine.dispose()

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python create_admin.py <username> <password>")
        sys.exit(1)

    username = sys.argv[1]
    password = sys.argv[2]
    
    asyncio.run(create_admin(username, password))
