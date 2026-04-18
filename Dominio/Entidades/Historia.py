from datetime import datetime
from dataclasses import dataclass
from typing import Optional

@dataclass
class Historia:
    id: int
    numero_historia: str
    medico_id: int
    turno: str
    responsable_triaje_id: int
    estado: str
    usuario_registro_id: int
    fecha_registro: datetime

    @staticmethod
    def create(numero_historia: str, medico_id: int,
               turno: str, responsable_triaje_id: int, usuario_registro_id: int,
               fecha_registro: Optional[datetime] = None,
               estado: str = "Pendiente") -> 'Historia':
        return Historia(
            id=0,
            numero_historia=numero_historia,
            medico_id=medico_id,
            turno=turno,
            responsable_triaje_id=responsable_triaje_id,
            estado=estado,
            usuario_registro_id=usuario_registro_id,
            fecha_registro=fecha_registro or datetime.now()
        )
