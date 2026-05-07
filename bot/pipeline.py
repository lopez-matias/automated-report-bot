import logging
import os
import tempfile
from datetime import datetime
from pathlib import Path

from .builders import get_builder
from .config import load_config
from .delivery.email import EmailDelivery, build_email_body
from .sources import get_source
from .transformers import apply_transforms

logger = logging.getLogger(__name__)


class ReportPipeline:
    def __init__(self, config: dict | str):
        if isinstance(config, str):
            config = load_config(config)
        self.config = config
        self.output_dir = Path(os.getenv("OUTPUT_DIR", "output"))

    def run(self) -> dict:
        name = self.config.get("name", "report")
        start = datetime.now()
        logger.info("Starting pipeline: %s", name)

        result = {
            "report": name,
            "started_at": start.isoformat(),
            "status": "ok",
            "rows": 0,
            "files": [],
            "error": None,
        }

        try:
            df = self._fetch()
            result["rows"] = len(df)

            df = self._transform(df)

            files = self._build(df)
            result["files"] = files

            self._deliver(df, files)

        except Exception as exc:
            logger.exception("Pipeline failed: %s — %s", name, exc)
            result["status"] = "error"
            result["error"] = str(exc)
            self._send_failure_alert(exc)

        result["duration_s"] = (datetime.now() - start).total_seconds()
        logger.info(
            "Pipeline %s finished in %.1fs | status=%s | rows=%d",
            name,
            result["duration_s"],
            result["status"],
            result["rows"],
        )
        return result

    # ── Steps ────────────────────────────────────────────────────────────────

    def _fetch(self):
        source_cfg = self.config.get("source", {})
        source = get_source(source_cfg)
        return source.fetch()

    def _transform(self, df):
        transforms = self.config.get("transform", [])
        if not transforms:
            return df
        return apply_transforms(df, transforms)

    def _build(self, df) -> list[str]:
        fmt = self.config.get("format", "excel")
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        safe_name = self.config.get("name", "report").replace(" ", "_").lower()

        self.output_dir.mkdir(parents=True, exist_ok=True)
        files = []

        formats = ["excel", "pdf"] if fmt == "both" else [fmt]
        ext_map = {"excel": "xlsx", "pdf": "pdf"}

        for f in formats:
            ext = ext_map[f]
            out = str(self.output_dir / f"{safe_name}_{ts}.{ext}")
            builder = get_builder(f, self.config)
            builder.build(df, out)
            files.append(out)

        return files

    def _deliver(self, df, files: list[str]):
        delivery_cfg = self.config.get("delivery", {})
        recipients = delivery_cfg.get("recipients", [])
        if not recipients:
            logger.info("No recipients configured — skipping delivery")
            return

        subject_tpl = delivery_cfg.get("subject", "{report_name}")
        date_range = self._date_range()
        subject = subject_tpl.replace("{date_range}", date_range).replace(
            "{report_name}", self.config.get("name", "Report")
        )

        body_html = build_email_body(
            {**self.config, "date_range": date_range},
        )

        attachments = files if delivery_cfg.get("attach_file", True) else []

        email = EmailDelivery(delivery_cfg)
        email.send(
            recipients=recipients,
            subject=subject,
            body_html=body_html,
            attachments=attachments,
            cc=delivery_cfg.get("cc"),
            bcc=delivery_cfg.get("bcc"),
        )

    def _date_range(self) -> str:
        now = datetime.now()
        return now.strftime("%b %d, %Y")

    def _send_failure_alert(self, exc: Exception):
        alert_email = os.getenv("ALERT_EMAIL", "")
        if not alert_email:
            return
        try:
            delivery_cfg = self.config.get("delivery", {})
            email = EmailDelivery(delivery_cfg)
            email.send(
                recipients=[alert_email],
                subject=f"[ALERT] Report failed: {self.config.get('name')}",
                body_html=f"<p>Report <b>{self.config.get('name')}</b> failed.</p><pre>{exc}</pre>",
            )
        except Exception as alert_exc:
            logger.error("Failed to send failure alert: %s", alert_exc)
