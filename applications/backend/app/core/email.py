import logging
import smtplib
from email.message import EmailMessage

from app.core.config import settings

logger = logging.getLogger(__name__)


def send_overheat_alert_email(*, to: str, system_name: str, panel_temp_c: float, threshold_c: float) -> None:
    if not settings.smtp_host:
        logger.info("SMTP_HOST not configured, skipping overheat alert email to %s", to)
        return

    message = EmailMessage()
    message["Subject"] = f"[SolarSense] Superaquecimento em {system_name}"
    message["From"] = settings.smtp_user or "solarsense@localhost"
    message["To"] = to
    message.set_content(
        f"O painel de '{system_name}' atingiu {panel_temp_c}°C, acima do limite de {threshold_c}°C."
    )

    with smtplib.SMTP(settings.smtp_host, settings.smtp_port) as smtp:
        smtp.starttls()
        if settings.smtp_user:
            smtp.login(settings.smtp_user, settings.smtp_password)
        smtp.send_message(message)
