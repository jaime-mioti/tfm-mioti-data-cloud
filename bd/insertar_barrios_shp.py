import os
import geopandas as gpd
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv, find_dotenv

# 1. Cargar configuración 
load_dotenv(find_dotenv())

DATABASE_URL = f"postgresql+psycopg2://{os.getenv('DB_USER')}:{os.getenv('DB_PASSWORD')}@{os.getenv('DB_HOST')}:{os.getenv('DB_PORT')}/{os.getenv('DB_NAME')}"
engine = create_engine(DATABASE_URL)

def importar_shapefile(ruta_shp):
    print(f"Leyendo archivo: {ruta_shp}...")
    
    # 2. Leer el shapefile con GeoPandas
    gdf = gpd.read_file(ruta_shp)
    gdf = gdf[['CODDIS', 'NOMDIS', 'COD_BAR', 'NOMBRE', 'AREA', 'geometry']]
    gdf.rename(columns={'CODDIS': 'cod_distrito', 'NOMDIS': 'distrito', 'COD_BAR': 'cod_barrio', 'NOMBRE': 'barrio', 'AREA': 'area'}, inplace=True)
    # 3. Estandarizar coordenadas a WGS84 (EPSG:4326) 
    
    if gdf.crs is None:
        print("Aviso: El archivo no tiene sistema de coordenadas definido. Asumiendo 4326...")
        gdf.set_crs(epsg=4326, inplace=True)
    else:
        print(f"Proyección original: {gdf.crs}")
        gdf = gdf.to_crs(epsg=4326)

    # 4. Insertar en la base de datos
    nombre_tabla = "barrios_geo"
    
    print(f"Insertando datos en la tabla '{nombre_tabla}'...")
    try:
        gdf.to_postgis(
            name=nombre_tabla, 
            con=engine, 
            if_exists='replace', 
            index=False 
        )
        print("¡Importación exitosa!")
    except Exception as e:
        print(f"Error al insertar: {e}")

if __name__ == "__main__":
    importar_shapefile("barrios/BARRIOS.shp")