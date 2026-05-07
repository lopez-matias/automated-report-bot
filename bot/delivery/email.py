import smtplib
import logging
import mimetypes
from datetime import datetime
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
from pathlib import Path

from jinja2 import Environment, FileSystemLoader

logger = logging.getLogger(__name__)

TEMPLATE_DIR = Path(__file__).parent / "templates"
SIZE_WARN_BYTES = 10 * 1024 * 1024  # 10 MB


def _render_html(context: dict) -> str:
    env = Environment(loader=FileSystemLoader(str(TEMPLATE_DIR)), autoescape=True)
    tmpl = env.get_template("report_email.html")
    return tmpl.render(**context)


def _attach_bytes(msg: MIMEMultipart, data: bytes, filename: str):
    if len(data) > SIZE_WARN_BYTES:
        logger.warning(f"Attachment {filename} is {len(data) / 1024 / 1024:.1f} MB (>10 MB)")
    mime_type, _ = mimetypes.guess_type(filename)
    maintype, subtype = (mime_type or "application/octet-stream").split("/", 1)
    part = MIMEBase(maintype, subtype)
    part.set_payload(data)
    encoders.encode_base64(part)
    part.add_header("Content-Disposition", "attachment", filename=filename)
    msg.attach(part)


def send_smtp(
    email_config: dict,
    delivery_config: dict,
    subject: str,
    html_body: str,
    attachments: list[tuple[bytes, str]],
):
    msg = MIMEMultipart("mixed")
    msg["Subject"] = subject
    msg["From"] = f"{email_config['from_name']} <{email_config['from_email']}>"
    msg["To"] = ", ".join(delivery_config.get("recipients", []))

    cc = delivery_config.get("cc", [])
    bcc = delivery_config.get("bcc", [])
    if cc:
        msg["Cc"] = ", ".join(cc)

    all_recipients = (
        delivery_config.get("recipients", []) + cc + bcc
    )

    msg.attach(MIMEText(html_body, "html"))

    for data, filename in attachments:
        _attach_bytes(msg, data, filename)

    with smtplib.SMTP(email_config["smtp_host"], email_config["smtp_port"]) as server:
        server.starttls()
        server.login(email_config["smtp_user"], email_config["smtp_password"])
        server.sendmail(email_config["from_email"], all_recipients, msg.as_string())

    logger.info(f"Email sent via SMTP to {all_recipients}")


def send_sendgrid(
    email_config: dict,
    delivery_config: dict,
    subject: str,
    html_body: str,
    attachments: list[tuple[bytes, str]],
):
    import base64
    import sendgrid
    from sendgrid.helpers.mail import (
        Mail, Attachment, FileContent, FileName, FileType, Disposition, To
    )

    sg = sendgrid.SendGridAPIClient(api_key=email_config["sendgrid_api_key"])

    to_list = [To(email=r) for r in delivery_config.get("recipients", [])]

    mail = Mail(
        from_email=email_config["from_email"],
        subject=subject,
        html_content=html_body,
    )
    mail.to = to_list

    for data, filename in attachments:
        mime_type, _ = mimetypes.guess_type(filename)
        att = Attachment(
            FileContent(base64.b64encode(data).decode()),
            FileName(filename),
            FileType(mime_type or "application/octet-stream"),
            Disposition("attachment"),
        )
        mail.attachment = att

    sg.send(mail)
    logger.info(f"Email sent via SendGrid to {delivery_config.get('recipients')}")


def deliver_report(
    email_config: dict,
    delivery_config: dict,
    report_name: str,
    date_range: str,
    schedule_desc: str,
    attachments: list[tuple[bytes, str]],
    kpis: list[dict] = None,
):
    formats = ", ".join(name for _, name in attachments)
    subject_template = delivery_config.get(
        "subject", "{report_name} — {date_range}"
    )
    subject = subject_template.format(
        report_name=report_name,
        date_range=date_range,
    )

    body_template = delivery_config.get(
        "body", "Please find attached the {report_name} for {date_range}."
    )
    body_text = body_template.format(
        report_name=report_name,
        date_range=date_range,
    )

    html_body = _render_html({
        "report_name": report_name,
        "date_range": date_range,
        "body_text": body_text,
        "kpis": kpis or [],
        "attach_file": bool(attachments),
        "formats": formats,
        "schedule_desc": schedule_desc,
        "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M"),
    })

    provider = email_config.get("provider", "smtp")
    if provider == "sendgrid":
        send_sendgrid(email_config, delivery_config, subject, html_body, attachments)
    else:
        send_smtp(email_config, delivery_config, subject, html_body, attachments)


def send_alert(email_config: dict, report_name: str, error: str):
    alert_email = email_config.get("alert_email")
    if not alert_email:
        logger.warning("No ALERT_EMAIL configured — skipping failure alert")
        return

    subject = f"[ALERT] Report pipeline failed: {report_name}"
    body = f"""
    <h3 style="color:#c0392b">Pipeline Failure Alert</h3>
    <p><strong>Report:</strong> {report_name}</p>
    <p><strong>Time:</strong> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
    <p><strong>Error:</strong></p>
    <pre style="background:#f8f8f8;padding:12px;border-radius:4px">{error}</pre>
    """

    try:
        provider = email_config.get("provider", "smtp")
        delivery_cfg = {"recipients": [alert_email]}
        if provider == "sendgrid":
            send_sendgrid(email_config, delivery_cfg, subject, body, [])
        else:
            send_smtp(email_config, delivery_cfg, subject, body, [])
    except Exception as e:
        logger.error(f"Failed to send alert email: {e}")
