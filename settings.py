from __future__ import annotations
from typing import Optional
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

    show_live: bool  # Show the live visual
    freeze: Optional[int]  # Freeze the site


class Source(BaseModel):
    """
    lap Source settings
    """

    id: int
    name: Optional[str]


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
    message: Optional[str]
    site: Site
    source: Source
    source_file: str
    telraam: Telraam

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
    def load_from_yaml(cls, file_path: str) -> Settings:
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
