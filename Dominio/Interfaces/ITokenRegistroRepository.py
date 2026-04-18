from Dominio.Entidades.TokenRegistro import TokenRegistro
from typing import Optional

class ITokenRegistroRepository:
    def get_by_token(self, token: str) -> Optional[TokenRegistro]: pass
    def create(self, token: TokenRegistro) -> int: pass
    def mark_as_used(self, token: str) -> bool: pass
    def delete_expired(self) -> int: pass
