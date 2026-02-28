-- Extensión necesaria para el campo GEOMETRY
CREATE EXTENSION IF NOT EXISTS postgis;

-- 1. TABLA PRINCIPAL
CREATE TABLE public.inmuebles (
    id VARCHAR(50) PRIMARY KEY,      -- Identificador único (propertyCode de Idealista)
    precio FLOAT,                    -- Precio de venta actual
    geom GEOMETRY(Point, 4326),      -- Ubicación geográfica (Longitud, Latitud) SRID 4326
    numfotos INT,                    -- Cantidad de imágenes en el anuncio
    planta INT,                      -- Planta en la que está el inmueble
    precioInfo JSONB,                -- Histórico de variaciones y detalles de precio
    tipo_propiedad VARCHAR(50),      -- Categoría (piso, chalet, estudio, etc.)
    tamaño_m2 FLOAT,                 -- Superficie útil/construida
    es_exterior BOOL,                -- Indicador de vistas a la calle
    n_habitaciones INT,              -- Número de dormitorios
    n_baños INT,                     -- Número de baños
    direccion VARCHAR(100),          -- Dirección 
    provincia VARCHAR(50),           -- Provincia 
    municipio VARCHAR(50),           -- Municipio 
    distrito VARCHAR(50),            -- Distrito 
    pais VARCHAR(20),                -- País
    barrio VARCHAR(50),              -- Barrio 
    estado VARCHAR(20),              -- Estado del inmueble (buen estado, a reformar, etc.)
    tiene_ascensor BOOL,             -- Indicador de ascensor
    parking JSONB,                   -- Detalles sobre plaza de garaje
    precio_m2 FLOAT,                 -- precio/superficie
    tipo_detalle JSONB,              -- Clasificación detallada del inmueble
    texto_sugerido JSONB,            -- Títulos dinámicos de Idealista
    codigo_distrito INT              -- Código del distrito
);

-- 2. TABLA RAW_DATA
CREATE TABLE public.raw_data (
    id VARCHAR(50) PRIMARY KEY,
    raw_data JSONB,                  -- Almacenamiento íntegro del objeto JSON original
    CONSTRAINT fk_raw_inmuebles FOREIGN KEY (id) 
        REFERENCES public.inmuebles(id) ON DELETE CASCADE
);

-- 3. TABLA REFERENCIAS
CREATE TABLE public.idealista_reference (
    id VARCHAR(50) PRIMARY KEY,
    url VARCHAR(200),                -- URL directa al anuncio original
    CONSTRAINT fk_ref_inmuebles FOREIGN KEY (id) 
        REFERENCES public.inmuebles(id) ON DELETE CASCADE
);

-- 4. TABLA NLP: Procesamiento de Lenguaje Natural
CREATE TABLE public.inmuebles_nlp (
    id VARCHAR(50) PRIMARY KEY,
    description TEXT,                -- Descripción completa para futuros análisis de texto
    CONSTRAINT fk_nlp_inmuebles FOREIGN KEY (id) 
        REFERENCES public.inmuebles(id) ON DELETE CASCADE
);

COMMENT ON TABLE public.inmuebles IS 'Tabla maestra con atributos físicos y técnicos de los inmuebles.';
COMMENT ON COLUMN public.inmuebles.id IS 'Identificador único del anuncio (propertyCode).';
COMMENT ON COLUMN public.inmuebles.precio IS 'Precio total de venta en euros.';
COMMENT ON COLUMN public.inmuebles.geom IS 'Punto geométrico (Longitud/Latitud) usando SRID 4326.';
COMMENT ON COLUMN public.inmuebles.numfotos IS 'Número de fotografías publicadas en el anuncio.';
COMMENT ON COLUMN public.inmuebles.planta IS 'Altura del piso (0 para bajo, valores negativos para sótanos).';
COMMENT ON COLUMN public.inmuebles.precioInfo IS 'Detalles del precio, incluyendo moneda y posibles rebajas.';
COMMENT ON COLUMN public.inmuebles.tipo_propiedad IS 'Tipo de inmueble (flat, chalet, penthouse, etc.).';
COMMENT ON COLUMN public.inmuebles.tamaño_m2 IS 'Superficie construida en metros cuadrados.';
COMMENT ON COLUMN public.inmuebles.es_exterior IS 'Indica si el inmueble tiene orientación a la calle.';
COMMENT ON COLUMN public.inmuebles.n_habitaciones IS 'Cantidad de dormitorios disponibles.';
COMMENT ON COLUMN public.inmuebles.n_baños IS 'Cantidad de cuartos de baño.';
COMMENT ON COLUMN public.inmuebles.direccion IS 'Dirección textual o zona del inmueble.';
COMMENT ON COLUMN public.inmuebles.provincia IS 'Nombre de la provincia.';
COMMENT ON COLUMN public.inmuebles.municipio IS 'Nombre del municipio o ciudad.';
COMMENT ON COLUMN public.inmuebles.distrito IS 'Nombre del distrito municipal.';
COMMENT ON COLUMN public.inmuebles.pais IS 'Código internacional del país.';
COMMENT ON COLUMN public.inmuebles.barrio IS 'Nombre del barrio específico.';
COMMENT ON COLUMN public.inmuebles.estado IS 'Estado de conservación (good, renew, etc.).';
COMMENT ON COLUMN public.inmuebles.tiene_ascensor IS 'Boolean que indica si el edificio cuenta con ascensor.';
COMMENT ON COLUMN public.inmuebles.parking IS 'Información sobre plaza de garaje incluida o adicional.';
COMMENT ON COLUMN public.inmuebles.precio_m2 IS 'Valor calculado del precio dividido por la superficie.';
COMMENT ON COLUMN public.inmuebles.tipo_detalle IS 'JSON con subclases de tipología de vivienda.';
COMMENT ON COLUMN public.inmuebles.texto_sugerido IS 'Título y etiquetas generadas por el portal.';
COMMENT ON COLUMN public.inmuebles.codigo_distrito IS 'Identificador numérico del distrito administrativo.';

COMMENT ON TABLE public.raw_data IS 'Copia de seguridad del JSON original para trazabilidad completa.';
COMMENT ON COLUMN public.raw_data.id IS 'Relación con la tabla inmuebles.';
COMMENT ON COLUMN public.raw_data.raw_data IS 'JSON íntegro sin procesar tal como viene de la fuente.';

COMMENT ON TABLE public.idealista_reference IS 'Enlaces de referencia al portal externo.';
COMMENT ON COLUMN public.idealista_reference.id IS 'Relación con la tabla inmuebles.';
COMMENT ON COLUMN public.idealista_reference.url IS 'Dirección URL web del anuncio original.';

COMMENT ON TABLE public.inmuebles_nlp IS 'Datos para procesamiento de lenguaje natural y minería de texto.';
COMMENT ON COLUMN public.inmuebles_nlp.id IS 'Relación con la tabla inmuebles.';
COMMENT ON COLUMN public.inmuebles_nlp.description IS 'Descripción extensa del inmueble redactada por el anunciante.';

--poblacion_barrios
CREATE TABLE public.poblacion_barrios (
    cod_barrio INTEGER,
    barrio VARCHAR(255),
    distrito VARCHAR(255),
    cod_distrito INTEGER,
    num_personas INTEGER,
    num_personas_hombres INTEGER,
    num_personas_mujeres INTEGER,
    PRIMARY KEY (cod_distrito, cod_barrio) 
);

--indicadores distritos hay que usar un id como primary_key para evitarnos problemas al insertar
CREATE TABLE public.indicadores_madrid (
	id SERIAL PRIMARY KEY,
    cod_distrito INTEGER,
    distrito VARCHAR(100),
    cod_barrio INTEGER,
    barrio VARCHAR(100),
    categoria_1 VARCHAR(255),
    categoria_2 VARCHAR(255),
    indicador_nivel1 VARCHAR(255),
    indicador_nivel2 VARCHAR(255),
    indicador_nivel3 VARCHAR(255),
    unidad_indicador VARCHAR(100),
    indicador_completo TEXT,
    valor_indicador NUMERIC
);