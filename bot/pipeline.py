import logging
import os
from datetime import datetime, timedelta
from pathlib import Path

import pandas as pd

from bot.sources import get_source
from bot.transformers import apply_transforms
from bot.builders import build_excel, build_pdf
from bot.delivery import deliver_report, send_alert
from bot.config import get_email_config

logger = logging.getLogger(__name__)


def _date_range_label(df: pd.DataFrame) -> str:
    date_cols = df.select_dtypes(include=["datetime64", "object"]).columns
    for col in date_cols:
        try:
            parsed = pd.to_datetime(df[col], errors="coerce").dropna()
            if not parsed.empty:
                lo = parsed.min().strftime("%b %d")
                hi = parsed.max().strftime("%b %d, %Y")
                return f"{lo}–{hi}"
        except Exception:
            pass
    week_ago = (datetime.now() - timedelta(days=7)).strftime("%b %d")
    today = datetime.now().strftime("%b %d, %Y")
    return f"{week_ago}–{today}"


def _extract_kpis(df: pd.DataFrame) -> list[dict]:
    kpis = []
    numeric_cols = df.select_dtypes(include="number").columns.tolist()[:4]
    for col in numeric_cols:
        total = df[col].sum()
        label = col.replace("_", " ").title()
        kpis.append({"label": label, "value": f"{total:,.2f}"})
    return kpis


def run_report(report_config: dict) -> dict:
    report_name = report_config.get("name", "Report")
    fmt = report_config.get("format", "excel")
    output_dir = os.getenv("OUTPUT_DIR", "output")
    Path(output_dir).mkdir(parents=True, exist_ok=True)

    start = datetime.now()
    logger.info(f"[{report_name}] Pipeline started")

    try:
        # Extract
        source_cfg = report_config["source"]
        source = get_source(source_cfg)
        df = source.extract()
        logger.info(f"[{report_name}] Extracted {len(df)} rows")

        # Transform
        transforms = report_config.get("transform", [])
        if transforms:
            df = apply_transforms(df, transforms)
            logger.info(f"[{report_name}] Transformations applied")

        date_range = _date_range_label(df)
        timestamp = start.strftime("%Y%m%d_%H%M%S")
        safe_name = report_name.replace(" ", "_")

        # Build
        attachments = []
        if fmt in ("excel", "both"):
            excel_path = f"{output_dir}/{safe_name}_{timestamp}.xlsx"
            excel_bytes = build_excel(
                df,
                report_name=report_name,
                source_type=source_cfg.get("type", "unknown"),
                output_path=excel_path,
            )
            attachments.append((excel_bytes, f"{safe_name}_{timestamp}.xlsx"))

        if fmt in ("pdf", "both"):
            pdf_path = f"{output_dir}/{safe_name}_{timestamp}.pdf"
            pdf_bytes = build_pdf(
                df,
                report_name=report_name,
                date_range=date_range,
                output_path=pdf_path,
            )
            attachments.append((pdf_bytes, f"{safe_name}_{timestamp}.pdf"))

        # Deliver
        delivery_cfg = report_config.get("delivery", {})
        if delivery_cfg.get("recipients") and delivery_cfg.get("attach_file", True):
            email_config = get_email_config()
            schedule_desc = report_config.get("schedule", "a configured schedule")
            kpis = _extract_kpis(df)

            deliver_report(
                email_config=email_config,
                delivery_config=delivery_cfg,
                report_name=report_name,
                date_range=date_range,
                schedule_desc=schedule_desc,
                attachments=attachments,
                kpis=kpis,
            )

        duration = (datetime.now() - start).total_seconds()
        result = {
            "report": report_name,
            "status": "success",
            "rows": len(df),
            "duration_s": round(duration, 2),
            "files": [name for _, name in attachments],
        }
        logger.info(f"[{report_name}] Done in {duration:.2f}s — {len(df)} rows")
        return result

    except Exception as e:
        duration = (datetime.now() - start).total_seconds()
        logger.error(f"[{report_name}] Failed: {e}", exc_info=True)
        try:
            send_alert(get_email_config(), report_name, str(e))
        except Exception as alert_err:
            logger.error(f"Alert send failed: {alert_err}")
        return {
            "report": report_name,
            "status": "error",
            "error": str(e),
            "duration_s": round(duration, 2),
        }
