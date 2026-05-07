import logging
import re
import time
from datetime import datetime, timedelta

import schedule

from bot.config import load_all_configs
from bot.pipeline import run_report

logger = logging.getLogger(__name__)

DAY_MAP = {
    "monday": schedule.every().monday,
    "tuesday": schedule.every().tuesday,
    "wednesday": schedule.every().wednesday,
    "thursday": schedule.every().thursday,
    "friday": schedule.every().friday,
    "saturday": schedule.every().saturday,
    "sunday": schedule.every().sunday,
}


def _parse_and_register(sched_str: str, job_fn):
    sched_str = sched_str.strip().lower()

    m = re.match(r"every\s+(\d+)\s+(minute|minutes|hour|hours)", sched_str)
    if m:
        n, unit = int(m.group(1)), m.group(2)
        if "minute" in unit:
            schedule.every(n).minutes.do(job_fn)
        else:
            schedule.every(n).hours.do(job_fn)
        return

    m = re.match(r"every\s+(\w+)\s+at\s+(\d{2}:\d{2})", sched_str)
    if m:
        day, time_str = m.group(1), m.group(2)
        if day == "day":
            schedule.every().day.at(time_str).do(job_fn)
        elif day in DAY_MAP:
            DAY_MAP[day].at(time_str).do(job_fn)
        else:
            raise ValueError(f"Unknown day: {day}")
        return

    raise ValueError(f"Cannot parse schedule: '{sched_str}'")


def _should_run_missed(sched_str: str) -> bool:
    sched_str = sched_str.strip().lower()
    m = re.match(r"every\s+(\w+)\s+at\s+(\d{2}:\d{2})", sched_str)
    if not m:
        return False

    day, time_str = m.group(1), m.group(2)
    now = datetime.now()
    hour, minute = map(int, time_str.split(":"))
    scheduled_today = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
    delta = now - scheduled_today

    if day == "day" and timedelta(0) <= delta <= timedelta(hours=1):
        return True
    weekday_map = {
        "monday": 0, "tuesday": 1, "wednesday": 2, "thursday": 3,
        "friday": 4, "saturday": 5, "sunday": 6,
    }
    target_weekday = weekday_map.get(day)
    if target_weekday is not None and now.weekday() == target_weekday and timedelta(0) <= delta <= timedelta(hours=1):
        return True
    return False


def start_scheduler(config_dir: str = None):
    configs = load_all_configs(config_dir)
    logger.info(f"Loaded {len(configs)} report configs")

    for cfg in configs:
        report_name = cfg.get("name", "Unnamed Report")
        sched_str = cfg.get("schedule", "every monday at 08:00")

        def make_job(c):
            def job():
                logger.info(f"Scheduler triggering: {c.get('name')}")
                run_report(c)
            return job

        job_fn = make_job(cfg)

        try:
            _parse_and_register(sched_str, job_fn)
            logger.info(f"Registered '{report_name}' — schedule: {sched_str}")
        except ValueError as e:
            logger.error(f"Could not register '{report_name}': {e}")
            continue

        if _should_run_missed(sched_str):
            logger.info(f"Running missed job for '{report_name}'")
            job_fn()

    logger.info("Scheduler running. Press Ctrl+C to stop.")
    while True:
        schedule.run_pending()
        time.sleep(30)
