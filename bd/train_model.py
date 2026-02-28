import pandas as pd
import pickle
from sqlalchemy import create_engine
from sklearn.linear_model import LinearRegression
from sklearn.metrics import root_mean_squared_error
from sklearn.preprocessing import OneHotEncoder
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from dotenv import load_dotenv, find_dotenv
import os 

load_dotenv(find_dotenv())
# Configuración y Conexión
DATABASE_URL = f"postgresql+psycopg2://{os.getenv('DB_USER')}:{os.getenv('DB_PASSWORD')}@{os.getenv('DB_HOST')}:{os.getenv('DB_PORT')}/{os.getenv('DB_NAME')}"
engine = create_engine(DATABASE_URL)

def train_and_export():
    # 1. Carga desde bd
    df = pd.read_sql("SELECT * FROM public.inmuebles", con=engine)

    # 2. Preprocesamiento de variables categóricas
    # 'estado' suele tener nulos, los marcamos como 'unknown'
    df['tipo_propiedad'] = df['tipo_propiedad'].map({
        'flat': 'Piso', 'penthouse': 'Ático', 'chalet': 'Chalet', 
        'duplex': 'Dúplex', 'studio': 'Estudio', 'countryHouse': 'Casa Rústica'
    })  
    df['estado'] = df['estado'].map({'good': 'En buen estado', 'renew': 'Necesita refoma', 'newdevelopment': 'Obra nueva'})
    df['estado'] = df['estado'].fillna('unknown')
    
    # 3. Definición de Features
    # Variables numéricas y categóricas
    features = ['tamaño_m2', 'n_habitaciones', 'n_baños', 'barrio', 'estado', 'tipo_propiedad']
    X = df[features]
    y = df['precio']

    # 4. Pipeline con OneHotEncoder para las 3 columnas de texto
    preprocessor = ColumnTransformer(transformers=[
        ('cat', OneHotEncoder(handle_unknown='ignore'), ['barrio', 'estado', 'tipo_propiedad'])
    ], remainder='passthrough')

    model_pipeline = Pipeline(steps=[
        ('preprocessor', preprocessor),
        ('regressor', LinearRegression())
    ])

    # 5. Entrenamiento
    model_pipeline.fit(X, y)

    # 6. Cálculo de RMSE para el intervalo
    preds = model_pipeline.predict(X)
    rmse = root_mean_squared_error(y, preds)

    # 7. Guardar en PKL
    model_data = {
        "model": model_pipeline,
        "rmse": rmse,
        "features": features,
        # Guardamos los valores únicos para los selects de la App
        "unique_values": {
            "barrios": sorted(df['barrio'].unique().tolist()),
            "estados": sorted(df['estado'].unique().tolist()),
            "tipos": sorted(df['tipo_propiedad'].unique().tolist())
        }
    }
    
    with open("modelo_tasacion_inmobiliario.pkl", "wb") as f:
        pickle.dump(model_data, f)
        
    print("✅ Modelo .pkl generado con éxito")

if __name__ == "__main__":
    train_and_export()