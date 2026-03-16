import os
from dataclasses import dataclass

import yaml
from marshmallow_dataclass import class_schema


@dataclass
class Config:
    ALLOWED_HOSTS: list
    SECRET_KEY: str
    DEBUG: bool
    SWAGGER_TITLE: str
    SWAGGER_DESCRIPTION: str
    TOKEN_CHECK: bool
    MOBILE_SECRET_KEY: str
    TELEGRAM_BOT_TOKEN: str
    STARTING_BALANCE: int



config_path = "/../config.yaml"
if os.getenv("IS_TEST", False):
    config_path = "/../config.example.yaml"

with open(os.path.dirname(__file__) + config_path) as f:
    config_data = yaml.safe_load(f)

config: Config = class_schema(Config)().load(config_data)
