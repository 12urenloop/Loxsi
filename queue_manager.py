from asyncio import Queue, Lock
from typing import List, Container


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
