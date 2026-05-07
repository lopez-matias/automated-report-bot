"""Entry point: load .env then start the scheduler."""

import logging
import os

from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(
    level=os.getenv("LOG_LEVEL", "INFO"),
    format="%(asctime)s %(levelname)-8s %(name)s — %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)

from bot.scheduler import start

if __name__ == "__main__":
    start(config_dir=os.getenv("CONFIG_DIR", "reports/config"))
