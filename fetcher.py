import asyncio
from typing import Dict, List
from httpx import AsyncClient

from fastapi import Response
from httpx import ConnectError

from data_publisher import DataPublisher
from models import Count, Lap, LapSource, Team
from settings import Settings


class Fetcher:
    _settings: Settings
    _feed_publisher: DataPublisher
    _admin_publisher: DataPublisher

    def __init__(
        self, settings: Settings, feed_publisher, admin_publisher: DataPublisher
    ):
        self._settings = settings
        self._feed_publisher = feed_publisher
        self._admin_publisher = admin_publisher

    async def get_lap_source(self) -> List[Dict]:
        async with AsyncClient() as client:
            lap_sources: Response = await client.get(
                self._settings.telraam.api + "lap-source"
            )
            lap_sources: List[Dict] = lap_sources.json()
            lap_sources.append({"id": -1, "name": "accepted-laps"})
            return lap_sources

    async def fetch(self):
        async with AsyncClient() as client:

            async def _fetch(endpoint: str):
                response: Response = await client.get(
                    f"{self._settings.telraam.api}/{endpoint}"
                )

                await self._admin_publisher.publish("telraam-health", "good")
                return response.json()

            while True:
                try:
                    teams: List[Dict] = await _fetch("team")
                    lap_sources: List[Dict] = await self.get_lap_sources()

                    if self._settings.source.name == "accepted-laps":
                        laps: List[Dict] = await _fetch("accepted-laps")
                    else:
                        laps: List[Dict] = await _fetch("lap")

                    await self._admin_publisher.publish("lap-source", lap_sources)

                    teams_by_id: Dict[int, Team] = {
                        team["id"]: Team(**team) for team in teams
                    }

                    lap_sources_by_id: Dict[int, LapSource] = {
                        lap_source["id"]: LapSource(**lap_source)
                        for lap_source in lap_sources
                    }

                    laps: List[Lap] = [
                        Lap(
                            team=teams_by_id[lap["teamId"]],
                            lap_source=lap_sources_by_id[lap["lapSourceId"]],
                            **lap,
                        )
                        for lap in laps
                    ]

                    if self._settings.source.name != "accepted-laps":
                        laps: List[Lap] = [
                            lap
                            for lap in laps
                            if lap.lap_source.id == self._settings.source.id
                        ]

                    if self._settings.site.freeze is not None:
                        laps: List[Lap] = [
                            lap
                            for lap in laps
                            if lap.timestamp <= self._settings.site.freeze
                        ]

                    counts: List[Dict] = [
                        Count(
                            count=len([lap for lap in laps if lap.team == team]),
                            team=team,
                        ).model_dump()
                        for team in teams_by_id.values()
                    ]

                    await self._feed_publisher.publish("counts", counts)
                except (ConnectError, AttributeError):
                    await self._admin_publisher.publish("telraam-health", "bad")
                except Exception as e:
                    print(type(e), flush=True)

                await asyncio.sleep(self._settings.interval.fetch)
