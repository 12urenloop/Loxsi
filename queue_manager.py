from typing import List
from asyncio import Queue


class QueueManager:
    def __init__(self):
        self.queues: List[Queue] = []

    async def add(self) -> Queue:
        queue: Queue = Queue()
        self.queues.append(queue)
        return queue

    async def remove(self, queue: Queue) -> None:
        self.queues.remove(queue)

    async def broadcast(self, data: List) -> None:
        for queue in self.queues:
            await queue.put(data)

    async def count(self) -> int:
        return len(self.queues)
