from pydantic import BaseModel
from typing import Optional

import yaml


class AdminUser(BaseModel):
    name: str
    password: str


class Source(BaseModel):
    id: int = 0
    name: Optional[str]


class Telraam(BaseModel):
    base_url: str


class Settings(BaseModel):
    admin: AdminUser
    source: Source = Source()
    source_file: str
    telraam: Telraam
    message: Optional[str]
    freeze: Optional[int]

    def persist(self) -> None:
        with open(self.source_file, 'w') as file:
            file.write(yaml.dump(self.dict(exclude={'source_file'}), default_flow_style=False))


def get_config(source_file: str) -> Settings:
    with open(source_file, 'r') as file:
        return Settings(source_file=source_file, **yaml.load(file, Loader=yaml.Loader))


settings: Settings = get_config('config.yml')
