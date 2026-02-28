import pandas as pd
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from schemas_bd import IndicadorDistrito  # Nombre de la nueva clase
from dotenv import load_dotenv, find_dotenv

load_dotenv(find_dotenv())

# Configuración de conexión
DATABASE_URL = f"postgresql+psycopg2://{os.getenv('DB_USER')}:{os.getenv('DB_PASSWORD')}@{os.getenv('DB_HOST')}:{os.getenv('DB_PORT')}/{os.getenv('DB_NAME')}"
engine = create_engine(DATABASE_URL)
Session = sessionmaker(bind=engine)
session = Session()

def limpiar_valor(valor):
    """Convierte el valor del indicador a float, manejando posibles formatos europeos"""
    if pd.isna(valor) or valor == '':
        return 0.0
    if isinstance(valor, str):
        # Si viene con coma decimal, la cambiamos por punto
        valor = valor.replace('.', '').replace(',', '.')
    try:
        return float(valor)
    except ValueError:
        return 0.0

def etl_indicadores(ruta_csv):
    # 1. Cargar CSV
    # Nota: He añadido encoding latin1 por si el utf-8 da error con eñes/acentos de Madrid
    df = pd.read_csv(ruta_csv, sep=';')

    # 2. Filtros y selección de columnas solicitados
    df = df[df['año'] == 2025]
    
    columnas_interes = [
        'cod_distrito', 'distrito', 'cod_barrio', 'barrio',
        'categoría_1', 'categoría_2', 'indicador_nivel1', 'indicador_nivel2',
        'indicador_nivel3', 'unidad_indicador', 'indicador_completo', 'valor_indicador'
    ]
    
    # Aseguramos que existan las columnas antes de filtrar
    df = df[columnas_interes]

    print(f"Procesando {len(df)} registros de indicadores para el año 2025...")

    for _, row in df.iterrows():
        # 3. Mapeo al objeto de la base de datos
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

        session.add(nuevo_registro) # Usamos add porque no hay una PK natural única en el CSV

    try:
        session.commit()
        print("¡ETL de Indicadores finalizada con éxito!")
    except Exception as e:
        session.rollback()
        print(f"Error en la inserción: {e}")
    finally:
        session.close()

if __name__ == "__main__":
    ruta = r"datos_abiertos_madrid/indicadores_distritos_madrid.csv"
    etl_indicadores(ruta)