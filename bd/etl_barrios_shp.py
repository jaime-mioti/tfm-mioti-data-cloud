"""
Script para insertar el shapefile con las geometrías de los barrios de Madrid
"""
import os
import geopandas as gpd
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv, find_dotenv

# Configuración de conexión 
load_dotenv(find_dotenv())
DATABASE_URL = f"postgresql+psycopg2://{os.getenv('DB_USER')}:{os.getenv('DB_PASSWORD')}@{os.getenv('DB_HOST')}:{os.getenv('DB_PORT')}/{os.getenv('DB_NAME')}"
engine = create_engine(DATABASE_URL)

# Función para insertar el archivo shapefile en postgres
def importar_shapefile(ruta_shp):
    print(f"Leyendo archivo: {ruta_shp}...")
    
    # Leer el shapefile con GeoPanda, nos quedamos con las co,lumnas que nos interesan y renombramos
    gdf = gpd.read_file(ruta_shp) 
    gdf = gdf[['CODDIS', 'NOMDIS', 'COD_BAR', 'NOMBRE', 'AREA', 'geometry']]
    gdf.rename(columns={'CODDIS': 'cod_distrito', 'NOMDIS': 'distrito', 'COD_BAR': 'cod_barrio', 'NOMBRE': 'barrio', 'AREA': 'area'}, inplace=True)
    # Estandarizar coordenadas a WGS84 (EPSG:4326) para que coincida con el sistema usado con los inmuebles 
    print(f"Proyección original: {gdf.crs}")
    gdf = gdf.to_crs(epsg=4326)
    print(f"Proyección una vez cambiada: {gdf.crs}")
    # Insertar en la base de datos
    nombre_tabla = "barrios_geo"
    print(f"Insertando datos en la tabla '{nombre_tabla}'...")
    try:
        gdf.to_postgis(
            name=nombre_tabla, 
            con=engine, 
            if_exists='replace', 
            index=False 
        )
        print("Importación exitosa")
    except Exception as e:
        print(f"Error al insertar: {e}")

if __name__ == "__main__":
    importar_shapefile("barrios/BARRIOS.shp")