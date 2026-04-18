from dataclasses import dataclass

@dataclass
class ResponsableTriaje:
    id: int
    nombre: str
    area: str

    @staticmethod
    def create(nombre: str, area: str = "") -> 'ResponsableTriaje':
        return ResponsableTriaje(id=0, nombre=nombre, area=area)
