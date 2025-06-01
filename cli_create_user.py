import asyncio
from argparse import ArgumentParser

from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession

from api.models.database_models import DBUser
from api.utils.database import dispose_database, get_engine, get_session
from api.utils.security import get_password_hash


async def create_user(username: str, password: str, superuser: bool):
    hashed_password: str = get_password_hash(password)

    engine: AsyncEngine = await get_engine()
    session: AsyncSession
    async for session in get_session(engine):
        try:
            session.add(DBUser(username=username, hashed_password=hashed_password, superuser=superuser))
            await session.commit()
        except IntegrityError:
            print(f"User with the username {username} already exists. Please try again.")
        else:
            print(f"User with the username {username} was successfully created.")
    await dispose_database()


if __name__ == "__main__":
    parser: ArgumentParser = ArgumentParser(
        description="Add a new user to the database. Useful if no user was yet created."
    )
    parser.add_argument("--username", required=True, help="The username of the user you want to create.")
    parser.add_argument("--password", required=True, help="The password of the user you want to create.")
    parser.add_argument("--superuser", action="store_true", help="If set, the user will be created as a superuser.")

    args = parser.parse_args()

    asyncio.run(create_user(args.username, args.password, args.superuser))
