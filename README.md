# 📊 Visualizador de Dispersión 3D de Ventas

Dashboard interactivo que permite **subir cualquier CSV**, configurar qué columnas
se muestran en cada eje del gráfico 3D y explorar correlaciones con filtros dinámicos.

## 🛠️ Stack

| Capa       | Tecnología                        |
|------------|-----------------------------------|
| Backend    | Python 3.9+ · Flask · Blueprints  |
| Datos      | Pandas · CSV (subido por usuario) |
| Frontend   | HTML · CSS · JavaScript           |
| Gráficos   | Plotly.js                         |
| Seguridad  | Werkzeug · python-dotenv          |

## 🚀 Instalación y uso

```bash
# 1. Clona el repositorio
git clone https://github.com/J0H4N-B/visualizador-3d-ventas.git
cd visualizador-3d-ventas

# 2. Crea y activa un entorno virtual (recomendado)
python -m venv venv
source venv/bin/activate      # Linux / Mac
venv\Scripts\activate         # Windows

# 3. Instala dependencias
pip install -r requirements.txt

# 4. Configura el entorno
cp .env.example .env
# Edita .env y cambia SECRET_KEY por una clave segura

# 5. Ejecuta el servidor
python run.py

# 6. Abre en tu navegador
# http://localhost:5000
```

## 📁 Estructura del proyecto

```
proyecto1_3d/
├── run.py                          # Punto de entrada
├── config.py                       # Configuración centralizada
├── requirements.txt
├── .env.example                    # Variables de entorno de ejemplo
├── data/
│   ├── ventas_ejemplo.csv          # Dataset de ejemplo descargable
│   └── uploads/                    # CSVs subidos (auto-creada)
├── app/
│   ├── __init__.py                 # Application Factory
│   ├── blueprints/
│   │   ├── main.py                 # Sirve el frontend
│   │   ├── upload.py               # /api/upload — carga de CSV
│   │   └── scatter.py              # /api/scatter — datos del gráfico
│   └── utils/
│       └── file_handler.py         # Validación y lectura segura de archivos
└── templates/
    └── index.html                  # Frontend SPA (3 vistas)
```

## 🔄 Flujo de uso

```
1. Subir CSV  →  2. Configurar ejes (X, Y, Z)  →  3. Explorar gráfico 3D
```

## ✨ Funcionalidades

- **Upload dinámico**: arrastra y suelta o selecciona cualquier CSV
- **Configuración de ejes**: elige qué columna numérica va en X, Y y Z
- **Agrupación por color**: cualquier columna categórica puede colorear las trazas
- **Filtros dinámicos**: se generan automáticamente según las columnas del CSV
- **KPIs en tiempo real**: suma de las métricas numéricas según filtros activos
- **Preview del CSV**: muestra las primeras 5 filas antes de graficar
- **CSV de ejemplo**: descargable desde la interfaz

## 🔒 Seguridad implementada

- Solo se aceptan archivos `.csv` (validación de extensión)
- Nombres de archivo sanitizados con `werkzeug.utils.secure_filename`
- Nombres únicos con UUID para evitar colisiones
- Límite de tamaño configurable (5 MB por defecto)
- Límite de filas al leer (10.000 máx para evitar OOM)
- Columnas validadas contra el DataFrame real (evita inyección de parámetros)
- Ruta del archivo guardada en sesión del servidor (no expuesta al cliente)
- Limpieza automática de uploads antiguos

## 🔄 Cómo escalar a producción

1. **Cambia `SECRET_KEY`** en `.env` por una clave aleatoria larga.
2. **Usa gunicorn** en lugar del servidor de desarrollo:
   ```bash
   gunicorn "run:app" --bind 0.0.0.0:8000 --workers 4
   ```
3. **Almacenamiento**: para múltiples instancias, sube los CSV a S3/GCS
   en lugar de disco local y ajusta `file_handler.py`.
4. **Base de datos de sesiones**: reemplaza las sesiones de Flask por
   Redis para soportar múltiples workers.
5. **Agrega un nuevo Blueprint**: crea `app/blueprints/mi_modulo.py`
   y regístralo en `app/__init__.py`.

## 📄 Licencia

MIT — libre para usar, modificar y distribuir.
