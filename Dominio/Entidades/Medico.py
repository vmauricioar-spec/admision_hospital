from dataclasses import dataclass

@dataclass
class Medico:
    id: int
    nombre: str
    especialidad_id: int

    @staticmethod
    def create(nombre: str, especialidad_id: int) -> 'Medico':
        return Medico(id=0, nombre=nombre, especialidad_id=especialidad_id)
