from Dominio.Interfaces.ITokenRegistroRepository import ITokenRegistroRepository
from Dominio.Entidades.TokenRegistro import TokenRegistro
from Persistencia.Conexion.DatabaseConnection import DatabaseConnection
from typing import Optional
from datetime import datetime

class TokenRegistroRepository(ITokenRegistroRepository):
    def __init__(self):
        self.db = DatabaseConnection.get_instance()

    def _map_to_entity(self, row) -> TokenRegistro:
        return TokenRegistro(
            id=row[0],
            token=row[1],
            expires_at=row[2],
            used=bool(row[3]),
            created_at=row[4]
        )

    def get_by_token(self, token: str) -> Optional[TokenRegistro]:
        conn = self.db.get_connection()
        cursor = conn.cursor()
        cursor.execute(
            "SELECT IdTokenRegistro, Token, FechaExpiracion, Usado, FechaCreacion FROM TokensRegistro WHERE Token = ?",
            (token,)
        )
        row = cursor.fetchone()
        cursor.close()
        return self._map_to_entity(row) if row else None

    def create(self, token: TokenRegistro) -> int:
        conn = self.db.get_connection()
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO TokensRegistro (Token, FechaExpiracion, Usado, FechaCreacion) VALUES (?, ?, ?, ?)",
            (token.token, token.expires_at, 0, token.created_at)
        )
        conn.commit()
        cursor.execute("SELECT SCOPE_IDENTITY()")
        last_id = cursor.fetchone()[0]
        cursor.close()
        return last_id

    def mark_as_used(self, token: str) -> bool:
        conn = self.db.get_connection()
        cursor = conn.cursor()
        cursor.execute("UPDATE TokensRegistro SET Usado = 1 WHERE Token = ?", (token,))
        conn.commit()
        cursor.close()
        return True

    def delete_expired(self) -> int:
        conn = self.db.get_connection()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM TokensRegistro WHERE FechaExpiracion < ?", (datetime.now(),))
        conn.commit()
        rows_deleted = cursor.rowcount
        cursor.close()
        return rows_deleted
