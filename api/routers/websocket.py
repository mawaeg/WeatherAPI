from typing import Annotated

from fastapi import APIRouter, Depends, WebSocket, WebSocketDisconnect, WebSocketException, status

from api.models.database_models import DBUser
from api.utils.security import get_current_user_ws
from api.utils.websocket_connection_handler import WebsocketHandler, get_websocket_handler

websocket_router = APIRouter()


@websocket_router.websocket("/ws")
async def websocket_endpoint(
    websocket: WebSocket,
    current_user: Annotated[DBUser, Depends(get_current_user_ws)],
    ws_handler: Annotated[WebsocketHandler, Depends(get_websocket_handler)],
):
    if not ws_handler.add(current_user, websocket):
        return await websocket.close(1008)

    await websocket.accept()
    await websocket.send_json({"message": "Hello World!"})

    print(f"Accepted connection with {current_user.username}")
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        ws_handler.remove(current_user)
