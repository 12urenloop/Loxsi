from typing import Optional

from pydantic import BaseModel


class LapSource(BaseModel):
    id: int
    name: str


class Team(BaseModel):
    id: int
    name: str


class Lap(BaseModel):
    id: int
    team: Team
    lap_source: LapSource
    timestamp: int


class Count(BaseModel):
    count: int
    team: Team


class Message(BaseModel):
    message: Optional[str]


class FreezeTime(BaseModel):
    time: int
