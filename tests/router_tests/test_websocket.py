import asyncio
from typing import Any

import pytest
from fastapi import WebSocketDisconnect
from fastapi.testclient import TestClient

from api.main import app
from api.models.database_models import Sensor, SensorData
from api.utils.database import get_engine
from api.utils.websocket_connection_handler import get_websocket_handler
from tests.utils.fake_db import override_get_engine
from tests.utils.fixtures import superuser_token, token
from tests.utils.sensor_utils import create_sensor

app.dependency_overrides[get_engine] = override_get_engine
client: TestClient = TestClient(app)


def test_ws_connect_no_authentication():
    try:
        with client.websocket_connect("/ws") as _:
            return
    except WebSocketDisconnect as exception:
        assert exception.code == 1008


def test_ws_connect_no_bearer():
    try:
        with client.websocket_connect("/ws", headers={"Authorization": "1234"}) as _:
            return
    except WebSocketDisconnect as exception:
        assert exception.code == 1008


def test_ws_connect_wrong_token(token: str):
    try:
        with client.websocket_connect("/ws", headers={"Authorization": f"Bearer {token}1234"}) as _:
            return
    except WebSocketDisconnect as exception:
        assert exception.code == 1008


@pytest.mark.asyncio
async def test_ws_connect(superuser_token: str):
    ws_handler = get_websocket_handler()
    task = asyncio.get_event_loop().create_task(get_websocket_handler().event_loop())

    sensor: Sensor = await create_sensor(name="TestSensorWS")

    with client.websocket_connect("/ws", headers={"Authorization": f"Bearer {superuser_token}"}) as websocket:
        data = websocket.receive_json()
        assert data == {"message": "Hello World!"}

        data: dict[str, Any] = {
            "id": -1,
            "temperature": 32.1,
            "humidity": 56.78,
            "pressure": 123.45,
            "voltage": 3.45,
            "sensor_id": sensor.id,
        }
        sensor_data: SensorData = SensorData(**data)
        await ws_handler.add_event(sensor_data)

        # As the websocket.receive_json() is synchronous and TestClient does not really work with async ws,
        # the delay is need, so that the ws_handler can run its loop.
        await asyncio.sleep(0.1)

        received_data = websocket.receive_json()
        assert data.get("id") == received_data.get("id")
        assert data.get("temperature") == received_data.get("temperature")
    task.cancel()


# ToDo Investigate performance issue
def test_ws_connect_double_connection(token: str):
    with client.websocket_connect("/ws", headers={"Authorization": f"Bearer {token}"}) as websocket:
        data = websocket.receive_json()
        assert data == {"message": "Hello World!"}

        try:
            with client.websocket_connect("/ws", headers={"Authorization": f"Bearer {token}"}) as _:
                pass
        except WebSocketDisconnect as exception:
            assert exception.code == 1008
