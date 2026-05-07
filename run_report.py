"""CLI to run a single report immediately: python run_report.py reports/config/monthly_summary.yaml"""
import sys
import logging
import json

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s — %(message)s",
)

from bot.config import load_report_config
from bot.pipeline import run_report

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python run_report.py <path/to/config.yaml>")
        sys.exit(1)

    config_path = sys.argv[1]
    cfg = load_report_config(config_path)
    result = run_report(cfg)
    print(json.dumps(result, indent=2))
    sys.exit(0 if result["status"] == "success" else 1)
