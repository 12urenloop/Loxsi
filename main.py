from api import ApiRouter
from fastapi import FastAPI
from websocket import WebSocketHandler, WebSocketHandlerAdmin

from settings import Settings

app = FastAPI()

settings = Settings.load_from_yaml("config.yml")

feed_handler = WebSocketHandler()
admin_feed_handler = WebSocketHandlerAdmin()

api_router = ApiRouter(settings, feed_handler, admin_feed_handler).add_routes()
app.include_router(api_router)
