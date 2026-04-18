import os
import smtplib
import ssl
from email.message import EmailMessage


class NotificationConfigError(Exception):
    """Error de configuración para notificaciones."""


class NotificationService:
    def __init__(self):
        self.smtp_host = (os.getenv("GMAIL_SMTP_HOST") or "smtp.gmail.com").strip()
        self.smtp_port = int((os.getenv("GMAIL_SMTP_PORT") or "465").strip())
        self.gmail_user = (os.getenv("GMAIL_USER") or "").strip()
        self.gmail_app_password = (os.getenv("GMAIL_APP_PASSWORD") or "").strip()

    def send_email_credentials(self, to_email: str, username: str, password: str):
        if not self.gmail_user or not self.gmail_app_password:
            raise NotificationConfigError(
                "Falta configurar GMAIL_USER y/o GMAIL_APP_PASSWORD."
            )
        if not to_email:
            raise NotificationConfigError("Correo destino inválido.")

        msg = EmailMessage()
        msg["Subject"] = "Credenciales de acceso - Historias Clinicas"
        msg["From"] = self.gmail_user
        msg["To"] = to_email
        msg.set_content(
            "Se ha creado su acceso al sistema.\n\n"
            f"Usuario: {username}\n"
            f"Contrasena: {password}\n\n"
            "Cambie y proteja esta contraseña en cuanto sea posible."
        )

        context = ssl.create_default_context()
        with smtplib.SMTP_SSL(
            self.smtp_host,
            self.smtp_port,
            context=context,
            timeout=20,
        ) as smtp:
            smtp.login(self.gmail_user, self.gmail_app_password)
            smtp.send_message(msg)

        return "ok"

    def send_password_reset_link(self, to_email: str, nombre: str, reset_link: str):
        if not self.gmail_user or not self.gmail_app_password:
            raise NotificationConfigError(
                "Falta configurar GMAIL_USER y/o GMAIL_APP_PASSWORD."
            )
        if not to_email:
            raise NotificationConfigError("Correo destino inválido.")

        saludo = f"Hola {nombre}," if nombre else "Hola,"
        msg = EmailMessage()
        msg["Subject"] = "Recuperación de contraseña - Historias Clínicas"
        msg["From"] = self.gmail_user
        msg["To"] = to_email
        msg.set_content(
            f"{saludo}\n\n"
            "Recibimos una solicitud para restablecer tu contraseña.\n"
            "Usa el siguiente enlace para crear una nueva contraseña:\n\n"
            f"{reset_link}\n\n"
            "Este enlace vence en 30 minutos.\n"
            "Si no solicitaste este cambio, puedes ignorar este correo."
        )

        context = ssl.create_default_context()
        with smtplib.SMTP_SSL(
            self.smtp_host,
            self.smtp_port,
            context=context,
            timeout=20,
        ) as smtp:
            smtp.login(self.gmail_user, self.gmail_app_password)
            smtp.send_message(msg)

        return "ok"
