from datetime import datetime, timedelta
from os.path import isfile
import json
import logging

from src.data_publisher import DataPublisher

class Storeman:

    def __init__(self, feed_publisher: DataPublisher ) -> None:
        self.lastSave: datetime | None = None
        self._feed_publisher: DataPublisher = feed_publisher
        self.logger = logging.getLogger("uvicorn")

    async def storeScores(self, counts: list[dict]):
        if self.lastSave and self.lastSave > (datetime.now() - timedelta(minutes=10)):
            return
        self.lastSave = datetime.now()
        self.logger.info("Storing counts to cache")
        with open("tmp/counts.json", "+w") as f:
            f.write(json.dumps(counts))

    async def loadScores(self):
        if not isfile("tmp/counts.json"):
            self.logger.warning("No counts loaded from cache")
            return
        
        with open("tmp/counts.json", "+r") as f:
            counts = json.load(f)
            await self._feed_publisher.publish("counts", counts)

