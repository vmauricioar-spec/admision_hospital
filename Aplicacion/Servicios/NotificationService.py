import base64
import json
import logging
import os
import urllib.error
import urllib.parse
import urllib.request
from email.message import EmailMessage

_logger = logging.getLogger(__name__)


class NotificationConfigError(Exception):
    """Error de configuración para notificaciones."""


class NotificationService:
    TOKEN_URL = "https://oauth2.googleapis.com/token"
    SEND_URL = "https://gmail.googleapis.com/gmail/v1/users/me/messages/send"

    def __init__(self):
        self.email_delivery_enabled = (os.getenv("EMAIL_DELIVERY_ENABLED") or "false").strip().lower() in ("1", "true", "yes", "y")
        self.gmail_api_client_id = (os.getenv("GMAIL_API_CLIENT_ID") or "").strip()
        self.gmail_api_client_secret = (os.getenv("GMAIL_API_CLIENT_SECRET") or "").strip()
        self.gmail_api_refresh_token = (os.getenv("GMAIL_API_REFRESH_TOKEN") or "").strip()
        self.gmail_api_sender = (os.getenv("GMAIL_API_SENDER") or "").strip()
        self.gmail_api_timeout_seconds = max(int((os.getenv("GMAIL_API_TIMEOUT_SECONDS") or "15").strip()), 1)

    def _emit(self, level: str, message: str, *args) -> None:
        rendered = message % args if args else message
        print(f"[{level}] NotificationService {rendered}", flush=True)
        if level == "ERROR":
            _logger.error(message, *args)
        elif level == "WARNING":
            _logger.warning(message, *args)
        else:
            _logger.info(message, *args)

    def _get_access_token(self) -> str:
        if not self.gmail_api_client_id or not self.gmail_api_client_secret or not self.gmail_api_refresh_token:
            raise NotificationConfigError(
                "Faltan GMAIL_API_CLIENT_ID, GMAIL_API_CLIENT_SECRET o GMAIL_API_REFRESH_TOKEN."
            )

        body = urllib.parse.urlencode(
            {
                "client_id": self.gmail_api_client_id,
                "client_secret": self.gmail_api_client_secret,
                "refresh_token": self.gmail_api_refresh_token,
                "grant_type": "refresh_token",
            }
        ).encode("utf-8")
        request = urllib.request.Request(
            self.TOKEN_URL,
            data=body,
            headers={"Content-Type": "application/x-www-form-urlencoded"},
            method="POST",
        )
        try:
            with urllib.request.urlopen(request, timeout=self.gmail_api_timeout_seconds) as response:
                payload = json.loads(response.read().decode("utf-8"))
        except urllib.error.HTTPError as exc:
            error_body = exc.read().decode("utf-8", errors="replace") if exc.fp else str(exc)
            self._emit("ERROR", "Gmail API token HTTPError code=%s body=%s", exc.code, error_body)
            raise RuntimeError(f"Gmail API token error HTTP {exc.code}: {error_body}") from exc
        except Exception as exc:
            self._emit("ERROR", "Gmail API token request failed: %s", exc)
            raise

        access_token = payload.get("access_token")
        if not access_token:
            raise RuntimeError(f"No se obtuvo access_token de Gmail API: {payload}")
        return access_token

    def _send_via_gmail_api(self, to_email: str, subject: str, text: str, log_context: str) -> None:
        sender = self.gmail_api_sender
        if not sender:
            raise NotificationConfigError("Falta GMAIL_API_SENDER.")

        msg = EmailMessage()
        msg["To"] = to_email
        msg["From"] = sender
        msg["Subject"] = subject
        msg.set_content(text)
        raw = base64.urlsafe_b64encode(msg.as_bytes()).decode("utf-8")

        payload = json.dumps({"raw": raw}).encode("utf-8")
        access_token = self._get_access_token()
        request = urllib.request.Request(
            self.SEND_URL,
            data=payload,
            headers={
                "Authorization": f"Bearer {access_token}",
                "Content-Type": "application/json",
                "User-Agent": "historias-admision/1.0",
            },
            method="POST",
        )
        self._emit("INFO", "Gmail API attempt [%s] from=%s to=%s", log_context, sender, to_email)
        try:
            with urllib.request.urlopen(request, timeout=self.gmail_api_timeout_seconds) as response:
                body = response.read().decode("utf-8", errors="replace")
                status_code = getattr(response, "status", None) or response.getcode()
                if status_code not in (200, 202):
                    raise RuntimeError(f"Gmail API send status={status_code} body={body}")
        except urllib.error.HTTPError as exc:
            error_body = exc.read().decode("utf-8", errors="replace") if exc.fp else str(exc)
            self._emit("ERROR", "Gmail API send HTTPError [%s] code=%s body=%s", log_context, exc.code, error_body)
            raise RuntimeError(f"Gmail API send error HTTP {exc.code}: {error_body}") from exc
        except Exception as exc:
            self._emit("ERROR", "Gmail API send failed [%s]: %s", log_context, exc)
            raise
        self._emit("INFO", "Gmail API success [%s] to=%s", log_context, to_email)

    def send_email_credentials(self, to_email: str, username: str, password: str):
        if not self.email_delivery_enabled:
            self._emit("INFO", "Email delivery disabled. Skipping credentials email to=%s", to_email)
            return "disabled"
        if not to_email:
            raise NotificationConfigError("Correo destino inválido.")

        subject = "Credenciales de acceso - Historias Clinicas"
        text = (
            "Se ha creado su acceso al sistema.\n\n"
            f"Usuario: {username}\n"
            f"Contrasena: {password}\n\n"
            "Cambie y proteja esta contraseña en cuanto sea posible."
        )
        self._send_via_gmail_api(to_email, subject, text, "credentials")
        return "ok"

    def send_password_reset_link(self, to_email: str, nombre: str, reset_link: str):
        if not self.email_delivery_enabled:
            self._emit("INFO", "Email delivery disabled. Skipping reset link email to=%s", to_email)
            return "disabled"
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
        self._send_via_gmail_api(to_email, subject, text, "password_reset")
        return "ok"
