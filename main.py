import asyncio
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from api import ApiRouter
from data_publisher import DataPublisher
from fetcher import Fetcher
from settings import Settings
from websocket import WebSocketHandler, WebSocketHandlerAdmin, WebSocketListener

settings = Settings.load_from_yaml("config.yml")

feed_publisher = DataPublisher()
admin_publisher = DataPublisher()

feed_handler = WebSocketHandler(settings, feed_publisher)
admin_feed_handler = WebSocketHandlerAdmin(settings, admin_publisher)
telraam = WebSocketListener(settings, feed_publisher, admin_publisher)

fetcher = Fetcher(settings, feed_publisher, admin_publisher)


@asynccontextmanager
async def lifespan(app: FastAPI):
    asyncio.create_task(telraam.start())
    asyncio.create_task(fetcher.fetch())
    await admin_publisher.publish("active-source", settings.source.model_dump())
    yield


app = FastAPI(
    title="Loxsi",
    description="Data proxy for the Telraam application",
    version="1.0.0",
    lifespan=lifespan,
)

app.mount("/static", StaticFiles(directory="static"), name="static")
api_router = ApiRouter(settings, feed_handler, admin_feed_handler, fetcher).add_routes()
app.include_router(api_router)
