from sqlalchemy import Column, Integer, String, Float, Boolean, Text, ForeignKey, Numeric
from sqlalchemy.dialects.postgresql import JSONB
from geoalchemy2 import Geometry
from sqlalchemy.orm import declarative_base
Base = declarative_base()

class Inmueble(Base):
    __tablename__ = 'inmuebles'
    __table_args__ = {'schema': 'public'}

    id = Column(String(50), primary_key=True)
    precio = Column(Float)
    geom = Column(Geometry(geometry_type='POINT', srid=4326))
    numfotos = Column(Integer)
    planta = Column(Integer)
    precioinfo = Column(JSONB)
    tipo_propiedad = Column(String(50))
    tamaño_m2 = Column(Float)
    es_exterior = Column(Boolean)
    n_habitaciones = Column(Integer)
    n_baños = Column(Integer)
    direccion = Column(String(100))
    provincia = Column(String(50))
    municipio = Column(String(50))
    distrito = Column(String(50))
    pais = Column(String(20))
    barrio = Column(String(50))
    estado = Column(String(20))
    tiene_ascensor = Column(Boolean)
    parking = Column(JSONB)
    precio_m2 = Column(Float)
    tipo_detalle = Column(JSONB)
    texto_sugerido = Column(JSONB)

class RawData(Base):
    __tablename__ = 'raw_data'
    __table_args__ = {'schema': 'public'}
    id = Column(String(50), ForeignKey('public.inmuebles.id', ondelete='CASCADE'), primary_key=True)
    raw_data = Column(JSONB)

class IdealistaReference(Base):
    __tablename__ = 'idealista_reference'
    __table_args__ = {'schema': 'public'}
    id = Column(String(50), ForeignKey('public.inmuebles.id', ondelete='CASCADE'), primary_key=True)
    url = Column(String(200))

class InmuebleNLP(Base):
    __tablename__ = 'inmuebles_nlp'
    __table_args__ = {'schema': 'public'}
    id = Column(String(50), ForeignKey('public.inmuebles.id', ondelete='CASCADE'), primary_key=True)
    description = Column(Text)
    
    
class PoblacionBarrios(Base):
    __tablename__ = 'poblacion_barrios'
    cod_barrio = Column(Integer, primary_key=True) 
    barrio = Column(String)
    distrito = Column(String)
    cod_distrito = Column(Integer, primary_key=True)
    num_personas = Column(Integer)
    num_personas_hombres = Column(Integer)
    num_personas_mujeres = Column(Integer)
    
class IndicadorDistrito(Base):
    __tablename__ = 'indicadores_madrid'

    id = Column(Integer, primary_key=True, autoincrement=True)
    cod_distrito = Column(Integer)
    distrito = Column(String(100))
    cod_barrio = Column(Integer)
    barrio = Column(String(100))
    categoria_1 = Column(String(255))
    categoria_2 = Column(String(255))
    indicador_nivel1 = Column(String(255))
    indicador_nivel2 = Column(String(255))
    indicador_nivel3 = Column(String(255))
    unidad_indicador = Column(String(100))
    indicador_completo = Column(Text)
    valor_indicador = Column(Numeric)