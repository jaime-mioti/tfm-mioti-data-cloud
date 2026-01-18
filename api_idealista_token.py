import os
import urllib.parse
import base64
import requests
from dotenv import load_dotenv

load_dotenv()

def get_idealista_token():
    # 1. Cargar y LIMPIAR variables (strip elimina espacios/enters invisibles)
    raw_key = os.getenv('API_KEY')
    raw_secret = os.getenv('SECRET')

    if not raw_key or not raw_secret:
        print("❌ Error: Faltan las credenciales en el .env")
        return None

    # Limpiamos espacios en blanco que suelen causar errores
    api_key = raw_key.strip()
    secret = raw_secret.strip()

    # 2. Generar Base64 (Tal como lo hace Thunder Client)
    # NOTA: Thunder Client a veces NO hace URL Encode si las claves son simples.
    # Vamos a probar concatenación directa primero, que es lo más común si no tienes símbolos raros.
    credentials = f"{api_key}:{secret}"
    encoded_credentials = base64.b64encode(credentials.encode()).decode()

    # --- ZONA DE DIAGNÓSTICO ---
    print("\n--- DIAGNÓSTICO ---")
    print(f"1. API Key cargada (longitud): {len(api_key)} caracteres")
    print(f"2. Secret cargado (longitud): {len(secret)} caracteres")
    print(f"3. Tu Base64 generado: {encoded_credentials[:10]}...{encoded_credentials[-10:]}")
    # Compara visualmente si este Base64 se parece al que viste en Thunder Client
    print("-------------------\n")

    # 3. Configuración IDÉNTICA al código que te funcionó
    reqUrl = "https://api.idealista.com/oauth/token"

    headersList = {
        "Accept": "*/*",
        "User-Agent": "Thunder Client (https://www.thunderclient.com)",
        "Authorization": f"Basic {encoded_credentials}",
        "Content-Type": "application/x-www-form-urlencoded" 
    }

    # Usamos string payload, no diccionario, para ser exactos al código que funcionó
    payload = "grant_type=client_credentials&scope=read"

    print("📡 Enviando petición...")
    
    try:
        response = requests.request("POST", reqUrl, data=payload, headers=headersList)
        
        if response.status_code == 200:
            token_data = response.json()
            return token_data["access_token"]
        else:
            print(f"⚠️ Error {response.status_code}: {response.text}")
            print("Cabeceras enviadas:", headersList)
            return None
            
    except Exception as e:
        print(f"❌ Error crítico: {e}")
        return None

if __name__ == "__main__":
    token = get_idealista_token()
    if token:
        print(f"\n✅ ¡ÉXITO TOTAL! Token: {token[:15]}...")
    else:
        print("\n❌ Falló. Mira los datos de diagnóstico arriba.")