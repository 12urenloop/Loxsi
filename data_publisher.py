from typing import Dict, Any
from asyncio import Lock, Queue

from queue_manager import QueueManager


class DataPublisher(QueueManager):
    """
    An extension on QueueManagers that only publishes data when it is different from last publish.
    Also provides a way to publish data to topics. This way one queue can easily be used for multiple data updates.
    """
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
