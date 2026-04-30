"""
config.py — Configuración centralizada de la aplicación
========================================================
Todas las variables de entorno y constantes se definen aquí.
Para agregar una nueva config, añádela a esta clase y úsala
con app.config['MI_VARIABLE'] desde cualquier parte del proyecto.
"""

import os
from dotenv import load_dotenv

load_dotenv()  # Carga variables desde el archivo .env


class Config:
    # ── Seguridad ──────────────────────────────────────────
    SECRET_KEY: str = os.getenv("SECRET_KEY", "dev-secret-key-change-in-production")

    # ── Uploads ────────────────────────────────────────────
    UPLOAD_FOLDER: str = os.getenv("UPLOAD_FOLDER", "data/uploads")
    # Solo se permiten archivos CSV
    ALLOWED_EXTENSIONS: set = {"csv"}
    # Tamaño máximo: 5 MB
    MAX_CONTENT_LENGTH: int = int(os.getenv("MAX_CONTENT_LENGTH", 5 * 1024 * 1024))

    # ── Flask ──────────────────────────────────────────────
    DEBUG: bool = os.getenv("FLASK_ENV", "development") == "development"
