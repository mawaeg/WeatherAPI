from datetime import timedelta
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status

from models.database_models import DBUser
from models.response_models import Token
from utils.security import authenticate_user, create_access_token

auth_router = APIRouter(tags=["Authentication"])


@auth_router.post("/token")
async def fetch_access_token(user: Annotated[DBUser | None, Depends(authenticate_user)]) -> Token:
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=30)
    access_token = create_access_token(data={"sub": user.username}, expires_delta=access_token_expires)
    return Token(access_token=access_token, token_type="bearer")
