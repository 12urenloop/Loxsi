import yaml
from pydantic import BaseModel


class Telraam(BaseModel):
    host: str
    port: int


class Settings(BaseModel):
    telraam: Telraam
    show_live: bool

    @classmethod
    def load_from_yaml(cls, file_path: str):
        with open(file_path, "r") as f:
            settings_data = yaml.safe_load(f)
        return cls(**settings_data)
