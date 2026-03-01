"""
Script para insertar los json de los distritos en la bd
"""

import json
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from geoalchemy2.shape import from_shape
from shapely.geometry import Point
from bd.utils import Inmueble, RawData, IdealistaReference, InmuebleNLP
from dotenv import load_dotenv, find_dotenv
import os 

load_dotenv(find_dotenv())
# Configuración de conexión
DATABASE_URL = f"postgresql+psycopg2://{os.getenv('DB_USER')}:{os.getenv('DB_PASSWORD')}@{os.getenv('DB_HOST')}:{os.getenv('DB_PORT')}/{os.getenv('DB_NAME')}"
engine = create_engine(DATABASE_URL)
Session = sessionmaker(bind=engine)
session = Session()

# Función de Procesamiento
def importar_json(ruta_archivo):
    with open(ruta_archivo, 'r', encoding='utf-8') as f:
        datos = json.load(f)

    for item in datos:
        prop_id = str(item.get('propertyCode'))
        lat = item.get('latitude')
        lon = item.get('longitude')

        # Crear objeto principal Inmueble
        nuevo_inmueble = Inmueble(
            id=prop_id,
            precio=item.get('price'),
            geom=from_shape(Point(lon, lat), srid=4326) if lat and lon else None,
            numfotos=item.get('numPhotos'),
            planta=int(item.get('floor', 0)) if item.get('floor') and item.get('floor').isdigit() else None,
            precioinfo=item.get('priceInfo'),
            tipo_propiedad=item.get('propertyType'),
            tamaño_m2=item.get('size'),
            es_exterior=item.get('exterior'),
            n_habitaciones=item.get('rooms'),
            n_baños=item.get('bathrooms'),
            direccion=item.get('address'),
            provincia=item.get('province'),
            municipio=item.get('municipality'),
            distrito=item.get('district'),
            pais=item.get('country'),
            barrio=item.get('neighborhood'),
            estado=item.get('status'),
            tiene_ascensor=item.get('hasLift'),
            parking=item.get('parkingSpace'),
            precio_m2=item.get('priceByArea'),
            tipo_detalle=item.get('detailedType'),
            texto_sugerido=item.get('suggestedText')
        )

        # Crear objetos para tablas relacionadas
        raw = RawData(id=prop_id, raw_data=item)
        ref = IdealistaReference(id=prop_id, url=f"https://www.idealista.com/inmueble/{prop_id}/")
        nlp = InmuebleNLP(id=prop_id, description=item.get('description'))

        # Insertar en orden por las foreign key declaradas
        session.merge(nuevo_inmueble)
        session.merge(raw)
        session.merge(ref)
        session.merge(nlp)

    try:
        session.commit()
        print(f"Éxito: Se han procesado e importado {len(datos)} registros en las 4 tablas.")
    except Exception as e:
        session.rollback()
        print(f"Error: {e}")
    finally:
        session.close()

#Funcion para cargar todo iterando por archivo en la carpeta con los json
def cargar_idealista_postgre(carpeta):
    for file in os.listdir(carpeta):
        importar_json(f"{carpeta}/{file}")  


if __name__ == "__main__":
    cargar_idealista_postgre('raw_data')