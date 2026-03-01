"""
Script para insertar los indicadores de los barrios en su respectiva tabla
"""
import pandas as pd
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from bd.utils import IndicadorDistrito, limpiar_valor  
from dotenv import load_dotenv, find_dotenv

load_dotenv(find_dotenv())

# Configuración de conexión
DATABASE_URL = f"postgresql+psycopg2://{os.getenv('DB_USER')}:{os.getenv('DB_PASSWORD')}@{os.getenv('DB_HOST')}:{os.getenv('DB_PORT')}/{os.getenv('DB_NAME')}"
engine = create_engine(DATABASE_URL)
Session = sessionmaker(bind=engine)
session = Session()


#Funcion principal 
def etl_indicadores(ruta_csv):
    # Cargar CSV
    df = pd.read_csv(ruta_csv, sep=';')

    # Filtros y selección de columnas solicitados
    df = df[df['año'] == 2025]
    
    columnas_interes = [
        'cod_distrito', 'distrito', 'cod_barrio', 'barrio',
        'categoría_1', 'categoría_2', 'indicador_nivel1', 'indicador_nivel2',
        'indicador_nivel3', 'unidad_indicador', 'indicador_completo', 'valor_indicador'
    ]
    
    # Aseguramos que existan las columnas antes de filtrar
    df = df[columnas_interes]

    print(f"Procesando {len(df)} registros de indicadores...")

    for _, row in df.iterrows():
        # Mapeo al objeto de la base de datos definido en schemas_bd
        nuevo_registro = IndicadorDistrito(
            cod_distrito=int(row['cod_distrito']) if pd.notna(row['cod_distrito']) else None,
            distrito=str(row['distrito']).strip(),
            cod_barrio=int(row['cod_barrio']) if pd.notna(row['cod_barrio']) else None,
            barrio=str(row['barrio']).strip() if pd.notna(row['barrio']) else None,
            categoria_1=str(row['categoría_1']).strip(),
            categoria_2=str(row['categoría_2']).strip(),
            indicador_nivel1=str(row['indicador_nivel1']).strip(),
            indicador_nivel2=str(row['indicador_nivel2']).strip(),
            indicador_nivel3=str(row['indicador_nivel3']).strip(),
            unidad_indicador=str(row['unidad_indicador']).strip(),
            indicador_completo=str(row['indicador_completo']).strip(),
            valor_indicador=limpiar_valor(row['valor_indicador'])
        )

        session.add(nuevo_registro) 

    try:
        session.commit()
        print("Importación exitosa")
    except Exception as e:
        session.rollback()
        print(f"Error en la inserción: {e}")
    finally:
        session.close()

if __name__ == "__main__":
    ruta = r"datos_abiertos_madrid/indicadores_distritos_madrid.csv"
    etl_indicadores(ruta)