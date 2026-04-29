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
            # Forzar resolución a IPv4 antes de conectar
            try:
                import socket
                # Si host ya es IP, gethostbyname lo devuelve igual. Si es nombre, fuerza IPv4.
                actual_host = socket.gethostbyname(host)
                if actual_host != host:
                    self._emit("INFO", "Host %s resuelto a IPv4: %s", host, actual_host)
            except Exception as e:
                self._emit("WARNING", "No se pudo pre-resolver %s: %s", host, e)
                actual_host = host

            with smtplib.SMTP_SSL(
                actual_host,
                self.smtp_port,
                context=context,
                timeout=self.smtp_timeout_seconds,
            ) as smtp:
                smtp.login(self.gmail_user, self.gmail_app_password)
                smtp.send_message(msg)

        # Lista de hosts a intentar (Gmail y su alias antiguo que a veces tiene rutas distintas)
        hosts_to_try = [self.smtp_host]
        if "gmail.com" in self.smtp_host:
            hosts_to_try.append("smtp.googlemail.com")

        last_err = None
        for current_host in hosts_to_try:
            try:
                if current_host != self.smtp_host:
                    self._emit("INFO", "Intentando host alternativo: %s", current_host)
                _do_send(current_host)
                return # Éxito
            except (OSError, smtplib.SMTPConnectError, smtplib.SMTPException) as exc:
                last_err = exc
                self._emit("WARNING", "Fallo con %s: %s", current_host, exc)
                
                # Si es un error de red, intentar con todas las IPs disponibles para este host
                is_network_err = getattr(exc, "errno", None) == 101 or "timed out" in str(exc).lower()
                if is_network_err:
                    try:
                        import socket
                        addr_info = socket.getaddrinfo(current_host, self.smtp_port, socket.AF_INET, socket.SOCK_STREAM)
                        ips = list(set([info[4][0] for info in addr_info]))
                        for ip in ips:
                            try:
                                self._emit("INFO", "Probando IP directa: %s", ip)
                                _do_send(ip)
                                return # Éxito
                            except Exception as e_ip:
                                self._emit("WARNING", "Fallo IP %s: %s", ip, e_ip)
                    except Exception as e_dns:
                        self._emit("ERROR", "Error en resolución multi-IP para %s: %s", current_host, e_dns)

        # Si llegamos aquí, fallaron todos los hosts e IPs
        if isinstance(last_err, OSError):
            errno = getattr(last_err, "errno", None)
            self._emit(
                "ERROR",
                "SMTP SSL falló totalmente [%s] errno=%s host=%s: %s",
                log_context,
                errno,
                self.smtp_host,
                last_err,
            )
            _logger.exception("SMTP SSL failure traceback")
        raise last_err
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
            # Forzar resolución a IPv4
            try:
                import socket
                actual_host = socket.gethostbyname(host)
                if actual_host != host:
                    self._emit("INFO", "Host %s resuelto a IPv4: %s", host, actual_host)
            except Exception as e:
                self._emit("WARNING", "No se pudo pre-resolver %s: %s", host, e)
                actual_host = host

            with smtplib.SMTP(actual_host, self.smtp_port, timeout=self.smtp_timeout_seconds) as smtp:
                smtp.ehlo()
                smtp.starttls(context=context)
                smtp.ehlo()
                smtp.login(self.gmail_user, self.gmail_app_password)
                smtp.send_message(msg)

        hosts_to_try = [self.smtp_host]
        if "gmail.com" in self.smtp_host:
            hosts_to_try.append("smtp.googlemail.com")

        last_err = None
        for current_host in hosts_to_try:
            try:
                if current_host != self.smtp_host:
                    self._emit("INFO", "Intentando host alternativo STARTTLS: %s", current_host)
                _do_send(current_host)
                return
            except (OSError, smtplib.SMTPConnectError, smtplib.SMTPException) as exc:
                last_err = exc
                self._emit("WARNING", "Fallo STARTTLS con %s: %s", current_host, exc)
                
                is_network_err = getattr(exc, "errno", None) == 101 or "timed out" in str(exc).lower()
                if is_network_err:
                    try:
                        import socket
                        addr_info = socket.getaddrinfo(current_host, self.smtp_port, socket.AF_INET, socket.SOCK_STREAM)
                        ips = list(set([info[4][0] for info in addr_info]))
                        for ip in ips:
                            try:
                                self._emit("INFO", "Probando IP directa STARTTLS: %s", ip)
                                _do_send(ip)
                                return
                            except Exception as e_ip:
                                self._emit("WARNING", "Fallo IP STARTTLS %s: %s", ip, e_ip)
                    except Exception as e_dns:
                        self._emit("ERROR", "Error en resolución multi-IP STARTTLS para %s: %s", current_host, e_dns)

        if isinstance(last_err, OSError):
            errno = getattr(last_err, "errno", None)
            self._emit(
                "ERROR",
                "SMTP STARTTLS falló totalmente [%s] errno=%s host=%s: %s",
                log_context,
                errno,
                self.smtp_host,
                last_err,
            )
            _logger.exception("SMTP STARTTLS failure traceback")
        raise last_err
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
