from datetime import timedelta
from typing import Annotated

from fastapi import APIRouter, Depends

from api.models.database_models import DBUser
from api.models.response_models import Token
from api.utils.http_exceptions import INCORRECT_PASSWORD
from api.utils.security import authenticate_user, create_access_token

auth_router = APIRouter(tags=["Authentication"])


@auth_router.post("/token")
async def fetch_access_token(user: Annotated[DBUser | None, Depends(authenticate_user)]) -> Token:
    if not user:
        raise INCORRECT_PASSWORD
    access_token_expires = timedelta(minutes=30)
    access_token = create_access_token(data={"sub": user.username}, expires_delta=access_token_expires)
    return Token(access_token=access_token, token_type="bearer")
