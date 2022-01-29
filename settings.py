from pydantic import BaseModel
from typing import List

import yaml


class AdminUser(BaseModel):
    name: str
    password: str


class Source(BaseModel):
    name: str
    url: str


class Settings(BaseModel):
    admin: AdminUser
    sources: List[Source]


with open('config.yml', 'r') as f:
    settings = Settings(**yaml.load(f, Loader=yaml.Loader))
