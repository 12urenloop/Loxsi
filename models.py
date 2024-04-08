from typing import Optional

from pydantic import BaseModel


# Define the models for the received from Telraam


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
    message: str | None


class FreezeTime(BaseModel):
    time: int
