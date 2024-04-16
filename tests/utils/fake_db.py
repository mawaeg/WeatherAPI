from sqlalchemy.ext.asyncio import AsyncEngine, create_async_engine
from sqlalchemy.ext.asyncio.session import AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from sqlmodel import SQLModel

fake_engine: AsyncEngine = create_async_engine(
    "sqlite+aiosqlite://",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
async_session_maker = sessionmaker(fake_engine, class_=AsyncSession, expire_on_commit=False)


async def override_get_session() -> AsyncSession:
    async with async_session_maker() as session:
        yield session


async def initialize_fake_database():
    async with fake_engine.begin() as connection:
        await connection.run_sync(SQLModel.metadata.create_all)


async def dispose_fake_database():
    await fake_engine.dispose()
