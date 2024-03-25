import asyncio
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from api import ApiRouter
from data_publisher import DataPublisher
from fetcher import Fetcher
from settings import Settings
from websocket import WebSocketHandler, WebSocketListener

settings = Settings.load_from_yaml("config.yml")

# Classes to hold all messages to send to the websockets
feed_publisher = DataPublisher()
admin_publisher = DataPublisher()

# Websockets between Loxsi and the frontend
feed_handler = WebSocketHandler(settings, feed_publisher)
admin_feed_handler = WebSocketHandler(settings, admin_publisher)
# Websocket between Loxsi and Telraam
telraam = WebSocketListener(settings, feed_publisher, admin_publisher)

# Fetcher to periodically get data from the Telraam API
fetcher = Fetcher(settings, feed_publisher, admin_publisher)


# Start background tasks when the app starts
@asynccontextmanager
async def lifespan(app: FastAPI):
    asyncio.create_task(telraam.start())
    asyncio.create_task(fetcher.fetch())
    await admin_publisher.publish("active-source", settings.source.model_dump())
    yield  # Signal that the startup can go ahead


app = FastAPI(
    title="Loxsi",
    description="Data proxy for the Telraam application",
    version="1.0.0",
    lifespan=lifespan,
)

app.mount("/static", StaticFiles(directory="static"), name="static")
api_router = ApiRouter(settings, feed_handler, admin_feed_handler, fetcher).add_routes()
app.include_router(api_router)
