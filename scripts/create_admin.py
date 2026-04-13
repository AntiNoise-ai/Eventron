"""Create an admin organizer account.

Usage:
    python scripts/create_admin.py admin@example.com mypassword "管理员"

Or from docker:
    docker compose -f docker-compose.prod.yml exec app \
        python scripts/create_admin.py admin@example.com mypassword "管理员"
"""

import asyncio
import sys

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.config import settings
from app.models.organizer import Organizer
from app.services.auth_service import _hash_password


async def create_admin(email: str, password: str, name: str):
    engine = create_async_engine(settings.database_url, echo=False)
    factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with factory() as session:
        # Check if already exists
        from sqlalchemy import select
        result = await session.execute(
            select(Organizer).where(Organizer.email == email)
        )
        existing = result.scalar_one_or_none()
        if existing:
            print(f"⚠️  账号 {email} 已存在 (id={existing.id})")
            await engine.dispose()
            return

        # Hash password
        password_hash = _hash_password(password)

        organizer = Organizer(
            email=email,
            password_hash=password_hash,
            name=name,
            role="admin",
            is_active=True,
        )
        session.add(organizer)
        await session.commit()
        print(f"✅ 管理员账号已创建: {email} (id={organizer.id})")

    await engine.dispose()


if __name__ == "__main__":
    if len(sys.argv) < 4:
        print("用法: python scripts/create_admin.py <email> <password> <name>")
        print("示例: python scripts/create_admin.py admin@eventron.ai P@ssw0rd 管理员")
        sys.exit(1)

    asyncio.run(create_admin(sys.argv[1], sys.argv[2], sys.argv[3]))
