import asyncio
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from fastapi.staticfiles import StaticFiles
from starlette.responses import PlainTextResponse

from src.dependecies import get_settings, get_admin_publisher, get_feed_publisher, get_storeman
from src.routes import router
from src.tasks.fetcher import Fetcher
from src.tasks.listener import WebSocketListener


# Start background tasks when the app starts
@asynccontextmanager
async def lifespan(_app: FastAPI):
    settings = await get_settings()
    feed_publisher = await get_feed_publisher()
    admin_publisher = await get_admin_publisher()
    storeman = await get_storeman()

    await storeman.loadScores()

    asyncio.create_task(WebSocketListener(settings, feed_publisher, admin_publisher).start())
    asyncio.create_task(Fetcher(settings, feed_publisher, admin_publisher, storeman).fetch())

    await feed_publisher.publish("frozen", settings.site.freeze is not None)
    await feed_publisher.publish("message", settings.site.message)
    await admin_publisher.publish("active-source", settings.source.dict())

    yield  # Signal that the startup can go ahead


app = FastAPI(
    title="Loxsi",
    description="Data proxy for the Telraam application",
    version="0.6.9",
    lifespan=lifespan,
)

app.mount("/static", StaticFiles(directory="static"), name="static")
app.include_router(router)


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request, exc):
    print(exc.with_traceback(), flush=True)
    return PlainTextResponse(str(exc), status_code=400)
