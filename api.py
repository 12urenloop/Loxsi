from typing import Dict
from fastapi import APIRouter, Depends, HTTPException, Request, WebSocket
from fastapi.responses import HTMLResponse
from fastapi.security import HTTPBasicCredentials
from fastapi.templating import Jinja2Templates
import httpx

from fetcher import Fetcher
from models import FreezeTime, LapSource, Message
from settings import Settings
from websocket import WebSocketHandler
from starlette.status import (
    HTTP_202_ACCEPTED,
    HTTP_401_UNAUTHORIZED,
    HTTP_409_CONFLICT,
    HTTP_502_BAD_GATEWAY,
)


class ApiRouter(APIRouter):
    _settings: Settings
    _feed_handler: WebSocketHandler
    _admin_feed_handler: WebSocketHandler
    _fetcher: Fetcher
    _templates: Jinja2Templates

    def __init__(
        self,
        settings: Settings,
        feed_handler: WebSocketHandler,
        admin_feed_handler: WebSocketHandler,
        fetcher: Fetcher,
    ):
        super().__init__()

        self.settings = settings
        self._feed_handler = feed_handler
        self._admin_feed_handler = admin_feed_handler
        self._fetcher = fetcher
        self._templates = Jinja2Templates(directory="templates")

    def add_routes(self):

        @self.get("/ping")
        async def _ping(request: Request):
            return {"message": "Pong!"}

        @self.post(
            "/api/use/{id}",
            dependencies=[Depends(self._admin_auth)],
        )
        async def _post_lap_source(id: int):
            try:
                lap_sources: list[Dict] = await self._fetcher.get_lap_sources()
                lap_sources_by_id: Dict[int, LapSource] = {
                    ls.id: ls for ls in [LapSource(**ls) for ls in lap_sources]
                }
                await self._admin_publisher.publish("telraam-health", "good")
                if id in lap_sources_by_id:
                    lap_source = lap_sources_by_id[id]
                    await self._admin_publisher.publish(
                        "active-source", lap_source.model_dump()
                    )
                    self._settings.source.id = lap_source.id
                    self._settings.source.name = lap_source.name
                    self._settings.persist()
                else:
                    raise HTTPException(
                        status_code=HTTP_409_CONFLICT, detail="Invalid LapSource Id"
                    )
                return ["ok"]
            except httpx.ConnectError:
                await self._admin_publisher.publish("telraam-health", "bad")
                raise HTTPException(
                    status_code=HTTP_502_BAD_GATEWAY, detail="Can't reach data server"
                )

        @self.post(
            "/api/message",
            status_code=HTTP_202_ACCEPTED,
            dependencies=[Depends(self._admin_auth)],
        )
        async def _post_message(message: Message):
            self._settings.message = message.message
            self._settings.persist()
            await self._feed_publisher.publish("message", message.message)

        @self.post(
            "/api/freeze",
            status_code=HTTP_202_ACCEPTED,
            dependencies=[Depends(self._admin_auth)],
        )
        async def _post_freeze(time: FreezeTime):
            self._settings.freeze = time.time
            self._settings.persist()
            await self._admin_publisher.publish("freeze", time.time)

        @self.delete(
            "/api/freeze",
            status_code=HTTP_202_ACCEPTED,
            dependencies=[Depends(self._admin_auth)],
        )
        async def _delete_freeze():
            self._settings.freeze = None
            self._settings.persist()
            await self._admin_publisher.publish("freeze", None)

        @self.get("/admin", response_class=HTMLResponse)
        async def _admin(request: Request, _=self._admin_auth):
            return self._templates.TemplateResponse("admin.html", {"request": request})

        @self.websocket("/feed")
        async def _feed(websocket: WebSocket):
            await self._feed_handler.connect(websocket)

        @self.websocket("/admin/feed")
        async def _feed_admin(websocket: WebSocket):
            await self._admin_feed_handler.connect(websocket)

        return self

    async def _admin_auth(self, credentials: HTTPBasicCredentials):
        invalid_credentials = HTTPException(
            status_code=HTTP_401_UNAUTHORIZED,
            detail="Invalid Credentials",
            headers={"WWW-Authenticate": "Basic"},
        )

        if not credentials:
            raise invalid_credentials

        if (
            credentials.password == self._settings.admin.password
            and credentials.username == self._settings.admin.name
        ):
            return

        raise invalid_credentials
