import asyncio
from typing import override

from websockets import InvalidHandshake
import websockets.exceptions
from fastapi import WebSocket
from fastapi.encoders import jsonable_encoder

from data_publisher import DataPublisher


class WebSocketHandler:
    _publisher: DataPublisher

    def __init__(self, publisher: DataPublisher) -> None:
        self._publisher = publisher

    async def connect(self, websocket: WebSocket):
        await websocket.accept()

        queue = await self._publisher.add()

        try:
            await self._handle_connect(queue)
        finally:
            await self._publisher.remove_client(websocket)

    async def _send(websocket: WebSocket, queue: asyncio.Queue):
        async def _feed():
            topic, data = await queue.get()
            return (topic, data)

        while True:
            try:
                topic, data = await asyncio.wait_for(_feed(), timeout=3)
                await websocket.send_json(
                    {"topic": topic, "data": jsonable_encoder(data)}
                )
            except asyncio.exceptions.TimeoutError:
                await websocket.send_json({"topic": "ping", "data": "ping"})

    async def _handle_connect(self, websocket: WebSocket, queue: asyncio.Queue):
        await self._send(websocket, queue)


class WebSocketHandlerAdmin(WebSocketHandler):

    @override
    async def _handle_connect(self, websocket: WebSocket, queue: asyncio.Queue):
        async def _receive():
            while True:
                message = await websocket.receive_text()
                await self.handle_receive(message)  # Call handle_receive

        receive_task = asyncio.create_task(_receive())
        send_task = asyncio.create_task(super._send(websocket, queue))

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
    _uri: str
    _feed_publisher: DataPublisher
    _admin_publisher: DataPublisher

    def __init__(
        self, uri: str, _feed_publisher: DataPublisher, _admin_publisher: DataPublisher
    ) -> None:
        self._uri = uri
        self._feed_publisher = _feed_publisher
        self._admin_publisher = _admin_publisher

    async def start(self):
        try:
            async with websockets.connect(self._uri) as ws:
                while True:
                    try:
                        message = await ws.recv()
                        await self._receive(message)
                    except websockets.exceptions.ConnectionClosed:
                        print("Connection lost, reconnecting...", flush=True)
                        await self.start()
        except (OSError, InvalidHandshake):
            print("Connection error, retrying ...", flush=True)
            await asyncio.sleep(5)
            await self.start()

    async def _receive(self, message: str):
        print(message, flush=True)
