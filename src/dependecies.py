from starlette.templating import Jinja2Templates

from src.data_publisher import DataPublisher
from src.settings import Settings
from src.websocket import WebSocketHandler

_settings = Settings.load_from_yaml("config.yml")

_feed_publisher = DataPublisher()
_feed_handler = WebSocketHandler(_settings, _feed_publisher)

_admin_publisher = DataPublisher()
_admin_feed_handler = WebSocketHandler(_settings, _admin_publisher)

_templates = Jinja2Templates(directory="templates")


async def get_settings() -> Settings:
    return _settings


async def get_feed_publisher() -> DataPublisher:
    return _feed_publisher


async def get_feed_handler() -> WebSocketHandler:
    return _feed_handler


async def get_admin_publisher() -> DataPublisher:
    return _admin_publisher


async def get_admin_feed_handler() -> WebSocketHandler:
    return _admin_feed_handler


async def get_templates() -> Jinja2Templates:
    return _templates
