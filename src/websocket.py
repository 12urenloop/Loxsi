import asyncio

import starlette.websockets
from fastapi import WebSocket
from fastapi.encoders import jsonable_encoder

from src.data_publisher import DataPublisher
from src.settings import Settings


class ConnectionTracker:
    """
    Counts the total of active websocket connections
    """

    def __init__(self, admin_publisher: DataPublisher):
        self._count: int = 0
        self._admin_publisher: DataPublisher = admin_publisher

    async def count(self) -> int:
        return self._count

    async def inc(self):
        self._count += 1
        await self._notify()

    async def dec(self):
        self._count -= 1
        await self._notify()

    async def _notify(self):
        await self._admin_publisher.publish('active-connections', self._count)


class WebSocketHandler:
    """
    Handles WebSocket connections and message handling.
    """

    def __init__(
            self,
            settings: Settings,
            publisher: DataPublisher,
            connection_tracker: ConnectionTracker
    ):
        """
        Initializes a new instance of the WebSocket class.

        Args:
            settings (Settings): The settings object containing configuration options.
            publisher (DataPublisher): The data publisher object used for publishing data.
            connection_tracker (ConnectionTracker): Track the connection count.
        """
        self._settings: Settings = settings
        self._publisher: DataPublisher = publisher
        self._connection_tracker: ConnectionTracker = connection_tracker

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
        await self._connection_tracker.inc()

        try:
            await self._send(websocket, queue)
        finally:
            await self._connection_tracker.dec()
            await self._publisher.remove(queue)

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
                try:
                    topic, data = await asyncio.wait_for(
                        _feed(), timeout=self._settings.interval.feed
                    )
                    await websocket.send_json({'topic': topic, 'data': jsonable_encoder(data)})
                except asyncio.exceptions.TimeoutError:
                    await websocket.send_json({'ping': 'pong'})
                except Exception as e:
                    raise e
            except starlette.websockets.WebSocketDisconnect:
                return
            except Exception as e:
                print(e)
                return
