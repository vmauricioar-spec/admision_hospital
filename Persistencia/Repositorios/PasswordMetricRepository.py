from datetime import timedelta
from Persistencia.Conexion.DatabaseConnection import DatabaseConnection


class PasswordMetricRepository:
    _PERU_OFFSET = timedelta(hours=-5)

    def __init__(self):
        self.db = DatabaseConnection.get_instance()
        try:
            self._ensure_table()
        except Exception as exc:
            print(f"[WARN] No se pudo validar tabla MetricasContrasena al iniciar: {exc}")

    def _to_peru_time(self, value):
        if value is None:
            return None
        return value + self._PERU_OFFSET

    def _ensure_table(self):
        conn = self.db.get_connection()
        cursor = conn.cursor()
        cursor.execute(
            """
            IF OBJECT_ID('Usuarios', 'U') IS NOT NULL
               AND NOT EXISTS (SELECT * FROM sys.tables WHERE name = 'MetricasContrasena')
            BEGIN
                CREATE TABLE MetricasContrasena (
                    IdMetricaContrasena INT IDENTITY(1,1) PRIMARY KEY,
                    IdUsuario INT NOT NULL,
                    LongitudContrasena INT NOT NULL,
                    TiempoGeneracionMs INT NOT NULL,
                    NivelFortaleza VARCHAR(20) NOT NULL,
                    FechaCreacion DATETIME NOT NULL DEFAULT GETDATE(),
                    FOREIGN KEY (IdUsuario) REFERENCES Usuarios(IdUsuario)
                )
            END
            """
        )
        conn.commit()
        cursor.close()

    def create(
        self,
        usuario_id: int,
        password_length: int,
        generation_time_ms: int,
        strength_label: str,
    ) -> int:
        if usuario_id is None:
            raise ValueError("No se recibió IdUsuario para registrar la métrica de contraseña.")
        conn = self.db.get_connection()
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO MetricasContrasena (IdUsuario, LongitudContrasena, TiempoGeneracionMs, NivelFortaleza)
            OUTPUT INSERTED.IdMetricaContrasena
            VALUES (?, ?, ?, ?)
            """,
            (usuario_id, password_length, generation_time_ms, strength_label),
        )
        row = cursor.fetchone()
        conn.commit()
        cursor.close()
        if not row or row[0] is None:
            raise RuntimeError("No se pudo obtener el IdMetricaContrasena luego de guardar la métrica.")
        return int(row[0])

    def get_all(self):
        conn = self.db.get_connection()
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT
                pm.IdMetricaContrasena,
                pm.IdUsuario,
                u.NombreUsuario,
                u.NombreCompleto,
                pm.LongitudContrasena,
                pm.TiempoGeneracionMs,
                pm.NivelFortaleza,
                pm.FechaCreacion
            FROM MetricasContrasena pm
            INNER JOIN Usuarios u ON u.IdUsuario = pm.IdUsuario
            ORDER BY pm.FechaCreacion DESC
            """
        )
        rows = cursor.fetchall()
        cursor.close()
        result = []
        for row in rows:
            result.append(
                {
                    "id": row[0],
                    "usuario_id": row[1],
                    "username": row[2],
                    "nombre_completo": row[3],
                    "password_length": int(row[4]),
                    "generation_time_ms": int(row[5]),
                    "strength_label": row[6],
                    "created_at": self._to_peru_time(row[7]),
                }
            )
        return result

    def get_summary(self):
        conn = self.db.get_connection()
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT
                COUNT(*),
                ISNULL(AVG(CAST(LongitudContrasena AS FLOAT)), 0),
                ISNULL(AVG(CAST(TiempoGeneracionMs AS FLOAT)), 0)
            FROM MetricasContrasena
            """
        )
        row = cursor.fetchone()
        cursor.close()
        total_passwords = int(row[0]) if row else 0
        avg_length = float(row[1]) if row else 0.0
        avg_generation_ms = float(row[2]) if row else 0.0
        return {
            "total_passwords": total_passwords,
            "avg_length": avg_length,
            "avg_generation_ms": avg_generation_ms,
        }

    def get_per_user(self):
        conn = self.db.get_connection()
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT
                u.IdUsuario,
                u.NombreUsuario,
                u.NombreCompleto,
                COUNT(pm.IdMetricaContrasena) AS PasswordsGenerated,
                MAX(pm.FechaCreacion) AS LastMetricAt,
                ISNULL((
                    SELECT TOP 1 pm2.LongitudContrasena
                    FROM MetricasContrasena pm2
                    WHERE pm2.IdUsuario = u.IdUsuario
                    ORDER BY pm2.FechaCreacion DESC, pm2.IdMetricaContrasena DESC
                ), 0) AS LastPasswordLength,
                ISNULL((
                    SELECT TOP 1 pm2.TiempoGeneracionMs
                    FROM MetricasContrasena pm2
                    WHERE pm2.IdUsuario = u.IdUsuario
                    ORDER BY pm2.FechaCreacion DESC, pm2.IdMetricaContrasena DESC
                ), 0) AS LastGenerationMs
            FROM Usuarios u
            LEFT JOIN MetricasContrasena pm ON pm.IdUsuario = u.IdUsuario
            GROUP BY u.IdUsuario, u.NombreUsuario, u.NombreCompleto
            ORDER BY u.IdUsuario DESC
            """
        )
        rows = cursor.fetchall()
        cursor.close()
        result = []
        for row in rows:
            result.append(
                {
                    "usuario_id": row[0],
                    "username": row[1],
                    "nombre_completo": row[2],
                    "passwords_generated": int(row[3] or 0),
                    "last_metric_at": self._to_peru_time(row[4]),
                    "last_password_length": int(row[5] or 0),
                    "last_generation_ms": int(row[6] or 0),
                }
            )
        return result
