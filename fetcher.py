import asyncio

from fastapi import Response
from httpx import AsyncClient
from httpx import ConnectError

from data_publisher import DataPublisher
from models import Count, Lap, LapSource, Team
from settings import Settings


class Fetcher:
    """
    Fetcher class is responsible for fetching data from the Telraam API and publishing it to the appropriate channels.
    """

    _settings: Settings
    _feed_publisher: DataPublisher
    _admin_publisher: DataPublisher

    def __init__(
            self, settings: Settings, feed_publisher, admin_publisher: DataPublisher
    ):
        """
        Initializes a new instance of the Fetcher class.

        Args:
            settings (Settings): The settings object containing configuration parameters.
            feed_publisher (DataPublisher): The data publisher for publishing feed data.
            admin_publisher (DataPublisher): The data publisher for publishing admin data.
        """
        self._settings = settings
        self._feed_publisher = feed_publisher
        self._admin_publisher = admin_publisher

    async def get_lap_source(self) -> list[dict]:
        """
        Retrieves the lap sources from the Telraam API.

        Returns:
            list[dict]: A list of lap sources as dictionaries.
        """
        async with AsyncClient() as client:
            lap_sources: Response = await client.get(
                self._settings.telraam.api + "lap-source"
            )
            lap_sources: list[dict] = lap_sources.json()
            lap_sources.append({"id": -1, "name": "accepted-laps"})
            return lap_sources

    async def fetch(self):
        """
        Fetches data from the Telraam API and publishes it to the appropriate channels.
        """
        async with AsyncClient() as client:

            async def _fetch(endpoint: str):
                """
                Fetches data from the Telraam API.

                Args:
                    endpoint (str): The API endpoint to fetch data from.

                Returns:
                    dict: The JSON response from the API.
                """
                response: Response = await client.get(
                    f"{self._settings.telraam.api}/{endpoint}"
                )

                await self._admin_publisher.publish("telraam-health", "good")
                return response.json()

            while True:
                try:
                    teams: list[dict] = await _fetch("team")  # Get all teams
                    lap_sources: list[dict] = (
                        await self.get_lap_sources()
                    )  # Get all lap sources

                    # Get all laps according to the source
                    if self._settings.source.name == "accepted-laps":
                        laps: list[dict] = await _fetch("accepted-laps")
                    else:
                        laps: list[dict] = await _fetch("lap")

                    await self._admin_publisher.publish("lap-source", lap_sources)

                    # Create models from the fetched data
                    teams_by_id: dict[int, Team] = {
                        team["id"]: Team(**team) for team in teams
                    }

                    lap_sources_by_id: dict[int, LapSource] = {
                        lap_source["id"]: LapSource(**lap_source)
                        for lap_source in lap_sources
                    }

                    # Create Lap models from the fetched data sorted by teams and lap sources
                    laps: list[Lap] = [
                        Lap(
                            team=teams_by_id[lap["teamId"]],
                            lap_source=lap_sources_by_id[lap["lapSourceId"]],
                            **lap,
                        )
                        for lap in laps
                    ]

                    # Filter laps by source
                    if self._settings.source.name != "accepted-laps":
                        laps: list[Lap] = [
                            lap
                            for lap in laps
                            if lap.lap_source.id == self._settings.source.id
                        ]

                    # Filter laps by freeze time
                    if self._settings.site.freeze is not None:
                        laps: list[Lap] = [
                            lap
                            for lap in laps
                            if lap.timestamp <= self._settings.site.freeze
                        ]

                    # Publish the amount of laps to the feed publisher
                    counts: list[dict] = [
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
