from Dominio.Entidades.Especialidad import Especialidad
from typing import List, Optional

class IEspecialidadRepository:
    def get_by_id(self, id: int) -> Optional[Especialidad]: pass
    def get_by_nombre(self, nombre: str) -> Optional[Especialidad]: pass
    def get_all(self) -> List[Especialidad]: pass
    def create(self, especialidad: Especialidad) -> int: pass
    def update(self, especialidad: Especialidad) -> bool: pass
    def delete(self, id: int) -> bool: pass
