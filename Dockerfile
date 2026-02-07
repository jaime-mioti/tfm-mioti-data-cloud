# Usamos una imagen ligera de Python
FROM    Python 3.11.3 
# Directorio de trabajo dentro del contenedor
WORKDIR /app
#Copiamos los requisitos e instalamos
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

#Copiamos el resto del código
#COPY . .

#Comando para ejecutar la app
#CMD ["python", "main.py"]