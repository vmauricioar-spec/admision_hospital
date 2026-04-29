import logging
import os
import traceback
from flask import Flask, render_template, request
from dotenv import load_dotenv
import pyodbc

load_dotenv()

from Presentacion.Rutas.auth_routes import auth_bp
from Presentacion.Rutas.admin_routes import admin_bp
from Presentacion.Rutas.admission_routes import admission_bp
from Presentacion.sesion_cache import redirect_al_panel_si_hay_sesion, aplicar_no_cache_privado


def _configure_app_logging() -> None:
    """Asegura que INFO aparezca en logs de Render/Gunicorn (LOG_LEVEL opcional)."""
    level_name = (os.getenv("LOG_LEVEL") or "INFO").upper()
    level = getattr(logging, level_name, logging.INFO)
    logging.basicConfig(level=level, format="%(asctime)s %(levelname)s %(name)s: %(message)s", force=True)

    gunicorn_error_logger = logging.getLogger("gunicorn.error")
    if gunicorn_error_logger.handlers:
        logging.getLogger().handlers = gunicorn_error_logger.handlers
        logging.getLogger().setLevel(level)

    for name in (
        "app",
        "Presentacion.Rutas.admin_routes",
        "Presentacion.Rutas.auth_routes",
        "Aplicacion.Servicios.NotificationService",
    ):
        logging.getLogger(name).setLevel(level)


app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", "historias_clinicas_secret_key_2024")
_configure_app_logging()

app.register_blueprint(auth_bp)
app.register_blueprint(admin_bp)
app.register_blueprint(admission_bp)


@app.after_request
def _no_cache_html_responses(response):
    """Impide ver login o panel desde caché al usar Atrás/Adelante sin nueva petición al servidor."""
    if request.path.startswith("/static"):
        return response
    return aplicar_no_cache_privado(response)


@app.route('/')
def index():
    ya = redirect_al_panel_si_hay_sesion()
    if ya is not None:
        return ya
    return render_template('index.html')


@app.errorhandler(pyodbc.Error)
def handle_db_error(error):
    app.logger.exception("Database error: %s", error)
    if request.path.startswith("/admission/") and (
        request.is_json or "application/json" in (request.headers.get("Accept", ""))
    ):
        return {"status": "error", "message": "Error de base de datos. Intenta nuevamente."}, 500
    return render_template(
        'error.html',
        title="Error de base de datos",
        message="Tuvimos un problema temporal con la base de datos. Intenta de nuevo en unos segundos.",
    ), 500


@app.errorhandler(Exception)
def handle_unexpected_error(error):
    app.logger.error("Unhandled exception: %s\n%s", error, traceback.format_exc())
    if request.path.startswith("/admission/") and (
        request.is_json or "application/json" in (request.headers.get("Accept", ""))
    ):
        return {"status": "error", "message": "Ocurrió un error interno. Intenta nuevamente."}, 500
    return render_template(
        'error.html',
        title="Error interno del servidor",
        message="Ocurrió un error inesperado. Por favor intenta nuevamente.",
    ), 500

if __name__ == '__main__':
    port = int(os.getenv("PORT", "5000"))
    debug = (os.getenv("FLASK_DEBUG", "false").lower() in ("1", "true", "yes", "y"))
    app.run(debug=debug, host='0.0.0.0', port=port)
