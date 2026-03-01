"""
Script para insertar la población de los barrios en su respectiva tabla
"""
import pandas as pd
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from bd.utils import PoblacionBarrios, limpiar_entero  
from dotenv import load_dotenv, find_dotenv

load_dotenv(find_dotenv())

# Configuración de conexión
DATABASE_URL = f"postgresql+psycopg2://{os.getenv('DB_USER')}:{os.getenv('DB_PASSWORD')}@{os.getenv('DB_HOST')}:{os.getenv('DB_PORT')}/{os.getenv('DB_NAME')}"
engine = create_engine(DATABASE_URL)
Session = sessionmaker(bind=engine)
session = Session()

#Función principal para cargar el csv de poblacion en bd
def etl_poblacion(ruta_csv):
    # Cargar CSV
    df = pd.read_csv(ruta_csv, sep=';', encoding='utf-8')

    # Filtros en el df
    df = df[df['fecha'] == '1 de enero de 2024']
    df = df[df['distrito'].str.strip() != df['barrio'].str.strip()]

    print(f"Procesando {len(df)} barrios...")

    for _, row in df.iterrows():
        # Conversión de tipos y limpieza de datos
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
        print("Importación exitosa")
    except Exception as e:
        session.rollback()
        print(f"Error en la inserción: {e}")
    finally:
        session.close()

if __name__ == "__main__":
    etl_poblacion(r'datos_abiertos_madrid/poblacion_distrito_barrio_madrid.csv')