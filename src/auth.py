from typing import Annotated

from fastapi import Depends, HTTPException
from fastapi.security import HTTPBasicCredentials, HTTPBasic
from starlette.status import HTTP_401_UNAUTHORIZED

from src.dependecies import get_settings
from src.settings import Settings

security = HTTPBasic()


async def is_admin(
        credentials: Annotated[HTTPBasicCredentials, Depends(security)],
        settings: Annotated[Settings, Depends(get_settings)]
):
    invalid_credentials = HTTPException(
        status_code=HTTP_401_UNAUTHORIZED,
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
