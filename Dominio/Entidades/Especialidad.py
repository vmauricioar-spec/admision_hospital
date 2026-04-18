from dataclasses import dataclass

@dataclass
class Especialidad:
    id: int
    nombre: str
    descripcion: str

    @staticmethod
    def create(nombre: str, descripcion: str = "") -> 'Especialidad':
        return Especialidad(id=0, nombre=nombre, descripcion=descripcion)
