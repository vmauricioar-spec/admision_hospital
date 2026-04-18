from Dominio.Interfaces.IResponsableTriajeRepository import IResponsableTriajeRepository
from Dominio.Entidades.ResponsableTriaje import ResponsableTriaje
from Persistencia.Conexion.DatabaseConnection import DatabaseConnection
from typing import List, Optional

class ResponsableTriajeRepository(IResponsableTriajeRepository):
    def __init__(self):
        self.db = DatabaseConnection.get_instance()

    def _map_to_entity(self, row) -> ResponsableTriaje:
        return ResponsableTriaje(
            id=row[0],
            nombre=row[1],
            area=row[2] if len(row) > 2 else ""
        )

    def get_by_id(self, id: int) -> Optional[ResponsableTriaje]:
        conn = self.db.get_connection()
        cursor = conn.cursor()
        cursor.execute(
            "SELECT IdResponsableTriaje, NombreResponsable, Area FROM ResponsablesTriaje WHERE IdResponsableTriaje = ?",
            id,
        )
        row = cursor.fetchone()
        cursor.close()
        return self._map_to_entity(row) if row else None

    def get_all(self) -> List[ResponsableTriaje]:
        conn = self.db.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT IdResponsableTriaje, NombreResponsable, Area FROM ResponsablesTriaje ORDER BY NombreResponsable")
        rows = cursor.fetchall()
        cursor.close()
        return [self._map_to_entity(row) for row in rows]

    def get_by_nombre(self, nombre: str) -> Optional[ResponsableTriaje]:
        conn = self.db.get_connection()
        cursor = conn.cursor()
        cursor.execute(
            "SELECT TOP 1 IdResponsableTriaje, NombreResponsable, Area FROM ResponsablesTriaje WHERE LOWER(NombreResponsable) = LOWER(?)",
            nombre
        )
        row = cursor.fetchone()
        cursor.close()
        return self._map_to_entity(row) if row else None

    def create(self, responsable: ResponsableTriaje) -> int:
        conn = self.db.get_connection()
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO ResponsablesTriaje (NombreResponsable, Area) VALUES (?, ?)",
            (responsable.nombre, responsable.area)
        )
        conn.commit()
        cursor.execute("SELECT SCOPE_IDENTITY()")
        last_id = cursor.fetchone()[0]
        cursor.close()
        return last_id

    def update(self, responsable: ResponsableTriaje) -> bool:
        conn = self.db.get_connection()
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE ResponsablesTriaje SET NombreResponsable=?, Area=? WHERE IdResponsableTriaje=?",
            (responsable.nombre, responsable.area, responsable.id)
        )
        conn.commit()
        cursor.close()
        return True

    def delete(self, id: int) -> bool:
        conn = self.db.get_connection()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM ResponsablesTriaje WHERE IdResponsableTriaje = ?", id)
        conn.commit()
        cursor.close()
        return True
