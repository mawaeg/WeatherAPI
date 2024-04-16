import httpx
from fastapi import status


def assert_not_authenticated(response: httpx.Response):
    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    assert response.json() == {"detail": "Not authenticated"}


def assert_invalid_credentials(response: httpx.Response):
    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    assert response.json() == {"detail": "Could not validate credentials"}


def assert_missing_privileges(response: httpx.Response):
    assert response.status_code == status.HTTP_403_FORBIDDEN
    assert response.json() == {"detail": "The user doesn't have enough privileges"}


def assert_user_already_exists(response: httpx.Response):
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.json() == {"detail": "A user with that name already exists."}
