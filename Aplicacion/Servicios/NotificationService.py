import logging
import os
import smtplib
import ssl
from email.message import EmailMessage

_logger = logging.getLogger(__name__)


class NotificationConfigError(Exception):
    """Error de configuración para notificaciones."""


class NotificationService:
    def __init__(self):
        self.smtp_host = (os.getenv("GMAIL_SMTP_HOST") or "smtp.gmail.com").strip()
        self.smtp_port = int((os.getenv("GMAIL_SMTP_PORT") or "465").strip())
        self.gmail_user = (os.getenv("GMAIL_USER") or "").strip()
        self.gmail_app_password = (os.getenv("GMAIL_APP_PASSWORD") or "").strip()
        self.smtp_timeout_seconds = max(int((os.getenv("SMTP_TIMEOUT_SECONDS") or "6").strip()), 1)
        self.smtp_security = (os.getenv("SMTP_SECURITY") or "auto").strip().lower()

    def _emit(self, level: str, message: str, *args) -> None:
        rendered = message % args if args else message
        print(f"[{level}] NotificationService {rendered}", flush=True)
        if level == "ERROR":
            _logger.error(message, *args)
        elif level == "WARNING":
            _logger.warning(message, *args)
        else:
            _logger.info(message, *args)

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
        
        def _do_send(host):
            with smtplib.SMTP_SSL(
                host,
                self.smtp_port,
                context=context,
                timeout=self.smtp_timeout_seconds,
            ) as smtp:
                smtp.login(self.gmail_user, self.gmail_app_password)
                smtp.send_message(msg)

        try:
            _do_send(self.smtp_host)
        except (OSError, smtplib.SMTPConnectError) as exc:
            # Error 101 (Unreachable) o Timeout suelen indicar problemas de IPv6 o bloqueo de puerto
            is_network_err = getattr(exc, "errno", None) == 101 or "timed out" in str(exc).lower()
            
            if is_network_err:
                self._emit("WARNING", "Error de red (%s), intentando con IPs IPv4 directas...", exc)
                try:
                    import socket
                    # Obtener todas las IPs IPv4 disponibles para el host
                    addr_info = socket.getaddrinfo(self.smtp_host, self.smtp_port, socket.AF_INET, socket.SOCK_STREAM)
                    ips = list(set([info[4][0] for info in addr_info]))
                    
                    for ip in ips:
                        try:
                            self._emit("INFO", "Probando fallback IPv4: %s", ip)
                            _do_send(ip)
                            self._emit("INFO", "SMTP success via IPv4 fallback (%s) [%s]", ip, log_context)
                            return
                        except Exception as e_ip:
                            self._emit("WARNING", "Fallo IP %s: %s", ip, e_ip)
                    
                except Exception as e_dns:
                    self._emit("ERROR", "Error en resolución/fallback IPv4: %s", e_dns)
            
            # Si llegamos aquí y es un OSError, reportarlo
            if isinstance(exc, OSError):
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

    def _smtp_starttls_send(self, msg: EmailMessage, log_context: str) -> None:
        to_addr = (msg.get("To") or "").strip()
        self._emit(
            "INFO",
            "SMTP STARTTLS attempt [%s] host=%s port=%s from=%s to=%s",
            log_context,
            self.smtp_host,
            self.smtp_port,
            self.gmail_user,
            to_addr,
        )
        context = ssl.create_default_context()
        
        def _do_send(host):
            with smtplib.SMTP(host, self.smtp_port, timeout=self.smtp_timeout_seconds) as smtp:
                smtp.ehlo()
                smtp.starttls(context=context)
                smtp.ehlo()
                smtp.login(self.gmail_user, self.gmail_app_password)
                smtp.send_message(msg)

        try:
            _do_send(self.smtp_host)
        except (OSError, smtplib.SMTPConnectError) as exc:
            is_network_err = getattr(exc, "errno", None) == 101 or "timed out" in str(exc).lower()
            
            if is_network_err:
                self._emit("WARNING", "Error de red STARTTLS (%s), intentando con IPs IPv4 directas...", exc)
                try:
                    import socket
                    addr_info = socket.getaddrinfo(self.smtp_host, self.smtp_port, socket.AF_INET, socket.SOCK_STREAM)
                    ips = list(set([info[4][0] for info in addr_info]))
                    
                    for ip in ips:
                        try:
                            self._emit("INFO", "Probando fallback IPv4 STARTTLS: %s", ip)
                            _do_send(ip)
                            self._emit("INFO", "SMTP STARTTLS success via IPv4 fallback (%s) [%s]", ip, log_context)
                            return
                        except Exception as e_ip:
                            self._emit("WARNING", "Fallo IP %s: %s", ip, e_ip)
                except Exception as e_dns:
                    self._emit("ERROR", "Error en resolución/fallback IPv4 STARTTLS: %s", e_dns)
            
            if isinstance(exc, OSError):
                errno = getattr(exc, "errno", None)
                self._emit(
                    "ERROR",
                    "SMTP STARTTLS OSError [%s] errno=%s host=%s port=%s: %s",
                    log_context,
                    errno,
                    self.smtp_host,
                    self.smtp_port,
                    exc,
                )
                _logger.exception("SMTP STARTTLS OSError traceback [%s]", log_context)
            raise
        except smtplib.SMTPException as exc:
            self._emit(
                "ERROR",
                "SMTP STARTTLS protocol error [%s] host=%s port=%s: %s",
                log_context,
                self.smtp_host,
                self.smtp_port,
                exc,
            )
            _logger.exception("SMTP STARTTLS protocol traceback [%s]", log_context)
            raise
        except Exception as exc:
            self._emit(
                "ERROR",
                "SMTP STARTTLS unexpected error [%s] host=%s port=%s: %s",
                log_context,
                self.smtp_host,
                self.smtp_port,
                exc,
            )
            _logger.exception("SMTP STARTTLS unexpected traceback [%s]", log_context)
            raise
        self._emit("INFO", "SMTP STARTTLS success [%s] to=%s", log_context, to_addr)

    def _smtp_send(self, msg: EmailMessage, log_context: str) -> None:
        # Si se especifica un modo, intentarlo, pero si falla con error de red, 
        # permitir fallback a 'auto' para máxima resiliencia.
        try:
            if self.smtp_security == "ssl":
                self._smtp_ssl_send(msg, log_context)
                return
            if self.smtp_security == "starttls":
                self._smtp_starttls_send(msg, log_context)
                return
        except (OSError, smtplib.SMTPConnectError) as e:
            is_network_err = getattr(e, "errno", None) == 101 or "timed out" in str(e).lower()
            if is_network_err:
                self._emit("WARNING", "Error de red en modo %s, intentando auto-fallback...", self.smtp_security)
            else:
                raise e

        # auto mode: try configured port first, then fallback to the other common Gmail port.
        original_port = self.smtp_port
        attempts = []
        if original_port == 465:
            attempts = [587] # Solo el otro, el original ya falló arriba
        elif original_port == 587:
            attempts = [465]
        else:
            attempts = [465, 587]

        last_exc = None
        for port in attempts:
            self.smtp_port = port
            try:
                if port == 465:
                    self._smtp_ssl_send(msg, log_context)
                else:
                    self._smtp_starttls_send(msg, log_context)
                return
            except Exception as exc:
                last_exc = exc
                self._emit("WARNING", "SMTP auto fallback failed on port=%s [%s]", port, log_context)
        self.smtp_port = original_port
        if last_exc:
            raise last_exc

    def send_email_credentials(self, to_email: str, username: str, password: str):
        if not self.gmail_user or not self.gmail_app_password:
            raise NotificationConfigError(
                "Falta configurar GMAIL_USER y/o GMAIL_APP_PASSWORD."
            )
        if not to_email:
            raise NotificationConfigError("Correo destino inválido.")

        subject = "Credenciales de acceso - Historias Clinicas"
        text = (
            "Se ha creado su acceso al sistema.\n\n"
            f"Usuario: {username}\n"
            f"Contrasena: {password}\n\n"
            "Cambie y proteja esta contraseña en cuanto sea posible."
        )

        msg = EmailMessage()
        msg["Subject"] = subject
        msg["From"] = self.gmail_user
        msg["To"] = to_email
        msg.set_content(text)
        self._smtp_send(msg, "credentials")
        return "ok"

    def send_password_reset_link(self, to_email: str, nombre: str, reset_link: str):
        if not self.gmail_user or not self.gmail_app_password:
            raise NotificationConfigError(
                "Falta configurar GMAIL_USER y/o GMAIL_APP_PASSWORD."
            )
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

        msg = EmailMessage()
        msg["Subject"] = subject
        msg["From"] = self.gmail_user
        msg["To"] = to_email
        msg.set_content(text)
        self._smtp_send(msg, "password_reset")
        return "ok"
