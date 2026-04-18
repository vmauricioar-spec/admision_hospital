from Dominio.Entidades.ResponsableTriaje import ResponsableTriaje
from typing import List, Optional

class IResponsableTriajeRepository:
    def get_by_id(self, id: int) -> Optional[ResponsableTriaje]: pass
    def get_all(self) -> List[ResponsableTriaje]: pass
    def create(self, responsable: ResponsableTriaje) -> int: pass
    def update(self, responsable: ResponsableTriaje) -> bool: pass
    def delete(self, id: int) -> bool: pass
