from typing import Annotated

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncEngine, create_async_engine
from sqlalchemy.ext.asyncio.session import AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlmodel import SQLModel

from SECRETS import PSQL_URL

base_engine: AsyncEngine = create_async_engine(PSQL_URL, echo=True, future=True)


async def get_engine() -> AsyncEngine:
    return base_engine  # pragma: no cover: Real database access cannot be properly tested


async def get_session(engine: Annotated[AsyncEngine, Depends(get_engine)]) -> AsyncSession:
    """
    Creates an Async database session from the engine

    Yields:
        An async session.
    """
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with async_session() as session:
        yield session


async def initialize_database():  # pragma: no cover: Real database access cannot be properly tested
    """
    Initializes the database engine and creates all tables.
    """
    async with base_engine.begin() as connection:
        await connection.run_sync(SQLModel.metadata.create_all)


async def dispose_database():  # pragma: no cover: Real database access cannot be properly tested
    """
    Disposes the database engine.
    """
    await base_engine.dispose()
