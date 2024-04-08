from src.data_publisher import DataPublisher
from src.settings import Settings


class Task:
    def __init__(self, settings: Settings, feed_publisher: DataPublisher, admin_publisher: DataPublisher):
        self._settings: Settings = settings
        self._feed_publisher: DataPublisher = feed_publisher
        self._admin_publisher: DataPublisher = admin_publisher
