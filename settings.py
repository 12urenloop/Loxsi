from typing import Optional
import yaml
from pydantic import BaseModel


class Admin(BaseModel):
    name: str
    password: str


class Interval(BaseModel):
    feed: int
    fetch: int
    websocket: int


class Site(BaseModel):
    show_live: bool
    freeze: Optional[int]


class Source(BaseModel):
    id: int
    name: Optional[str]


class Telraam(BaseModel):
    api: str
    ws: str


class Settings(BaseModel):
    admin: Admin
    debug: bool
    interval: Interval
    message: Optional[str]
    site: Site
    source: Source
    source_file: str
    telraam: Telraam

    def persist(self):
        with open(self.source_file, "w") as file:
            file.write(
                yaml.dump(
                    self.model_dump(exclude={"source_file"}), default_flow_style=False
                )
            )

    @classmethod
    def load_from_yaml(cls, file_path: str):
        with open(file_path, "r") as f:
            settings_data = yaml.safe_load(f)
        return cls(source_file=file_path, **settings_data)
