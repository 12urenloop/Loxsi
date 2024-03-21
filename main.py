import asyncio
from contextlib import asynccontextmanager

from fastapi import FastAPI

from api import ApiRouter
from data_publisher import DataPublisher
from settings import Settings
from websocket import WebSocketHandler, WebSocketHandlerAdmin, WebSocketListener

settings = Settings.load_from_yaml("config.yml")

feed_publisher = DataPublisher()
admin_publisher = DataPublisher()

feed_handler = WebSocketHandler(feed_publisher)
admin_feed_handler = WebSocketHandlerAdmin(admin_publisher)
telraam = WebSocketListener(settings.telraam_uri, feed_publisher, admin_publisher)


@asynccontextmanager
async def lifespan(app: FastAPI):
    asyncio.create_task(telraam.start())
    yield


app = FastAPI(
    title="Loxsi",
    description="Data proxy for the Telraam application",
    version="1.0.0",
    lifespan=lifespan,
)

api_router = ApiRouter(settings, feed_handler, admin_feed_handler).add_routes()
app.include_router(api_router)
