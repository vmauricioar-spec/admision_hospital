import os
import threading
from typing import Optional

import pyodbc


class DatabaseConnection:
    _instance: Optional["DatabaseConnection"] = None

    def __init__(self):
        self.server = os.environ.get("DB_SERVER", "DESKTOP-B8EBRI2")
        self.database = os.environ.get("DB_NAME", "HistoriasClinicas")
        self.driver = os.environ.get("DB_DRIVER", "ODBC Driver 17 for SQL Server")
        self.trusted = os.environ.get("DB_TRUSTED", "yes").lower() in ("1", "true", "yes", "y")
        raw_encrypt = os.environ.get("DB_ENCRYPT")
        self.encrypt = (
            raw_encrypt.lower() in ("1", "true", "yes", "y")
            if raw_encrypt is not None
            else (not self.trusted)
        )
        raw_tsc = os.environ.get("DB_TRUST_SERVER_CERTIFICATE")
        self.trust_server_certificate = (
            raw_tsc.lower() in ("1", "true", "yes", "y")
            if raw_tsc is not None
            else self.trusted
        )
        self.connection_timeout = int(os.environ.get("DB_CONNECTION_TIMEOUT", "30"))
        # pyodbc connections must not be shared across threads; Gunicorn may run several.
        self._local = threading.local()

    def _build_connection_string(self) -> str:
        parts = [
            f"DRIVER={{{self.driver}}};",
            f"SERVER={self.server};",
            f"DATABASE={self.database};",
        ]
        if self.trusted:
            parts.append("Trusted_Connection=yes;")
        else:
            user = os.environ.get("DB_USER", "")
            pwd = os.environ.get("DB_PASSWORD", "")
            parts.append(f"UID={user};PWD={pwd};")
        parts.append(f"Encrypt={'yes' if self.encrypt else 'no'};")
        parts.append(f"TrustServerCertificate={'yes' if self.trust_server_certificate else 'no'};")
        parts.append(f"Connection Timeout={self.connection_timeout};")
        return "".join(parts)

    @staticmethod
    def get_instance() -> "DatabaseConnection":
        if DatabaseConnection._instance is None:
            DatabaseConnection._instance = DatabaseConnection()
        return DatabaseConnection._instance

    def _thread_conn(self) -> Optional[pyodbc.Connection]:
        return getattr(self._local, "connection", None)

    def _set_thread_conn(self, conn: Optional[pyodbc.Connection]) -> None:
        self._local.connection = conn

    def get_connection(self) -> pyodbc.Connection:
        conn_str = self._build_connection_string()
        conn = self._thread_conn()
        if conn is None:
            self._set_thread_conn(pyodbc.connect(conn_str))
            return self._thread_conn()

        try:
            # Keep-alive check to avoid stale pooled connections on hosted environments.
            cursor = conn.cursor()
            cursor.execute("SELECT 1")
            cursor.fetchone()
            cursor.close()
            return conn
        except pyodbc.Error:
            try:
                conn.close()
            except Exception:
                pass
            self._set_thread_conn(pyodbc.connect(conn_str))
            return self._thread_conn()

    def close(self):
        conn = self._thread_conn()
        if conn:
            try:
                conn.close()
            except Exception:
                pass
            self._set_thread_conn(None)
