"""
run.py — Punto de entrada de la aplicación
===========================================
Ejecuta con:
    python run.py

En producción usa un servidor WSGI como gunicorn:
    gunicorn "run:app" --bind 0.0.0.0:8000
"""

from app import create_app

app = create_app()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
