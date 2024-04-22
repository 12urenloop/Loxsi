from httpx import AsyncClient, Response

from src.data_publisher import DataPublisher
from src.settings import Settings


class TelraamClient(AsyncClient):

    def __init__(
            self,
            settings: Settings,
            admin_publisher: DataPublisher,
            *args, **kwargs
    ):
        super().__init__(*args, **kwargs)
        self._settings: Settings = settings
        self._admin_publisher: DataPublisher = admin_publisher

    async def _get(self, endpoint: str) -> list:
        response: Response = await self.get(
            f"{self._settings.telraam.api}/{endpoint}"
        )

        await self._admin_publisher.publish("telraam-health", "good")

        return response.json()

    async def get_lap_sources(self) -> list[dict]:
        lap_sources = await self._get("lap-source")
        lap_sources.append({"id": -1, "name": "accepted-laps"})
        return lap_sources

    async def get_laps(self) -> list[dict]:
        return await self._get("lap")

    async def get_teams(self) -> list[dict]:
        return await self._get("team")

    async def get_accepted_laps(self) -> list[dict]:
        return await self._get("accepted-laps")

    async def get_stations(self) -> list[dict]:
        return await self._get("station")
