"""
app/utils/file_handler.py — Utilidades de manejo seguro de archivos
====================================================================
Centraliza toda la lógica de validación y lectura de CSV.
Si necesitas soportar otros formatos (Excel, JSON), agrégalos aquí.
"""

import os
import uuid
import pandas as pd
from flask import current_app
from werkzeug.utils import secure_filename
from werkzeug.datastructures import FileStorage


class FileValidationError(Exception):
    """Error de validación de archivo."""
    pass


def allowed_file(filename: str) -> bool:
    """Verifica que el archivo tenga una extensión permitida."""
    allowed = current_app.config.get("ALLOWED_EXTENSIONS", {"csv"})
    return (
        "." in filename
        and filename.rsplit(".", 1)[1].lower() in allowed
    )


def save_uploaded_file(file: FileStorage) -> str:
    """
    Guarda un archivo subido de forma segura.

    - Sanitiza el nombre original con secure_filename.
    - Agrega un UUID para evitar colisiones entre usuarios.
    - Retorna la ruta absoluta del archivo guardado.

    Lanza FileValidationError si el archivo no es válido.
    """
    if not file or file.filename == "":
        raise FileValidationError("No se recibió ningún archivo.")

    if not allowed_file(file.filename):
        raise FileValidationError(
            "Tipo de archivo no permitido. Solo se aceptan archivos .csv"
        )

    # Nombre seguro + UUID para evitar sobreescrituras
    safe_name = secure_filename(file.filename)
    unique_name = f"{uuid.uuid4().hex}_{safe_name}"
    upload_folder = current_app.config["UPLOAD_FOLDER"]
    filepath = os.path.join(upload_folder, unique_name)

    file.save(filepath)
    return filepath


def read_csv_safe(filepath: str, max_rows: int = 10_000) -> pd.DataFrame:
    """
    Lee un CSV con validaciones de seguridad:
    - Límite de filas para evitar ataques de memoria.
    - Manejo de encodings comunes (utf-8, latin-1).
    - Limpieza de nombres de columnas.

    Lanza FileValidationError si el CSV no es legible o válido.
    """
    if not os.path.exists(filepath):
        raise FileValidationError("Archivo no encontrado en el servidor.")

    for encoding in ("utf-8", "latin-1", "utf-8-sig"):
        try:
            df = pd.read_csv(filepath, nrows=max_rows, encoding=encoding)
            break
        except UnicodeDecodeError:
            continue
        except Exception as e:
            raise FileValidationError(f"Error al leer el CSV: {str(e)}")
    else:
        raise FileValidationError("No se pudo decodificar el archivo CSV.")

    if df.empty:
        raise FileValidationError("El CSV está vacío.")

    if len(df.columns) < 2:
        raise FileValidationError("El CSV debe tener al menos 2 columnas.")

    # Limpiar nombres de columnas
    df.columns = (
        df.columns
        .str.strip()
        .str.lower()
        .str.replace(" ", "_")
        .str.replace(r"[^\w]", "", regex=True)
    )

    return df


def get_numeric_columns(df: pd.DataFrame) -> list[str]:
    """Retorna solo las columnas numéricas del DataFrame."""
    return df.select_dtypes(include="number").columns.tolist()


def get_categorical_columns(df: pd.DataFrame) -> list[str]:
    """Retorna las columnas categóricas (objeto/string) del DataFrame."""
    return df.select_dtypes(include="object").columns.tolist()


def cleanup_old_uploads(upload_folder: str, max_files: int = 50) -> None:
    """
    Limpia archivos antiguos si la carpeta supera max_files archivos.
    Elimina los más antiguos primero (FIFO).
    Llama a esta función en uploads frecuentes para evitar llenar el disco.
    """
    files = sorted(
        [os.path.join(upload_folder, f) for f in os.listdir(upload_folder)],
        key=os.path.getctime,
    )
    while len(files) > max_files:
        os.remove(files.pop(0))
