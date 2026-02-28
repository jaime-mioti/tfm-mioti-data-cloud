import pandas as pd
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from schemas_bd import PoblacionBarrios  # Ajusta al nombre de tu clase
from dotenv import load_dotenv, find_dotenv

load_dotenv(find_dotenv())

# Configuración de conexión
DATABASE_URL = f"postgresql+psycopg2://{os.getenv('DB_USER')}:{os.getenv('DB_PASSWORD')}@{os.getenv('DB_HOST')}:{os.getenv('DB_PORT')}/{os.getenv('DB_NAME')}"
engine = create_engine(DATABASE_URL)
Session = sessionmaker(bind=engine)
session = Session()

def limpiar_entero(valor):
    """Convierte strings con puntos de miles a enteros puros"""
    if pd.isna(valor) or valor == '':
        return 0
    if isinstance(valor, str):
        # Quitamos el punto de miles (ej: 145.411 -> 145411)
        valor = valor.replace('.', '').strip()
    try:
        return int(valor)
    except ValueError:
        return 0

def etl_poblacion(ruta_csv):
    # 1. Cargar CSV
    df = pd.read_csv(ruta_csv, sep=';', encoding='utf-8')

    # 2. Filtros solicitados
    # Solo fecha actual y quitar filas donde distrito == barrio (totales de distrito)
    df = df[df['fecha'] == '1 de enero de 2024']
    df = df[df['distrito'].str.strip() != df['barrio'].str.strip()]

    print(f"Procesando {len(df)} barrios...")

    for _, row in df.iterrows():
        # 3. Conversión de tipos y limpieza de datos
        nuevo_registro = PoblacionBarrios(
            cod_barrio=int(row['cod_barrio']),
            barrio=str(row['barrio']).strip(),
            distrito=str(row['distrito']).strip(),
            cod_distrito=int(row['cod_distrito']),
            num_personas=limpiar_entero(row['num_personas']),
            num_personas_hombres=limpiar_entero(row['num_personas_hombres']),
            num_personas_mujeres=limpiar_entero(row['num_personas_mujeres'])
        )

        session.merge(nuevo_registro)

    try:
        session.commit()
        print("¡ETL finalizada con éxito!")
    except Exception as e:
        session.rollback()
        print(f"Error en la inserción: {e}")
    finally:
        session.close()

if __name__ == "__main__":
    etl_poblacion(r'datos_abiertos_madrid/poblacion_distrito_barrio_madrid.csv')