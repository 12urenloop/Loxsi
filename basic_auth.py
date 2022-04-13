from fastapi.security import HTTPBasic, HTTPBasicCredentials
from fastapi import Depends
from fastapi.exceptions import HTTPException
from starlette.status import HTTP_401_UNAUTHORIZED

from settings import settings
from typing import Optional

security = HTTPBasic()


async def admin(credentials: Optional[HTTPBasicCredentials] = Depends(security)) -> None:
    invalid_credentials = HTTPException(status_code=HTTP_401_UNAUTHORIZED, detail='Invalid Credentials', headers={"WWW-Authenticate": "Basic"})

    if not credentials:
        raise invalid_credentials

    if credentials.password == settings.admin.password and credentials.username == settings.admin.name:
        return
    else:
        raise invalid_credentials
