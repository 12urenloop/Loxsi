from typing import Annotated, Optional

from fastapi import Depends, HTTPException
from fastapi.security import HTTPBasicCredentials, HTTPBasic
from starlette.requests import Request
from starlette.status import HTTP_401_UNAUTHORIZED
from starlette.websockets import WebSocket

from src.dependecies import get_settings
from src.settings import Settings

# Subclass of HTTPBasic that also works with the initial ws request
class FixedHTTPBasic(HTTPBasic):
    async def __call__(  # type: ignore
        self,
        request: Request = None,
        websocket: WebSocket = None, # WebSocket is a subclass of Request, it represents the original ws http request
    ) -> Optional[HTTPBasicCredentials]:
        assert request is not None or websocket is not None
        return await super().__call__(request=(websocket if websocket else request))

security = FixedHTTPBasic()

async def is_admin(
        credentials: Annotated[HTTPBasicCredentials, Depends(security)],
        settings: Annotated[Settings, Depends(get_settings)]
):
    invalid_credentials = HTTPException(
        status_code=HTTP_401_UNAUTHORIZED, # Ignored and gives 500 instead when failing to auth for a websocket
        detail="Invalid Credentials",
        headers={"WWW-Authenticate": "Basic"},
    )

    if not credentials:
        raise invalid_credentials

    if (
            credentials.password == settings.admin.password
            and credentials.username == settings.admin.name
    ):
        return

    raise invalid_credentials
