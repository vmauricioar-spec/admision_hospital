from Persistencia.Repositorios.TokenRegistroRepository import TokenRegistroRepository
from Dominio.Entidades.TokenRegistro import TokenRegistro
import secrets
import uuid

class TokenService:
    def __init__(self):
        self.token_repo = TokenRegistroRepository()

    def generate_token(self, hours_valid: int = 24) -> str:
        token_str = str(uuid.uuid4())
        token = TokenRegistro.create(token_str, hours_valid)
        self.token_repo.create(token)
        return token_str

    def validate_token(self, token: str) -> bool:
        token_obj = self.token_repo.get_by_token(token)
        if not token_obj:
            return False
        return token_obj.is_valid()

    def use_token(self, token: str) -> bool:
        if self.validate_token(token):
            return self.token_repo.mark_as_used(token)
        return False

    def cleanup_expired(self) -> int:
        return self.token_repo.delete_expired()
