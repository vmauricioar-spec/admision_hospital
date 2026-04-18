from datetime import datetime
from dataclasses import dataclass
from typing import Optional

@dataclass
class Usuario:
    id: int
    username: str
    password_hash: str
    nombre_completo: str
    email: Optional[str]
    role: str
    activo: bool
    fecha_creacion: datetime

    @staticmethod
    def create(
        username: str,
        password_hash: str,
        nombre_completo: str,
        role: str,
        email: Optional[str] = None,
    ) -> 'Usuario':
        return Usuario(
            id=0,
            username=username,
            password_hash=password_hash,
            nombre_completo=nombre_completo,
            email=email,
            role=role,
            activo=True,
            fecha_creacion=datetime.now()
        )
