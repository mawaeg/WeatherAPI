from sqlalchemy.ext.asyncio import AsyncEngine, create_async_engine
from sqlalchemy.ext.asyncio.session import AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlmodel import SQLModel

from SECRETS import PSQL_URL

engine: AsyncEngine = create_async_engine(PSQL_URL, echo=True, future=True)


async def get_session() -> AsyncSession:
    """
    Creates an Async database session from the engine

    Yields:
        An async session.
    """
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with async_session() as session:
        yield session


async def initialize_database():
    """
    Initializes the database engine and creates all tables.
    """
    async with engine.begin() as connection:
        await connection.run_sync(SQLModel.metadata.create_all)


async def dispose_database():
    """
    Disposes the database engine.
    """
    await engine.dispose()
