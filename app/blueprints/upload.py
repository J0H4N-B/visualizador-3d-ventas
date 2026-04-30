"""
app/blueprints/upload.py — Blueprint de carga de archivos
==========================================================
Maneja la subida y análisis inicial del CSV.
Registrado con prefijo /api/upload en app/__init__.py

Endpoints:
    POST /api/upload/csv      → sube un CSV, retorna session_id + columnas
    GET  /api/upload/sample   → descarga el CSV de ejemplo
"""

import os
from flask import Blueprint, request, jsonify, current_app, send_file, session
from app.utils.file_handler import (
    save_uploaded_file,
    read_csv_safe,
    get_numeric_columns,
    get_categorical_columns,
    cleanup_old_uploads,
    FileValidationError,
)

upload_bp = Blueprint("upload", __name__)


@upload_bp.route("/csv", methods=["POST"])
def upload_csv():
    """
    Recibe un archivo CSV del frontend.
    Retorna las columnas detectadas para que el usuario
    configure qué métricas mostrar en el gráfico.
    """
    if "file" not in request.files:
        return jsonify({"error": "No se encontró el campo 'file' en la solicitud."}), 400

    file = request.files["file"]

    try:
        # 1. Guardar de forma segura
        filepath = save_uploaded_file(file)

        # 2. Leer y validar el CSV
        df = read_csv_safe(filepath)

        # 3. Limpiar uploads viejos si hay demasiados
        cleanup_old_uploads(current_app.config["UPLOAD_FOLDER"], max_files=50)

        # 4. Guardar la ruta en sesión (en vez de exponerla al cliente)
        session["csv_path"] = filepath
        session["csv_name"] = file.filename

        numeric_cols     = get_numeric_columns(df)
        categorical_cols = get_categorical_columns(df)

        if len(numeric_cols) < 2:
            return jsonify({
                "error": "El CSV debe tener al menos 2 columnas numéricas para graficar."
            }), 422

        return jsonify({
            "ok":              True,
            "filename":        file.filename,
            "filas":           len(df),
            "columnas_total":  len(df.columns),
            "columnas_numericas":    numeric_cols,
            "columnas_categoricas":  categorical_cols,
            "preview":         df.head(5).to_dict(orient="records"),
        })

    except FileValidationError as e:
        return jsonify({"error": str(e)}), 422
    except Exception as e:
        current_app.logger.error(f"Error inesperado en upload: {e}")
        return jsonify({"error": "Error interno al procesar el archivo."}), 500


@upload_bp.route("/sample", methods=["GET"])
def download_sample():
    """Sirve el CSV de ejemplo para que el usuario vea el formato esperado."""
    sample_path = os.path.join(
        current_app.root_path, "..", "data", "ventas_ejemplo.csv"
    )
    sample_path = os.path.abspath(sample_path)

    if not os.path.exists(sample_path):
        return jsonify({"error": "Archivo de ejemplo no encontrado."}), 404

    return send_file(sample_path, as_attachment=True, download_name="ventas_ejemplo.csv")
