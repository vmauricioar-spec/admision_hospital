import os
from flask import Flask, render_template, request
from dotenv import load_dotenv

load_dotenv()

from Presentacion.Rutas.auth_routes import auth_bp
from Presentacion.Rutas.admin_routes import admin_bp
from Presentacion.Rutas.admission_routes import admission_bp
from Presentacion.sesion_cache import redirect_al_panel_si_hay_sesion, aplicar_no_cache_privado

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", "historias_clinicas_secret_key_2024")

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

if __name__ == '__main__':
    port = int(os.getenv("PORT", "5000"))
    debug = (os.getenv("FLASK_DEBUG", "false").lower() in ("1", "true", "yes", "y"))
    app.run(debug=debug, host='0.0.0.0', port=port)
