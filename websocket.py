import asyncio
from typing import override

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

    _connection_error: int = 0

    def __init__(
        self, uri: str, _feed_publisher: DataPublisher, _admin_publisher: DataPublisher
    ) -> None:
        self._uri = uri
        self._feed_publisher = _feed_publisher
        self._admin_publisher = _admin_publisher

    async def start(self):
        print("HiHi", flush=True)
        print(self._uri, flush=True)
        async with websockets.connect(self._uri) as ws:
            print("Next", flush=True)
            while True:
                try:
                    await ws.send(str(self._connection_error))
                    message = await ws.recv()
                    await self._receive(message)
                except websockets.exceptions.ConnectionClosed:
                    self._connection_error += 1
                    await asyncio.sleep(self._connection_error * 5)
                    try:
                        print("Trying", flush=True)
                        message = await ws.recv()
                        await self._receive(message)
                        self._connection_error = 0
                    except websockets.exceptions.ConnectionClosed:
                        if self._connection_error > 1:
                            print("Lost connection with telraam", flush=True)
                            return

    async def _receive(self, message: str):
        print(message, flush=True)
