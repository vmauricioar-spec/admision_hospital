from Dominio.Entidades.Usuario import Usuario
from typing import List, Optional

class IUsuarioRepository:
    def get_by_id(self, id: int) -> Optional[Usuario]: pass
    def get_by_username(self, username: str) -> Optional[Usuario]: pass
    def get_all(self) -> List[Usuario]: pass
    def create(self, usuario: Usuario) -> int: pass
    def update(self, usuario: Usuario) -> bool: pass
    def delete(self, id: int) -> bool: pass
