"""
app/blueprints/main.py — Blueprint principal
=============================================
Sirve la página principal del dashboard.
Agrega aquí rutas de vistas adicionales (about, docs, etc.).
"""

from flask import Blueprint, render_template

main_bp = Blueprint("main", __name__)


@main_bp.route("/")
def index():
    """Página principal del visualizador."""
    return render_template("index.html")
