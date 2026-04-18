from Dominio.Interfaces.IMedicoRepository import IMedicoRepository
from Dominio.Entidades.Medico import Medico
from Persistencia.Conexion.DatabaseConnection import DatabaseConnection
from typing import List, Optional

class MedicoRepository(IMedicoRepository):
    def __init__(self):
        self.db = DatabaseConnection.get_instance()

    def _map_to_entity(self, row) -> Medico:
        return Medico(
            id=row[0],
            nombre=row[1],
            especialidad_id=row[2]
        )

    def get_by_id(self, id: int) -> Optional[Medico]:
        conn = self.db.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT IdMedico, NombreMedico, IdEspecialidad FROM Medicos WHERE IdMedico = ?", id)
        row = cursor.fetchone()
        cursor.close()
        return self._map_to_entity(row) if row else None

    def get_by_especialidad(self, especialidad_id: int) -> List[Medico]:
        conn = self.db.get_connection()
        cursor = conn.cursor()
        cursor.execute(
            "SELECT IdMedico, NombreMedico, IdEspecialidad FROM Medicos WHERE IdEspecialidad = ?",
            especialidad_id
        )
        rows = cursor.fetchall()
        cursor.close()
        return [self._map_to_entity(row) for row in rows]

    def get_all(self) -> List[Medico]:
        conn = self.db.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT IdMedico, NombreMedico, IdEspecialidad FROM Medicos ORDER BY NombreMedico")
        rows = cursor.fetchall()
        cursor.close()
        return [self._map_to_entity(row) for row in rows]

    def create(self, medico: Medico) -> int:
        conn = self.db.get_connection()
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO Medicos (NombreMedico, IdEspecialidad) VALUES (?, ?)",
            (medico.nombre, medico.especialidad_id)
        )
        conn.commit()
        cursor.execute("SELECT SCOPE_IDENTITY()")
        last_id = cursor.fetchone()[0]
        cursor.close()
        return last_id

    def update(self, medico: Medico) -> bool:
        conn = self.db.get_connection()
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE Medicos SET NombreMedico=?, IdEspecialidad=? WHERE IdMedico=?",
            (medico.nombre, medico.especialidad_id, medico.id)
        )
        conn.commit()
        cursor.close()
        return True

    def delete(self, id: int) -> bool:
        conn = self.db.get_connection()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM Medicos WHERE IdMedico = ?", id)
        conn.commit()
        cursor.close()
        return True
