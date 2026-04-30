"""
app/blueprints/scatter.py — Blueprint de datos del gráfico
===========================================================
Genera los datos para el gráfico 3D y los KPIs.
Registrado con prefijo /api/scatter en app/__init__.py

Endpoints:
    GET /api/scatter/data     → datos para Plotly 3D
    GET /api/scatter/kpis     → KPIs del filtro activo
    GET /api/scatter/filtros  → valores únicos para los filtros
"""

from flask import Blueprint, request, jsonify, session, current_app
from app.utils.file_handler import read_csv_safe, FileValidationError

scatter_bp = Blueprint("scatter", __name__)


def _get_dataframe():
    """
    Carga el DataFrame desde la sesión activa.
    Lanza ValueError si no hay CSV cargado.
    """
    csv_path = session.get("csv_path")
    if not csv_path:
        raise ValueError("No hay ningún CSV cargado. Sube un archivo primero.")
    return read_csv_safe(csv_path)


def _apply_filters(df, params):
    """
    Aplica filtros categóricos recibidos como query params.
    Acepta múltiples valores por columna: ?zona=Norte&zona=Sur
    Ignora columnas que no existen en el DataFrame (seguridad).
    """
    columnas_categoricas = df.select_dtypes(include="object").columns.tolist()

    for col in columnas_categoricas:
        valores = params.getlist(col)
        if valores:
            if col in df.columns:
                df = df[df[col].isin(valores)]

    return df


def _validate_numeric_col(df, col_name: str, default: str) -> str:
    """
    Valida que una columna exista y sea numérica.
    Retorna la columna default si no es válida (evita inyección).
    """
    numeric_cols = df.select_dtypes(include="number").columns.tolist()
    return col_name if col_name in numeric_cols else default


def _validate_unique_axes(eje_x: str, eje_y: str, eje_z: str) -> tuple[bool, str]:
    """
    Valida que los tres ejes no compartan la misma columna.
    Retorna (True, "") si son únicos, o (False, mensaje_error) si hay duplicados.
    """
    ejes = {"X": eje_x, "Y": eje_y, "Z": eje_z}
    vistos = {}
    duplicados = {}

    for axis_name, col in ejes.items():
        if col in vistos:
            duplicados[col] = [vistos[col], axis_name]
        else:
            vistos[col] = axis_name

    if duplicados:
        msgs = []
        for col, axes in duplicados.items():
            msgs.append(f'"{col}" está usada en los ejes {", ".join(axes)}')
        return False, f"Error de validación: {'; '.join(msgs)}. Cada eje debe tener una columna numérica distinta."

    return True, ""


@scatter_bp.route("/filtros", methods=["GET"])
def get_filtros():
    """
    Retorna los valores únicos de cada columna categórica
    para poblar los filtros del frontend dinámicamente.
    """
    try:
        df = _get_dataframe()
    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except FileValidationError as e:
        return jsonify({"error": str(e)}), 422

    cat_cols = df.select_dtypes(include="object").columns.tolist()
    num_cols = df.select_dtypes(include="number").columns.tolist()

    filtros = {}
    for col in cat_cols:
        filtros[col] = sorted(df[col].dropna().unique().tolist())

    return jsonify({
        "filtros": filtros,
        "columnas_numericas": num_cols,
    })


@scatter_bp.route("/data", methods=["GET"])
def scatter_data():
    """
    Genera las trazas para Plotly 3D.

    Query params:
        eje_x, eje_y, eje_z  — columnas numéricas para cada eje
        color_por            — columna categórica para agrupar trazas
        [filtros dinámicos]  — cualquier columna categórica del CSV
    """
    try:
        df = _get_dataframe()
    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except FileValidationError as e:
        return jsonify({"error": str(e)}), 422

    num_cols = df.select_dtypes(include="number").columns.tolist()
    if not num_cols:
        return jsonify({"error": "No hay columnas numéricas en el CSV."}), 422

    # Ejes (validados contra columnas reales)
    default_x = num_cols[0]
    default_y = num_cols[1] if len(num_cols) > 1 else num_cols[0]
    default_z = num_cols[2] if len(num_cols) > 2 else num_cols[0]

    eje_x = _validate_numeric_col(df, request.args.get("eje_x", default_x), default_x)
    eje_y = _validate_numeric_col(df, request.args.get("eje_y", default_y), default_y)
    eje_z = _validate_numeric_col(df, request.args.get("eje_z", default_z), default_z)

    # ── VALIDACIÓN: ejes únicos ──────────────────────────
    ok, error_msg = _validate_unique_axes(eje_x, eje_y, eje_z)
    if not ok:
        return jsonify({"error": error_msg}), 422

    # Columna para colorear las trazas
    cat_cols = df.select_dtypes(include="object").columns.tolist()
    color_por = request.args.get("color_por", cat_cols[0] if cat_cols else None)
    if color_por not in df.columns:
        color_por = None

    # Aplicar filtros dinámicos
    df = _apply_filters(df, request.args)

    if df.empty:
        return jsonify({"traces": [], "mensaje": "Sin datos para los filtros seleccionados."})

    # Construir trazas
    traces = []
    if color_por:
        for group_val, grupo in df.groupby(color_por):
            hover_text = grupo.apply(
                lambda row: " · ".join(str(row[c]) for c in cat_cols), axis=1
            ).tolist()

            traces.append({
                "name": str(group_val),
                "x": grupo[eje_x].tolist(),
                "y": grupo[eje_y].tolist(),
                "z": grupo[eje_z].tolist(),
                "text": hover_text,
            })
    else:
        traces.append({
            "name": "Datos",
            "x": df[eje_x].tolist(),
            "y": df[eje_y].tolist(),
            "z": df[eje_z].tolist(),
            "text": df.apply(lambda r: " · ".join(str(r[c]) for c in cat_cols), axis=1).tolist(),
        })

    return jsonify({
        "traces": traces,
        "ejes": {"x": eje_x, "y": eje_y, "z": eje_z},
        "total_registros": len(df),
    })


@scatter_bp.route("/kpis", methods=["GET"])
def kpis():
    """
    Calcula KPIs (suma, promedio, máx) de las columnas numéricas
    según los filtros activos.
    """
    try:
        df = _get_dataframe()
    except (ValueError, FileValidationError) as e:
        return jsonify({"error": str(e)}), 400

    # ── VALIDACIÓN: ejes únicos también en KPIs ──────────
    num_cols = df.select_dtypes(include="number").columns.tolist()
    default_x = num_cols[0] if num_cols else ""
    default_y = num_cols[1] if len(num_cols) > 1 else default_x
    default_z = num_cols[2] if len(num_cols) > 2 else default_x

    eje_x = _validate_numeric_col(df, request.args.get("eje_x", default_x), default_x)
    eje_y = _validate_numeric_col(df, request.args.get("eje_y", default_y), default_y)
    eje_z = _validate_numeric_col(df, request.args.get("eje_z", default_z), default_z)

    ok, error_msg = _validate_unique_axes(eje_x, eje_y, eje_z)
    if not ok:
        return jsonify({"error": error_msg}), 422

    df = _apply_filters(df, request.args)
    num_cols = df.select_dtypes(include="number").columns.tolist()

    kpis_data = {}
    for col in num_cols:
        kpis_data[col] = {
            "suma":     int(df[col].sum()),
            "promedio": round(float(df[col].mean()), 2),
            "maximo":   int(df[col].max()),
            "minimo":   int(df[col].min()),
        }

    return jsonify({
        "kpis":      kpis_data,
        "registros": len(df),
    })