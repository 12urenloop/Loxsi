from pydantic import BaseModel, Field

# TODO: Check types


class Detection(BaseModel):
    id: int
    station_id: int = Field(alias="stationId")
    baton_id: int = Field(alias="batonId")
    timestamp: int  # TODO: What is the type of timestamp?
    rssi: int
    battery: float
    uptime_ms: int = Field(alias="uptimeMs")
    remote_id: int = Field(alias="remoteId")
    timestamp_ingestion: int = Field(alias="timestampIngestion")


class Station(BaseModel):
    id: int
    name: str
    broken: bool
    distance_from_start: float = Field(alias="distanceFromStart")
    url: str
    coord_x: float
    coord_y: float


class Team(BaseModel):
    id: int
    name: str
    baton_id: int = Field(alias="batonId")


class Baton(BaseModel):
    id: int
    name: str
    mac: str


class Lap(BaseModel):
    id: int
    team_id: int = Field(alias="teamId")
    timestamp: int
    lap_source_id: int = Field(alias="lapSourceId")
    manual: bool


class LapSource(BaseModel):
    id: int
    name: str


class BatonSwitchover(BaseModel):
    id: int
    team_id: int = Field(alias="teamId")
    previous_baton_id: int = Field(alias="previousBatonId")
    new_baton_id: int = Field(alias="newBatonId")
    timestamp: int


class LapSourceSwitchover(BaseModel):
    id: int
    new_lap_source: int = Field(alias="newLapSource")
    timestamp: int
