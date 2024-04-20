import asyncio
import traceback

from httpx import ConnectError

from src.data_publisher import DataPublisher
from src.models import Count, Lap, LapSource, Team
from src.settings import Settings
from src.tasks.task import Task
from src.telraam import TelraamClient


class Fetcher(Task):
    """
    Fetcher class is responsible for fetching data from the Telraam API and publishing it to the appropriate channels.
    """

    def __init__(self, settings: Settings, feed_publisher: DataPublisher, admin_publisher: DataPublisher):
        super().__init__(settings, feed_publisher, admin_publisher)

    async def fetch(self):
        """
        Fetches data from the Telraam API and publishes it to the appropriate channels.
        """
        async with TelraamClient(self._settings, self._admin_publisher) as client:

            while True:
                try:
                    teams: list[dict] = await client.get_teams()  # Get all teams
                    lap_sources: list[dict] = (
                        await client.get_lap_sources()
                    )  # Get all lap sources

                    # Get all laps according to the source
                    if self._settings.source.name == "accepted-laps":
                        laps: list[dict] = await client.get_accepted_laps()
                    else:
                        laps: list[dict] = await client.get_laps()

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
                        new_laps: list[Lap] = [
                            lap
                            for lap in laps
                            if lap.timestamp <= self._settings.site.freeze
                        ]

                        # If the filter removed laps, we now the scoreboard is frozen
                        await self._feed_publisher.publish("frozen", len(new_laps) != len(laps))

                        laps: list[Lap] = new_laps

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
                    print(traceback.format_exc(), flush=True)

                await asyncio.sleep(self._settings.interval.fetch)
