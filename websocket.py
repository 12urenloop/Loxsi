import asyncio
from typing import override

import websockets.exceptions
from fastapi import WebSocket
from fastapi.encoders import jsonable_encoder

from data_publisher import DataPublisher


class WebSocketHandler:
    publisher: DataPublisher

    def __init__(self) -> None:
        self.publisher = DataPublisher()

    async def connect(self, websocket: WebSocket):
        await websocket.accept()

        queue = await self.publisher.add()

        try:
            await self._handle_connect(queue)
        finally:
            await self.publisher.remove_client(websocket)

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
