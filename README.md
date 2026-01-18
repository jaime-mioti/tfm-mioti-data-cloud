## 🛠️ Configuración en Windows (PowerShell)

Este proyecto usa **uv** para la gestión rápida de dependencias.

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
