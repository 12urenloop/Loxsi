from fastapi import APIRouter, Request, WebSocket

from settings import Settings
from websocket import WebSocketHandler, WebSocketHandlerAdmin


class ApiRouter(APIRouter):
    _settings: Settings
    _feed_handler: WebSocketHandler
    _admin_feed_handler: WebSocketHandlerAdmin

    def __init__(
        self,
        settings: Settings,
        feed_handler: WebSocketHandler,
        admin_feed_handler: WebSocketHandlerAdmin,
    ):
        super().__init__()

        self.settings = settings
        self._feed_handler = feed_handler
        self._admin_feed_handler = admin_feed_handler

    def add_routes(self):

        @self.get("/ping")
        async def _ping(request: Request):
            return {"message": "Pong!"}

        @self.websocket("/feed")
        async def _feed(websocket: WebSocket):
            await self._feed_handler.connect(websocket)

        @self.websocket("/admin/feed")
        async def _admin(websocket: WebSocket):
            await self._admin_feed_handler.connect(websocket)

        return self