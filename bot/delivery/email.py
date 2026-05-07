import logging
import mimetypes
import os
import smtplib
from email.mime.application import MIMEApplication
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from pathlib import Path

logger = logging.getLogger(__name__)

ATTACHMENT_WARN_BYTES = 10 * 1024 * 1024  # 10 MB


def _load_template(template_path: str, variables: dict) -> str:
    path = Path(template_path)
    if not path.exists():
        fallback = Path(__file__).parent / "templates" / "report_email.html"
        path = fallback
    html = path.read_text()
    for key, val in variables.items():
        html = html.replace(f"{{{{{key}}}}}", str(val))
    return html


class EmailDelivery:
    def __init__(self, config: dict):
        self.config = config
        self.smtp_host = os.getenv("SMTP_HOST", config.get("smtp_host", "smtp.gmail.com"))
        self.smtp_port = int(os.getenv("SMTP_PORT", config.get("smtp_port", 587)))
        self.smtp_user = os.getenv("SMTP_USER", config.get("smtp_user", ""))
        self.smtp_pass = os.getenv("SMTP_PASS", config.get("smtp_pass", ""))
        self.from_addr = os.getenv("FROM_EMAIL", config.get("from_email", self.smtp_user))
        self.use_sendgrid = os.getenv("USE_SENDGRID", "false").lower() == "true"
        self.sendgrid_key = os.getenv("SENDGRID_API_KEY", "")

    def send(
        self,
        recipients: list[str],
        subject: str,
        body_html: str,
        attachments: list[str] | None = None,
        cc: list[str] | None = None,
        bcc: list[str] | None = None,
    ):
        if self.use_sendgrid and self.sendgrid_key:
            self._send_sendgrid(recipients, subject, body_html, attachments, cc, bcc)
        else:
            self._send_smtp(recipients, subject, body_html, attachments, cc, bcc)

    def _send_smtp(self, recipients, subject, body_html, attachments, cc, bcc):
        msg = MIMEMultipart("mixed")
        msg["From"] = self.from_addr
        msg["To"] = ", ".join(recipients)
        msg["Subject"] = subject
        if cc:
            msg["Cc"] = ", ".join(cc)

        msg.attach(MIMEText(body_html, "html", "utf-8"))

        all_recipients = list(recipients) + (cc or []) + (bcc or [])

        for path in attachments or []:
            self._attach_file(msg, path)

        with smtplib.SMTP(self.smtp_host, self.smtp_port) as server:
            server.ehlo()
            server.starttls()
            if self.smtp_user:
                server.login(self.smtp_user, self.smtp_pass)
            server.sendmail(self.from_addr, all_recipients, msg.as_string())

        logger.info("Email sent to %s | subject: %s", recipients, subject)

    def _send_sendgrid(self, recipients, subject, body_html, attachments, cc, bcc):
        import base64
        import sendgrid
        from sendgrid.helpers.mail import (
            Attachment,
            ContentId,
            Disposition,
            FileContent,
            FileName,
            FileType,
            Mail,
            To,
        )

        sg = sendgrid.SendGridAPIClient(api_key=self.sendgrid_key)
        mail = Mail(
            from_email=self.from_addr,
            to_emails=[To(r) for r in recipients],
            subject=subject,
            html_content=body_html,
        )

        for path in attachments or []:
            file_path = Path(path)
            if not file_path.exists():
                continue
            with open(file_path, "rb") as f:
                data = base64.b64encode(f.read()).decode()
            att = Attachment(
                FileContent(data),
                FileName(file_path.name),
                FileType(mimetypes.guess_type(path)[0] or "application/octet-stream"),
                Disposition("attachment"),
            )
            mail.add_attachment(att)

        sg.send(mail)
        logger.info("SendGrid email sent to %s | subject: %s", recipients, subject)

    def _attach_file(self, msg: MIMEMultipart, path: str):
        file_path = Path(path)
        if not file_path.exists():
            logger.warning("Attachment not found: %s", path)
            return

        size = file_path.stat().st_size
        if size > ATTACHMENT_WARN_BYTES:
            logger.warning(
                "Attachment %s is %.1f MB — exceeds 10 MB warning threshold",
                file_path.name,
                size / 1024 / 1024,
            )

        with open(file_path, "rb") as f:
            part = MIMEApplication(f.read(), Name=file_path.name)
        part["Content-Disposition"] = f'attachment; filename="{file_path.name}"'
        msg.attach(part)


def build_email_body(report_config: dict, df_summary: dict | None = None) -> str:
    template_path = str(
        Path(__file__).parent / "templates" / "report_email.html"
    )
    variables = {
        "report_name": report_config.get("name", "Report"),
        "date_range": report_config.get("date_range", ""),
        "body": report_config.get("delivery", {}).get("body", "Please find the report attached."),
        "schedule": report_config.get("schedule", ""),
    }
    if df_summary:
        variables.update(df_summary)
    return _load_template(template_path, variables)
