import asyncio

from fastapi import HTTPException, WebSocket
from sqlalchemy.ext.asyncio import AsyncEngine

from api.models.database_models import DatabaseModelBase, DBUser
from api.utils.database import get_engine, get_session
from api.utils.permissions import get_user_read_permissions


class WebsocketHandler:
    def __init__(self):
        self._connections: dict[int, tuple[DBUser, WebSocket]] = {}
        self._message_queue: asyncio.Queue[DatabaseModelBase] = asyncio.Queue()

    def add(self, user: DBUser, websocket: WebSocket) -> bool:
        if not user.id:
            return False
        if self._connections.get(user.id):
            return False

        self._connections[user.id] = (user, websocket)
        return True

    def remove(self, user: DBUser) -> bool:
        if not user.id:
            return False
        if self._connections.pop(user.id, None):
            return True
        return False

    async def event_loop(self):
        engine: AsyncEngine = await get_engine()
        while True:
            event = await self._message_queue.get()
            async for session in get_session(engine):
                for user, websocket in self._connections.values():
                    try:
                        if event.id:
                            await get_user_read_permissions(session, user, event.id)
                            await websocket.send_text(event.model_dump_json())
                    except HTTPException:
                        pass
                self._message_queue.task_done()

    async def add_event(self, data: DatabaseModelBase):
        await self._message_queue.put(data)


_websocket_handler = WebsocketHandler()


def get_websocket_handler() -> WebsocketHandler:
    return _websocket_handler
