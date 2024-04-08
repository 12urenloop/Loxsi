import httpx
from fastapi import APIRouter, Depends, HTTPException, Request, WebSocket
from fastapi.responses import HTMLResponse
from fastapi.security import HTTPBasicCredentials
from fastapi.templating import Jinja2Templates
from starlette.status import (
    HTTP_202_ACCEPTED,
    HTTP_401_UNAUTHORIZED,
    HTTP_409_CONFLICT,
    HTTP_502_BAD_GATEWAY,
)

from fetcher import Fetcher
from models import FreezeTime, LapSource, Message
from settings import Settings
from websocket import WebSocketHandler


class ApiRouter(APIRouter):
    """_summary_
    Class responsible for defining the API routes and handling incoming requests.
    """

    _settings: Settings
    _feed_handler: WebSocketHandler
    _admin_feed_handler: WebSocketHandler
    _fetcher: Fetcher
    _templates: Jinja2Templates

    def setup(
            self,
            settings: Settings,
            feed_handler: WebSocketHandler,
            admin_feed_handler: WebSocketHandler,
            fetcher: Fetcher,
    ):
        """
        Initializes a new instance of the ApiRouter class.

        Args:
            settings (Settings): The settings object containing configuration options.
            feed_handler (WebSocketHandler): Websocket handler for the feed.
            admin_feed_handler (WebSocketHandler): Websocket handler for the admin feed.
            fetcher (Fetcher): Class responsible for fetching data from the Telraam API.
        """
        super().__init__()

        self.settings = settings
        self._feed_handler = feed_handler
        self._admin_feed_handler = admin_feed_handler
        self._fetcher = fetcher
        self._templates = Jinja2Templates(directory="templates")

    async def _admin_auth(self, credentials: HTTPBasicCredentials):
        """
        Authenticate the admin user using HTTP basic authentication.

        Args:
            credentials (HTTPBasicCredentials): The credentials provided by the client.

        Raises:
            HTTPException: If the credentials are invalid.

        Returns:
            None: If the credentials are valid.
        """
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


router = APIRouter()
apiRouter = ApiRouter()


@router.get("/ping")
async def _ping(request: Request):
    return {"message": "Pong!"}


@router.post(
    "/api/use/{id}",
    dependencies=[Depends(apiRouter._admin_auth)],
)
async def _post_lap_source(id: int):
    try:
        lap_sources: list[dict] = await apiRouter._fetcher.get_lap_sources()
        lap_sources_by_id: dict[int, LapSource] = {
            ls.id: ls for ls in [LapSource(**ls) for ls in lap_sources]
        }
        await apiRouter._admin_publisher.publish("telraam-health", "good")
        if id in lap_sources_by_id:
            lap_source = lap_sources_by_id[id]
            await apiRouter._admin_publisher.publish(
                "active-source", lap_source.model_dump()
            )
            apiRouter._settings.source.id = lap_source.id
            apiRouter._settings.source.name = lap_source.name
            apiRouter._settings.persist()
        else:
            raise HTTPException(
                status_code=HTTP_409_CONFLICT, detail="Invalid LapSource Id"
            )
        return ["ok"]
    except httpx.ConnectError:
        await apiRouter._admin_publisher.publish("telraam-health", "bad")
        raise HTTPException(
            status_code=HTTP_502_BAD_GATEWAY, detail="Can't reach data server"
        )


@router.post(
    "/api/message",
    status_code=HTTP_202_ACCEPTED,
    dependencies=[Depends(apiRouter._admin_auth)],
)
async def _post_message(message: Message):
    print("message", flush=True)
    apiRouter._settings.message = message.message
    apiRouter._settings.persist()
    await apiRouter._feed_publisher.publish("message", message.message)


@router.post(
    "/api/freeze",
    status_code=HTTP_202_ACCEPTED,
    dependencies=[Depends(apiRouter._admin_auth)],
)
async def _post_freeze(time: FreezeTime):
    apiRouter._settings.freeze = time.time
    apiRouter._settings.persist()
    await apiRouter._admin_publisher.publish("freeze", time.time)


@router.delete(
    "/api/freeze",
    status_code=HTTP_202_ACCEPTED,
    dependencies=[Depends(apiRouter._admin_auth)],
)
async def _delete_freeze():
    apiRouter._settings.freeze = None
    apiRouter._settings.persist()
    await apiRouter._admin_publisher.publish("freeze", None)


@router.get("/admin", response_class=HTMLResponse)
async def _admin(request: Request, _=apiRouter._admin_auth):
    return apiRouter._templates.TemplateResponse("admin.html", {"request": request})


@router.websocket("/feed")
async def _feed(websocket: WebSocket):
    await apiRouter._feed_handler.connect(websocket)


@router.websocket("/admin/feed")
async def _feed_admin(websocket: WebSocket):
    await apiRouter._admin_feed_handler.connect(websocket)
