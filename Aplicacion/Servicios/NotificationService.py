import json
import logging
import os
import smtplib
import ssl
import urllib.error
import urllib.request
from email.message import EmailMessage

_logger = logging.getLogger(__name__)

RESEND_API_URL = "https://api.resend.com/emails"


class NotificationConfigError(Exception):
    """Error de configuración para notificaciones."""


class NotificationService:
    def __init__(self):
        self.smtp_host = (os.getenv("GMAIL_SMTP_HOST") or "smtp.gmail.com").strip()
        self.smtp_port = int((os.getenv("GMAIL_SMTP_PORT") or "465").strip())
        self.gmail_user = (os.getenv("GMAIL_USER") or "").strip()
        self.gmail_app_password = (os.getenv("GMAIL_APP_PASSWORD") or "").strip()
        self.smtp_timeout_seconds = max(int((os.getenv("SMTP_TIMEOUT_SECONDS") or "6").strip()), 1)
        self.resend_api_key = (os.getenv("RESEND_API_KEY") or "").strip()
        self.resend_from = (os.getenv("RESEND_FROM_EMAIL") or "").strip()

    def _notification_channel(self) -> str:
        """auto: Resend si hay API key; si no, SMTP Gmail."""
        raw = (os.getenv("NOTIFICATION_PROVIDER") or "auto").strip().lower()
        if raw in ("resend", "smtp"):
            return raw
        return "resend" if self.resend_api_key else "smtp"

    def _emit(self, level: str, message: str, *args) -> None:
        rendered = message % args if args else message
        print(f"[{level}] NotificationService {rendered}", flush=True)
        if level == "ERROR":
            _logger.error(message, *args)
        elif level == "WARNING":
            _logger.warning(message, *args)
        else:
            _logger.info(message, *args)

    def _send_resend(self, subject: str, text: str, to_email: str, log_context: str) -> None:
        if not self.resend_api_key:
            raise NotificationConfigError("Falta RESEND_API_KEY para enviar por Resend.")
        from_addr = self.resend_from or "Historias Clinicas <onboarding@resend.dev>"
        self._emit(
            "INFO",
            "Resend attempt [%s] from=%s to=%s subject=%s",
            log_context,
            from_addr,
            to_email,
            subject[:80],
        )
        payload = {
            "from": from_addr,
            "to": [to_email],
            "subject": subject,
            "text": text,
        }
        data = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(
            RESEND_API_URL,
            data=data,
            headers={
                "Authorization": f"Bearer {self.resend_api_key}",
                "Content-Type": "application/json",
            },
            method="POST",
        )
        timeout = max(int((os.getenv("RESEND_TIMEOUT_SECONDS") or "15").strip()), 5)
        try:
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                body = resp.read().decode("utf-8", errors="replace")
                code = getattr(resp, "status", None) or resp.getcode()
                if code not in (200, 201):
                    raise RuntimeError(f"Resend HTTP {code}: {body}")
        except urllib.error.HTTPError as exc:
            err_body = exc.read().decode("utf-8", errors="replace") if exc.fp else ""
            self._emit(
                "ERROR",
                "Resend HTTPError [%s] code=%s: %s",
                log_context,
                exc.code,
                err_body or str(exc),
            )
            _logger.exception("Resend HTTPError traceback [%s]", log_context)
            raise RuntimeError(f"Resend error HTTP {exc.code}: {err_body}") from exc
        except OSError as exc:
            errno = getattr(exc, "errno", None)
            self._emit(
                "ERROR",
                "Resend OSError [%s] errno=%s: %s",
                log_context,
                errno,
                exc,
            )
            _logger.exception("Resend OSError traceback [%s]", log_context)
            raise
        except Exception as exc:
            self._emit("ERROR", "Resend unexpected [%s]: %s", log_context, exc)
            _logger.exception("Resend unexpected traceback [%s]", log_context)
            raise
        self._emit("INFO", "Resend success [%s] to=%s", log_context, to_email)

    def _smtp_ssl_send(self, msg: EmailMessage, log_context: str) -> None:
        to_addr = (msg.get("To") or "").strip()
        self._emit(
            "INFO",
            "SMTP attempt [%s] host=%s port=%s from=%s to=%s",
            log_context,
            self.smtp_host,
            self.smtp_port,
            self.gmail_user,
            to_addr,
        )
        context = ssl.create_default_context()
        try:
            with smtplib.SMTP_SSL(
                self.smtp_host,
                self.smtp_port,
                context=context,
                timeout=self.smtp_timeout_seconds,
            ) as smtp:
                smtp.login(self.gmail_user, self.gmail_app_password)
                smtp.send_message(msg)
        except OSError as exc:
            errno = getattr(exc, "errno", None)
            self._emit(
                "ERROR",
                "SMTP OSError [%s] errno=%s host=%s port=%s: %s",
                log_context,
                errno,
                self.smtp_host,
                self.smtp_port,
                exc,
            )
            _logger.exception("SMTP OSError traceback [%s]", log_context)
            raise
        except smtplib.SMTPException as exc:
            self._emit(
                "ERROR",
                "SMTP protocol error [%s] host=%s port=%s: %s",
                log_context,
                self.smtp_host,
                self.smtp_port,
                exc,
            )
            _logger.exception("SMTP protocol traceback [%s]", log_context)
            raise
        except Exception as exc:
            self._emit(
                "ERROR",
                "SMTP unexpected error [%s] host=%s port=%s: %s",
                log_context,
                self.smtp_host,
                self.smtp_port,
                exc,
            )
            _logger.exception("SMTP unexpected traceback [%s]", log_context)
            raise
        self._emit("INFO", "SMTP success [%s] to=%s", log_context, to_addr)

    def send_email_credentials(self, to_email: str, username: str, password: str):
        if not to_email:
            raise NotificationConfigError("Correo destino inválido.")

        subject = "Credenciales de acceso - Historias Clinicas"
        text = (
            "Se ha creado su acceso al sistema.\n\n"
            f"Usuario: {username}\n"
            f"Contrasena: {password}\n\n"
            "Cambie y proteja esta contraseña en cuanto sea posible."
        )

        channel = self._notification_channel()
        if channel == "resend":
            self._send_resend(subject, text, to_email, "credentials")
            return "ok"

        if not self.gmail_user or not self.gmail_app_password:
            raise NotificationConfigError(
                "Falta configurar GMAIL_USER y/o GMAIL_APP_PASSWORD (o usa RESEND_API_KEY)."
            )

        msg = EmailMessage()
        msg["Subject"] = subject
        msg["From"] = self.gmail_user
        msg["To"] = to_email
        msg.set_content(text)
        self._smtp_ssl_send(msg, "credentials")
        return "ok"

    def send_password_reset_link(self, to_email: str, nombre: str, reset_link: str):
        if not to_email:
            raise NotificationConfigError("Correo destino inválido.")

        saludo = f"Hola {nombre}," if nombre else "Hola,"
        subject = "Recuperación de contraseña - Historias Clínicas"
        text = (
            f"{saludo}\n\n"
            "Recibimos una solicitud para restablecer tu contraseña.\n"
            "Usa el siguiente enlace para crear una nueva contraseña:\n\n"
            f"{reset_link}\n\n"
            "Este enlace vence en 30 minutos.\n"
            "Si no solicitaste este cambio, puedes ignorar este correo."
        )

        channel = self._notification_channel()
        if channel == "resend":
            self._send_resend(subject, text, to_email, "password_reset")
            return "ok"

        if not self.gmail_user or not self.gmail_app_password:
            raise NotificationConfigError(
                "Falta configurar GMAIL_USER y/o GMAIL_APP_PASSWORD (o usa RESEND_API_KEY)."
            )

        msg = EmailMessage()
        msg["Subject"] = subject
        msg["From"] = self.gmail_user
        msg["To"] = to_email
        msg.set_content(text)
        self._smtp_ssl_send(msg, "password_reset")
        return "ok"
