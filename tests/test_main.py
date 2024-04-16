import httpx
import pytest
from fastapi.testclient import TestClient
from pytest_mock import MockerFixture

from api.main import app, dispose_db, initialize_db

client: TestClient = TestClient(app)


def test_root_route():
    """
    Asserts the api is running and response correctly to the root route.
    """
    response: httpx.Response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"message": "Hello World!"}


@pytest.mark.asyncio
async def test_startup_event(mocker: MockerFixture):
    """
    Asserts that the database gets initialized during the startup of the application.
    """
    initialize_db_mock = mocker.patch("api.main.initialize_database")

    await initialize_db()

    initialize_db_mock.assert_called_once()


@pytest.mark.asyncio
async def test_shutdown_event(mocker: MockerFixture):
    """
    Asserts that the database gets disposed during the shutdown of the application.
    """
    initialize_db_mock = mocker.patch("api.main.dispose_database")

    await dispose_db()

    initialize_db_mock.assert_called_once()
