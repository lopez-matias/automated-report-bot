import logging
from pathlib import Path

import yaml

logger = logging.getLogger(__name__)


def load_config(path: str | Path) -> dict:
    path = Path(path)
    with open(path) as f:
        cfg = yaml.safe_load(f)
    logger.debug("Loaded config from %s: %s", path, cfg.get("name"))
    return cfg


def load_all_configs(config_dir: str | Path = "reports/config") -> list[dict]:
    config_dir = Path(config_dir)
    configs = []
    for yaml_file in sorted(config_dir.glob("*.yaml")):
        try:
            cfg = load_config(yaml_file)
            cfg["_config_path"] = str(yaml_file)
            configs.append(cfg)
        except Exception as exc:
            logger.error("Failed to load config %s: %s", yaml_file, exc)
    logger.info("Loaded %d report config(s) from %s", len(configs), config_dir)
    return configs
