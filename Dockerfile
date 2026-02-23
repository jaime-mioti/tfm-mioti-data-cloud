# 1. Usamos una versión ligera y estable
FROM python:3.11-slim

# 2. Instalamos dependencias del sistema para PostgreSQL y compilación
RUN apt-get update && apt-get install -y \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# 3. Directorio de trabajo
WORKDIR /app

# 4. Instalamos las librerías de Python
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 5. Copiamos el código (Descomenta esto para que Docker vea tu app.py)
COPY . .

# 6. Exponemos el puerto de Streamlit
EXPOSE 8501

# 7. Comando específico para Streamlit
CMD ["streamlit", "run", "app.py", "--server.port=8501", "--server.address=0.0.0.0"]