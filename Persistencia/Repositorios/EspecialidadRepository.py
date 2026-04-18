from Dominio.Interfaces.IEspecialidadRepository import IEspecialidadRepository
from Dominio.Entidades.Especialidad import Especialidad
from Persistencia.Conexion.DatabaseConnection import DatabaseConnection
from typing import List, Optional

class EspecialidadRepository(IEspecialidadRepository):
    def __init__(self):
        self.db = DatabaseConnection.get_instance()

    def _map_to_entity(self, row) -> Especialidad:
        return Especialidad(
            id=row[0],
            nombre=row[1],
            descripcion=row[2] if len(row) > 2 else ""
        )

    def get_by_id(self, id: int) -> Optional[Especialidad]:
        conn = self.db.get_connection()
        cursor = conn.cursor()
        cursor.execute(
            "SELECT IdEspecialidad, NombreEspecialidad, Descripcion FROM Especialidades WHERE IdEspecialidad = ?",
            id,
        )
        row = cursor.fetchone()
        cursor.close()
        return self._map_to_entity(row) if row else None

    def get_by_nombre(self, nombre: str) -> Optional[Especialidad]:
        conn = self.db.get_connection()
        cursor = conn.cursor()
        cursor.execute(
            "SELECT IdEspecialidad, NombreEspecialidad, Descripcion FROM Especialidades WHERE NombreEspecialidad = ?",
            nombre,
        )
        row = cursor.fetchone()
        cursor.close()
        return self._map_to_entity(row) if row else None

    def get_all(self) -> List[Especialidad]:
        conn = self.db.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT IdEspecialidad, NombreEspecialidad, Descripcion FROM Especialidades ORDER BY NombreEspecialidad")
        rows = cursor.fetchall()
        cursor.close()
        return [self._map_to_entity(row) for row in rows]

    def create(self, especialidad: Especialidad) -> int:
        conn = self.db.get_connection()
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO Especialidades (NombreEspecialidad, Descripcion) VALUES (?, ?)",
            (especialidad.nombre, especialidad.descripcion)
        )
        conn.commit()
        cursor.execute("SELECT SCOPE_IDENTITY()")
        last_id = cursor.fetchone()[0]
        cursor.close()
        return last_id

    def update(self, especialidad: Especialidad) -> bool:
        conn = self.db.get_connection()
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE Especialidades SET NombreEspecialidad=?, Descripcion=? WHERE IdEspecialidad=?",
            (especialidad.nombre, especialidad.descripcion, especialidad.id)
        )
        conn.commit()
        cursor.close()
        return True

    def delete(self, id: int) -> bool:
        conn = self.db.get_connection()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM Especialidades WHERE IdEspecialidad = ?", id)
        conn.commit()
        cursor.close()
        return True
