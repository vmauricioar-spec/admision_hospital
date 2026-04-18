import pyodbc
import os
from typing import Optional

class DatabaseConnection:
    _instance: Optional['DatabaseConnection'] = None
    _connection: Optional[pyodbc.Connection] = None

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
    def get_instance() -> 'DatabaseConnection':
        if DatabaseConnection._instance is None:
            DatabaseConnection._instance = DatabaseConnection()
        return DatabaseConnection._instance

    def get_connection(self) -> pyodbc.Connection:
        if self._connection is None:
            conn_str = self._build_connection_string()
            self._connection = pyodbc.connect(conn_str)
        return self._connection

    def close(self):
        if self._connection:
            self._connection.close()
            self._connection = None
