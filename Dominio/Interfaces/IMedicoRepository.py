from Dominio.Entidades.Medico import Medico
from typing import List, Optional

class IMedicoRepository:
    def get_by_id(self, id: int) -> Optional[Medico]: pass
    def get_by_especialidad(self, especialidad_id: int) -> List[Medico]: pass
    def get_all(self) -> List[Medico]: pass
    def create(self, medico: Medico) -> int: pass
    def update(self, medico: Medico) -> bool: pass
    def delete(self, id: int) -> bool: pass
