import asyncio
import time
import json

from websockets import connect, InvalidHandshake
from websockets.exceptions import ConnectionClosed

from src.data_publisher import DataPublisher
from src.settings import Settings


class WebSocketListener:
    """
    Represents a WebSocket listener that connects to an existing WebSocket server and handles incoming messages.
    """

    def __init__(
        self,
        settings: Settings,
        _feed_publisher: DataPublisher,
        _admin_publisher: DataPublisher,
    ):
        self._settings: Settings = settings
        self._feed_publisher: DataPublisher = _feed_publisher
        self._admin_publisher: DataPublisher = _admin_publisher

    async def start(self):
        """
        Starts the WebSocket connection and continuously receives messages.

        If the connection is closed, it will attempt to reconnect.
        """
        try:
            async with connect(self._settings.telraam.ws) as ws:
                await self._admin_publisher.publish("telraam-health", "good")
                while True:
                    try:
                        message = await ws.recv()
                        await self._receive(message)
                    except ConnectionClosed:
                        await self.start()
        except (OSError, InvalidHandshake):
            await self._admin_publisher.publish("telraam-health", "bad")
            await asyncio.sleep(self._settings.interval.websocket)
            await self.start()

    async def _receive(self, message: str):
        """
        Handles the received message by parsing and publishing the data.

        Args:
            message (str): The received message as a string.
        """
        data: dict[str, str] = json.loads(message)
        if "topic" not in data or "data" not in data:
            raise ValueError("Invalid message from telraam")

        if data["topic"] == "position":
            position_data = data["data"]
            if position_data is None:
                return
            if "positioner" not in position_data or "positions" not in position_data:
                raise ValueError("Invalid message from telraam")
            if self._settings.site.freeze != None and self._settings.site.freeze < (time.time() * 1000):
                for team_data in position_data["positions"]:
                    team_data['progress'] = 0
                    team_data['speed'] = 0
                    team_data['acceleration'] = 0

            await self._feed_publisher.publish(data["topic"], position_data)
            return

        await self._feed_publisher.publish(data["topic"], data["data"])
