import asyncio

import websockets.exceptions
from fastapi import WebSocket
from fastapi.encoders import jsonable_encoder

from src.data_publisher import DataPublisher
from src.settings import Settings


class WebSocketHandler:
    """
    Handles WebSocket connections and message handling.
    """

    _settings: Settings
    _publisher: DataPublisher

    def __init__(self, settings: Settings, publisher: DataPublisher):
        """
        Initializes a new instance of the WebSocket class.

        Args:
            settings (Settings): The settings object containing configuration options.
            publisher (DataPublisher): The data publisher object used for publishing data.

        """
        self._settings = settings
        self._publisher = publisher

    async def connect(self, websocket: WebSocket):
        """
        Connects a WebSocket client and starts handling messages.

        Args:
            websocket (WebSocket): The WebSocket connection object.

        Notes:
            This method accepts the WebSocket connection, adds the client to the data publisher,
            and starts handling messages by calling the `_handle_connect` method.
        """
        await websocket.accept()

        queue = await self._publisher.add()

        try:
            await self._handle_connect(websocket, queue)
        finally:
            await self._publisher.remove(queue)

    async def _handle_connect(self, websocket: WebSocket, queue: asyncio.Queue):
        """
        Handles the WebSocket connection and message handling.

        Args:
            websocket (WebSocket): The WebSocket connection object.
            queue (asyncio.Queue): The queue for receiving messages from the data publisher.

        Notes:
            This method calls the `_send` method to start sending messages to the WebSocket client.
        """
        await self._send(websocket, queue)

    async def _send(self, websocket: WebSocket, queue: asyncio.Queue):
        """
        Sends messages to the WebSocket client.

        Args:
            websocket (WebSocket): The WebSocket connection object.
            queue (asyncio.Queue): The queue for receiving messages from the data publisher.

        Notes:
            This method continuously waits for messages from the queue and sends them to the
            WebSocket client. If the feed timeout is reached, it sends a ping message to keep
            the connection alive.
        """

        async def _feed():
            return await queue.get()

        while True:
            try:
                topic, data = await asyncio.wait_for(
                    _feed(), timeout=self._settings.interval.feed
                )
                await websocket.send_json({'topic': topic, 'data': jsonable_encoder(data)})
            except asyncio.exceptions.TimeoutError:
                await websocket.send_json({"ping": "pong"})
            except websockets.exceptions.ConnectionClosed:
                # Handle unexpected connection closure by reconnecting
                await self.connect(websocket)