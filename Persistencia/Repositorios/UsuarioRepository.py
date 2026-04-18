from Dominio.Interfaces.IUsuarioRepository import IUsuarioRepository
from Dominio.Entidades.Usuario import Usuario
from Persistencia.Conexion.DatabaseConnection import DatabaseConnection
from typing import List, Optional

class UsuarioRepository(IUsuarioRepository):
    def __init__(self):
        self.db = DatabaseConnection.get_instance()
        try:
            self._ensure_email_column()
        except Exception as exc:
            print(f"[WARN] No se pudo validar columna CorreoElectronico al iniciar: {exc}")

    def _ensure_email_column(self):
        conn = self.db.get_connection()
        cursor = conn.cursor()
        cursor.execute(
            """
            IF OBJECT_ID('Usuarios', 'U') IS NOT NULL
            BEGIN
                IF NOT EXISTS (
                    SELECT 1
                    FROM sys.columns
                    WHERE object_id = OBJECT_ID('Usuarios')
                      AND name = 'CorreoElectronico'
                )
                BEGIN
                    ALTER TABLE Usuarios ADD CorreoElectronico VARCHAR(150) NULL;
                END
            END
            ELSE IF OBJECT_ID('Usuario', 'U') IS NOT NULL
            BEGIN
                IF NOT EXISTS (
                    SELECT 1
                    FROM sys.columns
                    WHERE object_id = OBJECT_ID('Usuario')
                      AND name = 'Email'
                )
                BEGIN
                    ALTER TABLE Usuario ADD Email VARCHAR(150) NULL;
                END
            END
            """
        )
        conn.commit()
        cursor.close()

    def _map_to_entity(self, row) -> Usuario:
        return Usuario(
            id=row[0],
            username=row[1],
            password_hash=row[2],
            nombre_completo=row[3],
            email=row[4] if len(row) > 4 else None,
            role=row[5],
            activo=bool(row[6]),
            fecha_creacion=row[7]
        )

    def get_by_id(self, id: int) -> Optional[Usuario]:
        conn = self.db.get_connection()
        cursor = conn.cursor()
        cursor.execute(
            """SELECT IdUsuario, NombreUsuario, HashContrasena, NombreCompleto,
                      CorreoElectronico, Rol, Activo, FechaCreacion
               FROM Usuarios WHERE IdUsuario = ?""",
            id,
        )
        row = cursor.fetchone()
        cursor.close()
        return self._map_to_entity(row) if row else None

    def get_by_username(self, username: str) -> Optional[Usuario]:
        conn = self.db.get_connection()
        cursor = conn.cursor()
        cursor.execute(
            """SELECT IdUsuario, NombreUsuario, HashContrasena, NombreCompleto,
                      CorreoElectronico, Rol, Activo, FechaCreacion
               FROM Usuarios WHERE NombreUsuario = ?""",
            username,
        )
        row = cursor.fetchone()
        cursor.close()
        return self._map_to_entity(row) if row else None

    def get_by_email(self, email: str) -> Optional[Usuario]:
        conn = self.db.get_connection()
        cursor = conn.cursor()
        cursor.execute(
            """SELECT IdUsuario, NombreUsuario, HashContrasena, NombreCompleto,
                      CorreoElectronico, Rol, Activo, FechaCreacion
               FROM Usuarios WHERE CorreoElectronico = ?""",
            email,
        )
        row = cursor.fetchone()
        cursor.close()
        return self._map_to_entity(row) if row else None

    def get_all(self) -> List[Usuario]:
        conn = self.db.get_connection()
        cursor = conn.cursor()
        cursor.execute(
            """SELECT IdUsuario, NombreUsuario, HashContrasena, NombreCompleto,
                      CorreoElectronico, Rol, Activo, FechaCreacion
               FROM Usuarios ORDER BY FechaCreacion DESC"""
        )
        rows = cursor.fetchall()
        cursor.close()
        return [self._map_to_entity(row) for row in rows]

    def create(self, usuario: Usuario) -> int:
        conn = self.db.get_connection()
        cursor = conn.cursor()
        cursor.execute(
            """INSERT INTO Usuarios (
                    NombreUsuario,
                    HashContrasena,
                    NombreCompleto,
                    Rol,
                    Activo,
                    FechaCreacion,
                    CorreoElectronico
               )
               OUTPUT INSERTED.IdUsuario
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (
                usuario.username,
                usuario.password_hash,
                usuario.nombre_completo,
                usuario.role,
                1,
                usuario.fecha_creacion,
                usuario.email,
            )
        )
        row = cursor.fetchone()
        conn.commit()
        cursor.close()
        if not row or row[0] is None:
            raise RuntimeError("No se pudo obtener el IdUsuario luego de crear el usuario.")
        return int(row[0])

    def update(self, usuario: Usuario) -> bool:
        conn = self.db.get_connection()
        cursor = conn.cursor()
        cursor.execute(
            """UPDATE Usuarios SET NombreUsuario=?, HashContrasena=?, NombreCompleto=?, Rol=?, Activo=?, CorreoElectronico=? WHERE IdUsuario=?""",
            (
                usuario.username,
                usuario.password_hash,
                usuario.nombre_completo,
                usuario.role,
                usuario.activo,
                usuario.email,
                usuario.id,
            )
        )
        conn.commit()
        cursor.close()
        return True

    def update_password_hash(self, usuario_id: int, nuevo_hash: str) -> bool:
        conn = self.db.get_connection()
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE Usuarios SET HashContrasena = ? WHERE IdUsuario = ?",
            (nuevo_hash, usuario_id),
        )
        conn.commit()
        cursor.close()
        return True

    def delete(self, id: int) -> bool:
        conn = self.db.get_connection()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM Usuarios WHERE IdUsuario = ?", id)
        conn.commit()
        cursor.close()
        return True
