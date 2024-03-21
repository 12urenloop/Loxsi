from asyncio import Lock, Queue
from typing import Any, Container, Dict, List


class QueueManager:
    _queues: List[Queue] = []
    _broadcast_lock: Lock = Lock()

    async def add(self) -> Queue:
        queue: Queue = Queue()
        self._queues.append(queue)
        return queue

    async def remove(self, queue: Queue):
        self._queues.remove(queue)

    async def _broadcast(self, data: Container):
        async with self._broadcast_lock:
            for queue in self._queues:
                await queue.put(data)

    async def count(self) -> int:
        return len(self._queues)


class DataPublisher(QueueManager):
    _cache: Dict[str, Any] = {}
    _publish_lock: Lock = Lock()

    async def add(self) -> Queue:
        queue: Queue = await super().add()
        async with self._publish_lock:
            for topic in self._cache:
                await queue.put((topic, self._cache[topic]))
        return queue

    async def publish(self, topic, data) -> None:
        async with self._publish_lock:
            if topic in self._cache and self._cache[topic] == data:
                return
            self._cache[topic] = data
            await self._broadcast((topic, data))
