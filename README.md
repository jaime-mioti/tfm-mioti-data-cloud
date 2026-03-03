## 🛠️ Configuración en Windows (PowerShell) para reproducir el proyecto completo

- Requiere **API_KEY** y **SECRET** de idealista en un archivo .env
- Requiere tener instalado Docker.
- Ha sido probado en python 3.11.3 

### 1. Instalación de uv
```
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
```
### 2. Crear entorno virtual (solo una vez)
```
uv venv
```
### 3. Instalación de librerías necesarias
```
uv pip install -r requirements.txt
```
### 4. Para ejecutar scripts
```
uv run main.py
```
### 5. Nota: Si instalas una libreria nueva -> actualiza el requirements.txt
```
uv pip freeze > requirements.txt
```
### Proceso obtener info idealista
```
script get_token.ps1 (en terminal: ./get_token.ps1) (para obtener el token de acceso)
```

```
uv run distritos_madrid_idealista.py (para obtener los json de idealista)
```
### 6. Desplegar contenedores
```
docker-compose up -d --build
```
### 7. Ejecutar ddl

(esto seria en un script sql, ejecutar full_ddl.sql)
### 8. ETLs inserción
```
uv run bd/etl_barrios_shp.py
uv run bd/etl_indicadores.py
uv run bd/etl_json_postgre.py (asegurar tener archivos de idealista en carpeta raw_data (no subida al repo por seguridad))
uv run bd/etl_poblacion_barrios.py
```
### 9. Entrenar modelo
```
uv run bd/train_model.py (ver si ha generado un .pkl)
```
### 10. Entrar al puerto de streamlit y ver aplicacion
```
localhost:8501 (ver credenciales en docker-compose.yml)
```
