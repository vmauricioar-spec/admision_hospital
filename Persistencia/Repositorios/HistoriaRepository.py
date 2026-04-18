from Dominio.Interfaces.IHistoriaRepository import IHistoriaRepository
from Dominio.Entidades.Historia import Historia
from Persistencia.Conexion.DatabaseConnection import DatabaseConnection
from typing import List, Optional, Tuple
from datetime import datetime, date, time

class HistoriaRepository(IHistoriaRepository):
    def __init__(self):
        self.db = DatabaseConnection.get_instance()

    def _map_to_entity(self, row) -> Historia:
        return Historia(
            id=row[0],
            numero_historia=row[1],
            medico_id=row[2],
            turno=row[3],
            responsable_triaje_id=row[4],
            estado=row[5],
            usuario_registro_id=row[6],
            fecha_registro=row[7]
        )

    def _map_to_resumen(self, row) -> dict:
        return {
            'id': row[0],
            'numero_historia': row[1],
            'especialidad': row[2],
            'medico': row[3],
            'turno': row[4],
            'responsable_triaje': row[5],
            'estado': row[6],
            'fecha_registro': row[7].strftime('%d/%m/%Y %H:%M')
        }

    def get_by_id(self, id: int) -> Optional[Historia]:
        conn = self.db.get_connection()
        cursor = conn.cursor()
        cursor.execute(
            """SELECT IdHistoria, NumeroHistoria, IdMedico, Turno, 
               IdResponsableTriaje, Estado, IdUsuarioRegistro, FechaRegistro 
               FROM Historias WHERE IdHistoria = ?""",
            id,
        )
        row = cursor.fetchone()
        cursor.close()
        return self._map_to_entity(row) if row else None

    def get_by_fecha(self, fecha: datetime) -> List[Historia]:
        conn = self.db.get_connection()
        cursor = conn.cursor()
        cursor.execute(
            """SELECT IdHistoria, NumeroHistoria, IdMedico, Turno, 
               IdResponsableTriaje, Estado, IdUsuarioRegistro, FechaRegistro 
               FROM Historias WHERE CAST(FechaRegistro AS DATE) = CAST(? AS DATE)
               ORDER BY FechaRegistro DESC""", fecha)
        rows = cursor.fetchall()
        cursor.close()
        return [self._map_to_entity(row) for row in rows]

    def get_all(self) -> List[Historia]:
        conn = self.db.get_connection()
        cursor = conn.cursor()
        cursor.execute(
            """SELECT IdHistoria, NumeroHistoria, IdMedico, Turno, 
               IdResponsableTriaje, Estado, IdUsuarioRegistro, FechaRegistro 
               FROM Historias ORDER BY FechaRegistro DESC"""
        )
        rows = cursor.fetchall()
        cursor.close()
        return [self._map_to_entity(row) for row in rows]

    def get_resumen_all(self) -> List[dict]:
        conn = self.db.get_connection()
        cursor = conn.cursor()
        cursor.execute(
            """SELECT h.IdHistoria, h.NumeroHistoria, e.NombreEspecialidad AS Especialidad, m.NombreMedico AS Medico,
                      h.Turno, r.NombreResponsable AS ResponsableTriaje, h.Estado, h.FechaRegistro
               FROM Historias h
               INNER JOIN Medicos m ON h.IdMedico = m.IdMedico
               LEFT JOIN Especialidades e ON m.IdEspecialidad = e.IdEspecialidad
               LEFT JOIN ResponsablesTriaje r ON h.IdResponsableTriaje = r.IdResponsableTriaje
               ORDER BY h.FechaRegistro DESC"""
        )
        rows = cursor.fetchall()
        cursor.close()
        return [self._map_to_resumen(row) for row in rows]

    def get_resumen_by_fecha(self, fecha: datetime) -> List[dict]:
        conn = self.db.get_connection()
        cursor = conn.cursor()
        cursor.execute(
            """SELECT h.IdHistoria, h.NumeroHistoria, e.NombreEspecialidad AS Especialidad, m.NombreMedico AS Medico,
                      h.Turno, r.NombreResponsable AS ResponsableTriaje, h.Estado, h.FechaRegistro
               FROM Historias h
               INNER JOIN Medicos m ON h.IdMedico = m.IdMedico
               LEFT JOIN Especialidades e ON m.IdEspecialidad = e.IdEspecialidad
               LEFT JOIN ResponsablesTriaje r ON h.IdResponsableTriaje = r.IdResponsableTriaje
               WHERE CAST(h.FechaRegistro AS DATE) = CAST(? AS DATE)
               ORDER BY h.FechaRegistro DESC""",
            fecha
        )
        rows = cursor.fetchall()
        cursor.close()
        return [self._map_to_resumen(row) for row in rows]

    def create(self, historia: Historia) -> int:
        conn = self.db.get_connection()
        cursor = conn.cursor()
        cursor.execute(
            """INSERT INTO Historias (NumeroHistoria, IdMedico, Turno, 
               IdResponsableTriaje, Estado, IdUsuarioRegistro, FechaRegistro)
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (historia.numero_historia, historia.medico_id,
             historia.turno, historia.responsable_triaje_id, historia.estado,
             historia.usuario_registro_id, historia.fecha_registro)
        )
        conn.commit()
        cursor.execute("SELECT SCOPE_IDENTITY()")
        last_id = cursor.fetchone()[0]
        cursor.close()
        return last_id

    def update(self, historia: Historia) -> bool:
        conn = self.db.get_connection()
        cursor = conn.cursor()
        cursor.execute(
            """UPDATE Historias SET NumeroHistoria=?, IdMedico=?, 
               Turno=?, IdResponsableTriaje=?, Estado=? WHERE IdHistoria=?""",
            (historia.numero_historia, historia.medico_id,
             historia.turno, historia.responsable_triaje_id, historia.estado, historia.id)
        )
        conn.commit()
        cursor.close()
        return True

    def delete(self, id: int) -> bool:
        conn = self.db.get_connection()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM Historias WHERE IdHistoria = ?", id)
        conn.commit()
        cursor.close()
        return True

    def update_estado(self, id: int, nuevo_estado: str) -> bool:
        conn = self.db.get_connection()
        cursor = conn.cursor()
        cursor.execute("UPDATE Historias SET Estado = ? WHERE IdHistoria = ?", (nuevo_estado, id))
        conn.commit()
        cursor.close()
        return True

    def count_by_medico(self, medico_id: int) -> int:
        conn = self.db.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(1) FROM Historias WHERE IdMedico = ?", medico_id)
        total = cursor.fetchone()[0]
        cursor.close()
        return int(total)

    def list_id_medico_turno_por_numero_fecha(
        self, numero_historia: str, fecha_dia: date
    ) -> List[Tuple[int, int, str]]:
        """Filas con ese número (trim) ese día: lista de (Id, MedicoId, Turno)."""
        conn = self.db.get_connection()
        cursor = conn.cursor()
        fecha_param = datetime.combine(fecha_dia, time.min)
        numero_norm = (numero_historia or "").strip()
        cursor.execute(
            """SELECT IdHistoria, IdMedico, Turno FROM Historias
               WHERE CAST(FechaRegistro AS DATE) = CAST(? AS DATE)
               AND LTRIM(RTRIM(NumeroHistoria)) = ?""",
            (fecha_param, numero_norm),
        )
        rows = cursor.fetchall()
        cursor.close()
        return [(int(row[0]), int(row[1]), str(row[2] or "").strip()) for row in rows]
