from asyncio import Lock, Queue
from typing import Any, Container, Dict, List


class QueueManager:

    def __init__(self):
        self.queues: List[Queue] = []
        self._broadcast_lock: Lock = Lock()

    async def add(self) -> Queue:
        queue: Queue = Queue()
        self.queues.append(queue)
        return queue

    async def remove(self, queue: Queue) -> None:
        self.queues.remove(queue)

    async def broadcast(self, data: Container) -> None:
        async with self._broadcast_lock:
            for queue in self.queues:
                await queue.put(data)

    async def count(self) -> int:
        return len(self.queues)


class DataPublisher(QueueManager):

    def __init__(self):
        super().__init__()
        self.cache: Dict[str, Any] = {}
        self.publish_lock: Lock = Lock()

    async def add(self) -> Queue:
        queue: Queue = await super().add()
        async with self.publish_lock:
            for topic in self.cache:
                await queue.put((topic, self.cache[topic]))
        return queue

    async def publish(self, topic, data) -> None:
        async with self.publish_lock:
            if topic in self.cache and self.cache[topic] == data:
                return
            self.cache[topic] = data
            await self.broadcast((topic, data))
