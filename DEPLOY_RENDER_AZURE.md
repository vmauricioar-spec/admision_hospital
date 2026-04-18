# Deploy a Render + Azure SQL

## 1) Subir proyecto a GitHub
- Confirma que **no** subas `.env`, `venv/` ni `.venv/` (ya se excluyen en `.gitignore`).
- Sube el código con:
  - `requirements.txt`
  - `Procfile`
  - `config/init_database.sql`
  - `config/init_database_azure.sql`

## 2) Crear y preparar Azure SQL
1. En Azure, crea:
   - SQL Server lógico
   - Base de datos `HistoriasClinicas`
2. En firewall del SQL Server, habilita acceso para servicios de Azure y agrega tu IP de administración.
3. Abre Query Editor (o SSMS/Azure Data Studio) conectado a `HistoriasClinicas`.
4. Ejecuta `config/init_database_azure.sql`.
5. Verifica tablas clave:
   - `Usuarios`
   - `Historias`
   - `MetricasContrasena`
   - `TokensRecuperacionContrasena`

## 3) Crear Web Service en Render
1. New -> Web Service -> conectar repo GitHub.
2. Runtime: Python.
3. Selecciona despliegue por `render.yaml` (Docker) para que Render instale driver ODBC de SQL Server automáticamente.

## 4) Variables de entorno en Render
Configura estas variables:

- `SECRET_KEY`: clave secreta de Flask (larga y aleatoria).
- `FLASK_DEBUG=false`
- `DB_SERVER=<tu-servidor>.database.windows.net,1433`
- `DB_NAME=free-sql-db-0676007`
- `DB_DRIVER=ODBC Driver 18 for SQL Server`
- `DB_TRUSTED=false`
- `DB_USER=<usuario_sql>`
- `DB_PASSWORD=<password_sql>`
- `DB_ENCRYPT=yes`
- `DB_TRUST_SERVER_CERTIFICATE=no`
- `DB_CONNECTION_TIMEOUT=30`
- `ALCHEMY_SOLANA_RPC_URL=<tu_url_rpc>`
- `SOLANA_SIGNER_PRIVATE_KEY=<tu_private_key_backend>`
- `GMAIL_SMTP_HOST=smtp.gmail.com`
- `GMAIL_SMTP_PORT=465`
- `GMAIL_USER=<tu_correo>`
- `GMAIL_APP_PASSWORD=<tu_app_password>`

## 5) Verificación post-deploy
1. Abrir URL pública de Render.
2. Probar login admin.
3. Generar link único y registrar usuario:
   - debe registrar hash en Solana
   - debe enviar credenciales por correo
   - debe guardar métricas de contraseña
4. Revisar vista admin de métricas.

## 6) Checklist rápido de troubleshooting
- Error de DB auth:
  - revisa `DB_TRUSTED=false`, usuario/password y firewall en Azure.
- Error de conexión TLS:
  - confirma `DB_ENCRYPT=yes` y `DB_TRUST_SERVER_CERTIFICATE=no`.
- Error al enviar correo:
  - revisa `GMAIL_USER` y `GMAIL_APP_PASSWORD`.
- Error Solana:
  - revisa `ALCHEMY_SOLANA_RPC_URL` y fondos de la wallet firmante en Devnet.
