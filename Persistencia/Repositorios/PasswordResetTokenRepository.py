from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from Persistencia.Conexion.DatabaseConnection import DatabaseConnection


class PasswordResetTokenRepository:
    def __init__(self):
        self.db = DatabaseConnection.get_instance()
        try:
            self._ensure_table()
        except Exception as exc:
            print(f"[WARN] No se pudo validar tabla TokensRecuperacionContrasena al iniciar: {exc}")

    def _ensure_table(self):
        conn = self.db.get_connection()
        cursor = conn.cursor()
        cursor.execute(
            """
            IF OBJECT_ID('TokensRecuperacionContrasena', 'U') IS NULL
            BEGIN
                CREATE TABLE TokensRecuperacionContrasena (
                    IdTokenRecuperacion INT IDENTITY(1,1) PRIMARY KEY,
                    IdUsuario INT NOT NULL,
                    Token VARCHAR(120) NOT NULL UNIQUE,
                    FechaExpiracion DATETIME NOT NULL,
                    Usado BIT NOT NULL DEFAULT 0,
                    FechaCreacion DATETIME NOT NULL DEFAULT GETDATE(),
                    CONSTRAINT FK_TokensRecuperacionContrasena_Usuarios
                        FOREIGN KEY (IdUsuario) REFERENCES Usuarios(IdUsuario)
                );
            END
            """
        )
        conn.commit()
        cursor.close()

    def invalidate_active_tokens_by_user(self, user_id: int) -> None:
        conn = self.db.get_connection()
        cursor = conn.cursor()
        cursor.execute(
            """
            UPDATE TokensRecuperacionContrasena
            SET Usado = 1
            WHERE IdUsuario = ? AND Usado = 0
            """,
            user_id,
        )
        conn.commit()
        cursor.close()

    def create(self, user_id: int, token: str, minutes_valid: int = 30) -> int:
        expires_at = datetime.now() + timedelta(minutes=minutes_valid)
        conn = self.db.get_connection()
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO TokensRecuperacionContrasena (IdUsuario, Token, FechaExpiracion, Usado)
            OUTPUT INSERTED.IdTokenRecuperacion
            VALUES (?, ?, ?, 0)
            """,
            (user_id, token, expires_at),
        )
        row = cursor.fetchone()
        conn.commit()
        cursor.close()
        if not row or row[0] is None:
            raise RuntimeError("No se pudo crear el token de recuperación.")
        return int(row[0])

    def get_valid_token(self, token: str) -> Optional[Dict[str, Any]]:
        conn = self.db.get_connection()
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT TOP 1 IdTokenRecuperacion, IdUsuario, Token, FechaExpiracion, Usado
            FROM TokensRecuperacionContrasena
            WHERE Token = ? AND Usado = 0 AND FechaExpiracion > GETDATE()
            """,
            token,
        )
        row = cursor.fetchone()
        cursor.close()
        if not row:
            return None
        return {
            "id": int(row[0]),
            "usuario_id": int(row[1]),
            "token": row[2],
            "fecha_expiracion": row[3],
            "usado": bool(row[4]),
        }

    def mark_as_used(self, token: str) -> None:
        conn = self.db.get_connection()
        cursor = conn.cursor()
        cursor.execute(
            """
            UPDATE TokensRecuperacionContrasena
            SET Usado = 1
            WHERE Token = ?
            """,
            token,
        )
        conn.commit()
        cursor.close()
