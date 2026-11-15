import os
from pathlib import Path

CONFIG_DIR = Path("/home/ubuntu/shiplens/config")


def load_env_file(filename):
    path = CONFIG_DIR / filename

    for line in path.read_text().splitlines():
        line = line.strip()

        if not line or line.startswith("#"):
            continue

        key, separator, value = line.partition("=")

        if not separator:
            continue

        key = key.strip()
        value = value.strip().strip("'\"")

        if key.startswith("FIVETRAN_"):
            os.environ[key] = value


def load_fivetran_config():
    load_env_file("integration.env.example")
    load_env_file("fivetran_credentials.env")
