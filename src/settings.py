import yaml
from pydantic import BaseModel


class Admin(BaseModel):
    """
    Admin user credentials
    """

    name: str
    password: str


class Interval(BaseModel):
    """
    Intervals
    """

    feed: int  # Interval to fetch data from the Telraam API
    fetch: int  # Interval to wait for new data in a DataPublisher queue
    websocket: int  # Interval to wait when retrying to establish a websocket connection


class Site(BaseModel):
    """
    Site settings
    """

    freeze: int | None  # Freeze the site
    message: str | None  # MOTD banner content


class LapSource(BaseModel):
    """
    Lap source settings
    """

    id: int
    name: str | None


class PositionSource(BaseModel):
    """
    Positioner source settingd
    """

    id: int
    name: str | None


class Telraam(BaseModel):
    """
    Telraam urls / uris
    """

    api: str
    ws: str


class Settings(BaseModel):
    """
    Settings for the Loxsi application
    """

    admin: Admin
    interval: Interval
    site: Site
    lap_source: LapSource
    position_source: PositionSource
    source_file: str
    telraam: Telraam
    api_token: str

    def persist(self):
        """
        Persists the settings to a YAML file.
        """
        with open(self.source_file, "w") as file:
            file.write(
                yaml.dump(
                    self.model_dump(exclude={"source_file"}), default_flow_style=False
                )
            )

    @classmethod
    def load_from_yaml(cls, file_path: str) -> "Settings":
        """
        Load settings from a YAML file.

        Args:
            file_path (str): The path to the YAML file.

        Returns:
            Settings: An instance of the Settings class with the loaded settings.

        """
        with open(file_path, "r") as f:
            settings_data = yaml.safe_load(f)
        return cls(source_file=file_path, **settings_data)
