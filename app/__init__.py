"""
app/__init__.py — Application Factory
=======================================
Patrón Factory: crea y configura la app Flask.
Permite múltiples instancias (útil para testing).

Para agregar un nuevo Blueprint:
  1. Créalo en app/blueprints/mi_modulo.py
  2. Impórtalo aquí y regístralo con app.register_blueprint()
"""

import os
from flask import Flask
from config import Config


def create_app(config_class: object = Config) -> Flask:
    """Crea y configura la aplicación Flask."""

    app = Flask(
        __name__,
        template_folder=os.path.join(os.path.dirname(__file__), "..", "templates"),
        static_folder=os.path.join(os.path.dirname(__file__), "..", "static"),
    )

    # ── Cargar configuración ───────────────────────────────
    app.config.from_object(config_class)

    # ── Crear carpeta de uploads si no existe ──────────────
    os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)

    # ── Registrar Blueprints ───────────────────────────────
    from app.blueprints.main import main_bp
    from app.blueprints.upload import upload_bp
    from app.blueprints.scatter import scatter_bp

    app.register_blueprint(main_bp)
    app.register_blueprint(upload_bp, url_prefix="/api/upload")
    app.register_blueprint(scatter_bp, url_prefix="/api/scatter")

    return app
