from asyncio import Lock, Queue
from typing import Any

from src.settings import Settings

JsonData = str | int | float | dict | list


class QueueManager:
    """
    Manages a collection of queues and broadcast data to the queues.
    """

    def __init__(self) -> None:
        self._queues: list[Queue] = list()
        self._broadcast_lock: Lock = Lock()

    async def add(self) -> Queue:
        """
        Adds a new queue to the collection.

        Returns:
            Queue: The newly created queue.
        """
        queue: Queue = Queue()
        self._queues.append(queue)
        return queue

    async def remove(self, queue: Queue):
        """
        Removes a queue from the collection.

        Args:
            queue (Queue): The queue to be removed.
        """
        self._queues.remove(queue)

    async def _broadcast(self, data: tuple[str, JsonData]):
        """
        Broadcasts the given data to all queues in the collection.

        Args:
            data (tuple): The data to be broadcasted.
        """
        async with self._broadcast_lock:
            for queue in self._queues:
                await queue.put(data)

    async def count(self) -> int:
        """
        Returns the number of queues in the collection.

        Returns:
            int: The number of queues.
        """
        return len(self._queues)


class DataPublisher(QueueManager):
    """
    An extension on QueueManagers that only publishes data when it is different from last publish.
    Also provides a way to publish data to topics. This way one queue can easily be used for multiple data updates.
    """

    def __init__(self, settings: Settings) -> None:
        super().__init__()
        self._settings = settings
        self._cache: dict[str, Any] = dict()
        self._cache["position"] = {}
        self._publish_lock: Lock = Lock()

    async def add(self) -> Queue:
        """
        Adds a new queue and publishes cached data to the new queue.

        Returns:
            Queue: The newly created queue.

        """
        queue: Queue = await super().add()
        async with self._publish_lock:
            # Publish cached data to the new queue
            # Add the position data last
            for topic in self._cache:
                if topic != "position":
                    await queue.put((topic, self._cache[topic]))

            position_data = []
            if self._settings.position_source.name in self._cache["position"]:
                position_data = [
                    self._cache["position"][self._settings.position_source.name][
                        team_id
                    ]
                    for team_id in self._cache["position"][
                        self._settings.position_source.name
                    ]
                ]
            await queue.put(("position", position_data))
        return queue

    async def publish(self, topic: str, data: JsonData):
        """
        Publishes data to a specific topic.

        Args:
            topic (str): The topic to publish the data to.
            data (JsonData): The data to be published.
        """
        async with self._publish_lock:
            if topic == "position":
                position_source = data["positioner"]
                if position_source not in self._cache[topic]:
                    self._cache[topic][position_source] = {}

                for team_data in data["positions"]:
                    self._cache[topic][position_source][team_data["team_id"]] = (
                        team_data
                    )

                if position_source == self._settings.position_source.name:
                    await self._broadcast((topic, data["positions"]))
                return

            if topic in self._cache and self._cache[topic] == data:
                return
            if topic != "refresh":
                self._cache[topic] = data
            await self._broadcast((topic, data))
