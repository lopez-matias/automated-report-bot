import logging
import re
import time
from datetime import datetime, timedelta

import schedule

from .config import load_all_configs
from .pipeline import ReportPipeline

logger = logging.getLogger(__name__)

# Supported formats:
#   "every monday at 08:00"
#   "every day at 06:00"
#   "every friday at 17:30"
#   "every 1 hours"
#   "every 30 minutes"

WEEKDAYS = ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"]


def _register(cfg: dict):
    sched_str = cfg.get("schedule", "").strip().lower()
    name = cfg.get("name", cfg.get("_config_path", "unknown"))

    def job():
        logger.info("Running scheduled report: %s", name)
        result = ReportPipeline(cfg).run()
        logger.info("Scheduled report done: %s | %s", name, result["status"])

    # "every monday at 08:00"
    m = re.match(r"every (\w+) at (\d{2}:\d{2})", sched_str)
    if m:
        day, hhmm = m.group(1), m.group(2)
        if day == "day":
            schedule.every().day.at(hhmm).do(job).tag(name)
        elif day in WEEKDAYS:
            getattr(schedule.every(), day).at(hhmm).do(job).tag(name)
        else:
            logger.warning("Unknown day %r in schedule %r", day, sched_str)
        return

    # "every 1 hours" / "every 2 hours"
    m = re.match(r"every (\d+) hours?", sched_str)
    if m:
        schedule.every(int(m.group(1))).hours.do(job).tag(name)
        return

    # "every 30 minutes"
    m = re.match(r"every (\d+) minutes?", sched_str)
    if m:
        schedule.every(int(m.group(1))).minutes.do(job).tag(name)
        return

    logger.warning("Cannot parse schedule %r for report %r — skipping", sched_str, name)


def _run_missed(cfg: dict, tolerance_minutes: int = 60):
    """Run the job immediately if we're within tolerance_minutes of the scheduled time."""
    sched_str = cfg.get("schedule", "").strip().lower()
    m = re.match(r"every (\w+) at (\d{2}:\d{2})", sched_str)
    if not m:
        return
    day, hhmm = m.group(1), m.group(2)
    now = datetime.now()
    hh, mm = map(int, hhmm.split(":"))
    scheduled_today = now.replace(hour=hh, minute=mm, second=0, microsecond=0)
    diff = abs((now - scheduled_today).total_seconds())
    if diff <= tolerance_minutes * 60 and now >= scheduled_today:
        logger.info("Running missed job on startup: %s", cfg.get("name"))
        ReportPipeline(cfg).run()


def start(config_dir: str = "reports/config"):
    configs = load_all_configs(config_dir)
    if not configs:
        logger.warning("No report configs found in %s", config_dir)

    for cfg in configs:
        _run_missed(cfg)
        _register(cfg)

    logger.info("Scheduler started. %d job(s) registered.", len(schedule.jobs))

    while True:
        schedule.run_pending()
        time.sleep(30)
