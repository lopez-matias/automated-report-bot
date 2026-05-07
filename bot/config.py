import os
import yaml
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()


def load_report_config(path: str) -> dict:
    with open(path, "r") as f:
        return yaml.safe_load(f)


def load_all_configs(config_dir: str = None) -> list[dict]:
    config_dir = config_dir or os.getenv("REPORTS_CONFIG_DIR", "reports/config")
    configs = []
    for yaml_file in Path(config_dir).glob("*.yaml"):
        cfg = load_report_config(str(yaml_file))
        cfg["_config_file"] = str(yaml_file)
        configs.append(cfg)
    return configs


def get_db_url() -> str:
    return (
        f"postgresql+psycopg2://{os.getenv('DB_USER')}:{os.getenv('DB_PASSWORD')}"
        f"@{os.getenv('DB_HOST', 'localhost')}:{os.getenv('DB_PORT', '5432')}"
        f"/{os.getenv('DB_NAME')}"
    )


def get_email_config() -> dict:
    return {
        "provider": os.getenv("EMAIL_PROVIDER", "smtp"),
        "smtp_host": os.getenv("SMTP_HOST", "smtp.gmail.com"),
        "smtp_port": int(os.getenv("SMTP_PORT", "587")),
        "smtp_user": os.getenv("SMTP_USER"),
        "smtp_password": os.getenv("SMTP_PASSWORD"),
        "sendgrid_api_key": os.getenv("SENDGRID_API_KEY"),
        "from_email": os.getenv("EMAIL_FROM"),
        "from_name": os.getenv("EMAIL_FROM_NAME", "Report Bot"),
        "alert_email": os.getenv("ALERT_EMAIL"),
    }
