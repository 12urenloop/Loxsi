import asyncio
import json
from typing import Dict, override

from websockets import InvalidHandshake
import websockets.exceptions
from fastapi import WebSocket
from fastapi.encoders import jsonable_encoder

from data_publisher import DataPublisher
from settings import Settings


class WebSocketHandler:
    _settings: Settings
    _publisher: DataPublisher

    def __init__(self, settings: Settings, publisher: DataPublisher):
        self._settings = settings
        self._publisher = publisher

    async def connect(self, websocket: WebSocket):
        await websocket.accept()

        queue = await self._publisher.add()

        try:
            await self._handle_connect(queue)
        finally:
            await self._publisher.remove_client(websocket)

    async def _send(self, websocket: WebSocket, queue: asyncio.Queue):
        async def _feed():
            topic, data = await queue.get()
            return (topic, data)

        while True:
            try:
                topic, data = await asyncio.wait_for(
                    _feed(), timeout=self._settings.interval.feed
                )
                await websocket.send_json({topic: jsonable_encoder(data)})
            except asyncio.exceptions.TimeoutError:
                await websocket.send_json({"ping": "pong"})

    async def _handle_connect(self, websocket: WebSocket, queue: asyncio.Queue):
        await self._send(websocket, queue)


class WebSocketHandlerAdmin(WebSocketHandler):

    @override
    async def _handle_connect(self, websocket: WebSocket, queue: asyncio.Queue):
        async def _receive():
            while True:
                message = await websocket.receive_text()
                await self.handle_receive(message)

        receive_task = asyncio.create_task(_receive())
        send_task = asyncio.create_task(self._send(websocket, queue))

        try:
            await asyncio.gather(receive_task, send_task, return_exceptions=True)
        except websockets.exceptions.ConnectionClosedOK as e:
            raise e
        finally:
            receive_task.cancel()
            send_task.cancel()

    async def _handle_receive(self, message: str):
        print(message)


class WebSocketListener:
    _settings: Settings
    _feed_publisher: DataPublisher
    _admin_publisher: DataPublisher

    def __init__(
        self,
        settings: Settings,
        _feed_publisher: DataPublisher,
        _admin_publisher: DataPublisher,
    ):
        self._settings = settings
        self._feed_publisher = _feed_publisher
        self._admin_publisher = _admin_publisher

    async def start(self):
        try:
            async with websockets.connect(self._settings.telraam.ws) as ws:
                await self._admin_publisher.publish("telraam-health", "good")
                while True:
                    try:
                        message = await ws.recv()
                        await self._receive(message)
                    except websockets.exceptions.ConnectionClosed:
                        await self.start()
        except (OSError, InvalidHandshake):
            await self._admin_publisher.publish("telraam-health", "bad")
            await asyncio.sleep(self._settings.interval.ws)
            await self.start()

    async def _receive(self, message: str):
        data: Dict[str, str] = json.loads(message)
        key, value = list(data.items())[0]
        await self._feed_publisher.publish(key, value)


# TODO: Intervals
