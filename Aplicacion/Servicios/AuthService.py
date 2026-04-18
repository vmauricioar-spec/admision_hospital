from Persistencia.Repositorios.UsuarioRepository import UsuarioRepository
from Dominio.Entidades.Usuario import Usuario
from typing import Optional
import hashlib
import secrets
import string

class AuthService:
    def __init__(self):
        self.usuario_repo = UsuarioRepository()

    def _hash_password(self, password: str) -> str:
        return hashlib.sha256(password.encode()).hexdigest()

    def hash_password(self, password: str) -> str:
        return self._hash_password(password)

    def generate_secure_password(self, length: int = 16) -> str:
        alphabet = string.ascii_letters + string.digits + "!@#$%&*+-_=?"
        return "".join(secrets.choice(alphabet) for _ in range(length))

    def build_password_commitment(self, username: str, password: str, salt_hex: Optional[str] = None) -> tuple[str, str]:
        salt_value = salt_hex or secrets.token_hex(16)
        payload = f"{username}:{salt_value}:{password}"
        commitment = hashlib.sha256(payload.encode()).hexdigest()
        return salt_value, commitment

    def login(self, username: str, password: str) -> Optional[Usuario]:
        usuario = self.usuario_repo.get_by_username(username)
        if usuario and usuario.activo:
            if usuario.password_hash == self._hash_password(password):
                return usuario
        return None

    def verify_password(self, usuario: Usuario, password: str) -> bool:
        return usuario.password_hash == self._hash_password(password)

    def create_user(
        self,
        username: str,
        password: str,
        nombre_completo: str,
        role: str,
        email: Optional[str] = None,
    ) -> int:
        password_hash = self._hash_password(password)
        usuario = Usuario.create(username, password_hash, nombre_completo, role, email=email)
        return self.usuario_repo.create(usuario)

    def create_user_with_blockchain(
        self,
        username: str,
        password: str,
        nombre_completo: str,
        role: str,
        blockchain_service,
        email: Optional[str] = None,
    ) -> tuple[int, str, str, str]:
        salt_hex, commitment = self.build_password_commitment(username, password)
        tx_signature = blockchain_service.registrar_password_hash(
            username=username,
            password_commitment=commitment,
            salt_hex=salt_hex,
            role=role,
        )
        user_id = self.create_user(username, password, nombre_completo, role, email=email)
        return user_id, tx_signature, salt_hex, commitment

    def get_user_by_id(self, id: int) -> Optional[Usuario]:
        return self.usuario_repo.get_by_id(id)

    def change_password(self, usuario_id: int, new_password: str) -> bool:
        nuevo_hash = self._hash_password(new_password)
        return self.usuario_repo.update_password_hash(usuario_id, nuevo_hash)
