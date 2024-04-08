from typing import Annotated

import httpx
from fastapi import APIRouter, Depends, HTTPException, Request, WebSocket
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from starlette.status import (
    HTTP_202_ACCEPTED,
    HTTP_409_CONFLICT,
    HTTP_502_BAD_GATEWAY,
    HTTP_200_OK,
)

from src.auth import is_admin
from src.data_publisher import DataPublisher
from src.dependecies import (
    get_settings, get_admin_publisher, get_templates, get_feed_publisher, get_feed_handler,
    get_admin_feed_handler
)
from src.models import FreezeTime, LapSource, Message
from src.settings import Settings
from src.telraam import TelraamClient
from src.websocket import WebSocketHandler

router = APIRouter()


@router.get("/ping")
async def _ping(_request: Request):
    return {"message": "Pong!"}


@router.post("/api/use/{id}", dependencies=[Depends(is_admin)])
async def _post_lap_source(
        lap_source_id: int,
        settings: Annotated[Settings, Depends(get_settings)],
        admin_publisher: Annotated[DataPublisher, Depends(get_admin_publisher)]
):
    try:
        lap_sources: list[dict]
        async with TelraamClient(settings, admin_publisher) as client:
            lap_sources = await client.get_lap_sources()

        lap_sources_by_id: dict[int, LapSource] = {
            ls.id: ls for ls in [LapSource(**ls) for ls in lap_sources]
        }
        await admin_publisher.publish("telraam-health", "good")
        if lap_source_id in lap_sources_by_id:
            lap_source = lap_sources_by_id[lap_source_id]
            await admin_publisher.publish(
                "active-source", lap_source.model_dump()
            )
            settings.source.id = lap_source.id
            settings.source.name = lap_source.name
            settings.persist()
        else:
            raise HTTPException(
                status_code=HTTP_409_CONFLICT, detail="Invalid LapSource Id"
            )
        return ["ok"]
    except httpx.ConnectError:
        await admin_publisher.publish("telraam-health", "bad")
        raise HTTPException(
            status_code=HTTP_502_BAD_GATEWAY, detail="Can't reach data server"
        )


@router.post("/api/message", status_code=HTTP_202_ACCEPTED, dependencies=[Depends(is_admin)])
async def _post_message(
        message: Message,
        settings: Annotated[Settings, Depends(get_settings)],
        feed_publisher: Annotated[Settings, Depends(get_feed_publisher)]
):
    settings.message = message.message
    settings.persist()
    await feed_publisher.publish("message", message.message)


@router.post("/api/freeze", status_code=HTTP_202_ACCEPTED, dependencies=[Depends(is_admin)])
async def _post_freeze(
        time: FreezeTime,
        settings: Annotated[Settings, Depends(get_settings)],
        admin_publisher: Annotated[DataPublisher, Depends(get_admin_publisher)]
):
    settings.freeze = time.time
    settings.persist()
    await admin_publisher.publish("freeze", time.time)


@router.delete("/api/freeze", status_code=HTTP_202_ACCEPTED, dependencies=[Depends(is_admin)], )
async def _delete_freeze(
        settings: Annotated[Settings, Depends(get_settings)],
        admin_publisher: Annotated[DataPublisher, Depends(get_admin_publisher)]
):
    settings.freeze = None
    settings.persist()
    await admin_publisher.publish("freeze", None)


@router.get("/admin", status_code=HTTP_200_OK, dependencies=[Depends(is_admin)], response_class=HTMLResponse)
async def _admin(
        request: Request,
        templates: Annotated[Jinja2Templates, Depends(get_templates)],
):
    print("Got here!", flush=True)
    return templates.TemplateResponse("admin.html", {"request": request})


@router.websocket("/feed")
async def _feed(
        websocket: WebSocket,
        feed_handler: Annotated[WebSocketHandler, Depends(get_feed_handler)]
):
    await feed_handler.connect(websocket)


@router.websocket("/admin/feed")
async def _feed_admin(
        websocket: WebSocket,
        admin_feed_handler: Annotated[WebSocketHandler, Depends(get_admin_feed_handler)]
):
    await admin_feed_handler.connect(websocket)
