from Dominio.Entidades.Historia import Historia
from typing import List, Optional
from datetime import datetime

class IHistoriaRepository:
    def get_by_id(self, id: int) -> Optional[Historia]: pass
    def get_by_fecha(self, fecha: datetime) -> List[Historia]: pass
    def get_all(self) -> List[Historia]: pass
    def create(self, historia: Historia) -> int: pass
    def update(self, historia: Historia) -> bool: pass
    def delete(self, id: int) -> bool: pass
    def update_estado(self, id: int, nuevo_estado: str) -> bool: pass
