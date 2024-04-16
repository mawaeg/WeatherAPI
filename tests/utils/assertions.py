import httpx
from fastapi import HTTPException, status


def assert_HTTPException_EQ(response: httpx.Response, error: HTTPException):
    assert response.status_code == error.status_code
    assert response.json() == {"detail": error.detail}


NOT_AUTHENTICATED_EXCEPTION = HTTPException(
    status.HTTP_401_UNAUTHORIZED,
    "Not authenticated",
)
