"""
Script para realizar las llamadas a la API de idealista, requiere un access_token valido
"""
import subprocess
import json
import os
import time
from dotenv import load_dotenv

load_dotenv()

# --- CONFIGURACIÓN MANUAL ---
# Cambia este nombre por el distrito que quieras descargar (ej: "21_Barajas")
DISTRICT_TO_FETCH = "10_Latina" 
# ----------------------------

# Lista de los 21 Distritos con el formato que pide Idealista
DISTRITOS = {
    "01_Centro": "0-EU-ES-28-07-001-079-01",
    "02_Arganzuela": "0-EU-ES-28-07-001-079-02",
    "03_Retiro": "0-EU-ES-28-07-001-079-03",
    "04_Salamanca": "0-EU-ES-28-07-001-079-04",
    "05_Chamartin": "0-EU-ES-28-07-001-079-05",
    "06_Tetuan": "0-EU-ES-28-07-001-079-06",
    "07_Chamberi": "0-EU-ES-28-07-001-079-07",
    "08_Fuencarral_El_Pardo": "0-EU-ES-28-07-001-079-08",
    "09_Moncloa_Aravaca": "0-EU-ES-28-07-001-079-09",
    "10_Latina": "0-EU-ES-28-07-001-079-10",
    "11_Carabanchel": "0-EU-ES-28-07-001-079-11",
    "12_Usera": "0-EU-ES-28-07-001-079-12",
    "13_Puente_de_Vallecas": "0-EU-ES-28-07-001-079-13",
    "14_Moratalaz": "0-EU-ES-28-07-001-079-14",
    "15_Ciudad_Lineal": "0-EU-ES-28-07-001-079-15",
    "16_Hortaleza": "0-EU-ES-28-07-001-079-16",
    "17_Villaverde": "0-EU-ES-28-07-001-079-17",
    "18_Villa_de_Vallecas": "0-EU-ES-28-07-001-079-18",
    "19_Vicalvaro": "0-EU-ES-28-07-001-079-19",
    "20_San_Blas_Canillejas": "0-EU-ES-28-07-001-079-20",
    "21_Barajas": "0-EU-ES-28-07-001-079-21"
}

# Funcion que por debajo utiliza powershell para hacer la llamada a la api sobre la informacion que queremos
def llamar_api(location_id, page=1):
    token = os.getenv("ACCESS_TOKEN")
    temp_file = "temp_call.json"
    
    # Hemos añadido -UseBasicParsing para evitar el pop-up de seguridad de PowerShell
    ps_command = f"""
    $Headers = @{{
        "Authorization" = "Bearer {token}"
        "User-Agent"    = "Thunder Client (https://www.thunderclient.com)"
    }}
    $Body = "country=es&operation=sale&propertyType=homes&locationId={location_id}&maxItems=50&numPage={page}"
    
    try {{
        $res = Invoke-WebRequest -Method Post -Uri "https://api.idealista.com/3.5/es/search" `
               -Headers $Headers -Body $Body -ContentType "application/x-www-form-urlencoded" -UseBasicParsing
        
        $res.Content | Out-File -FilePath "{temp_file}" -Encoding utf8
        
        $restantes = $res.Headers["X-Usage-Daily-Remaining"]
        Write-Output "RESTANTES:$restantes"
    }} catch {{
        Write-Error $_.Exception.Message
    }}
    """

    try:
        process = subprocess.run(["powershell", "-Command", ps_command], capture_output=True, text=True)
        
        cuota = "Desconocida"
        for line in process.stdout.splitlines():
            if "RESTANTES:" in line:
                cuota = line.split("RESTANTES:")[1].strip()

        if os.path.exists(temp_file):
            with open(temp_file, "r", encoding="utf-8-sig") as f:
                data = json.load(f)
            os.remove(temp_file)
            return data, cuota
        else:
            print(f"   ❌ Error 404 o similar: {process.stderr}")
    except Exception as e:
        print(f"   ❌ Error ejecución: {e}")
    return None, "0"

# Funcion principal para obtener todos los anuncios de un distrito concreto
def descargar_un_distrito(nombre):
    if nombre not in DISTRITOS:
        print(f"❌ '{nombre}' no está en la lista.")
        return

    loc_id = DISTRITOS[nombre]
    todos_los_pisos = []
    pagina_actual = 1
    total_paginas = 1 

    print(f"🚀 Iniciando descarga de: {nombre}")
    print(f"📍 ID: {loc_id}")

    while pagina_actual <= total_paginas:
        res, cuota = llamar_api(loc_id, pagina_actual)
        
        if res and 'elementList' in res:
            pueblo_actual = res['elementList']
            todos_los_pisos.extend(pueblo_actual)
            
            total_paginas = res.get('totalPages', 1)
            total_items = res.get('total', 0)
            
            print(f"   ✅ Pág {pagina_actual}/{total_paginas} | Acumulado: {len(todos_los_pisos)}/{total_items} | 🎫 Quedan: {cuota}")
            
            pagina_actual += 1
            time.sleep(5) 
        else:
            print(f"   ⚠️ Se cortó la descarga. Guardando lo obtenido...")
            break

    if todos_los_pisos:
        filename = f"madrid_{nombre}.json"
        with open(filename, "w", encoding="utf-8") as f:
            json.dump(todos_los_pisos, f, indent=4, ensure_ascii=False)
        print(f"\n💾 ÉXITO: Generado '{filename}' con {len(todos_los_pisos)} anuncios.")
    else:
        print("\n💀 No se pudo obtener ningún dato.")

# Hubo algun proceso que se paro a la mitad, de ahi esta funcion para hacer descarga parcial
def descargar_desde_pagina(nombre, pagina_inicio):
    if nombre not in DISTRITOS: return

    loc_id = DISTRITOS[nombre]
    todos_los_pisos = []
    pagina_actual = pagina_inicio 
    total_paginas = 46 

    print(f"🔄 RESCATANDO: {nombre} desde página {pagina_inicio}")

    while pagina_actual <= total_paginas:
        res, cuota = llamar_api(loc_id, pagina_actual)
        
        if res and 'elementList' in res:
            todos_los_pisos.extend(res['elementList'])
            print(f"   ✅ Pág {pagina_actual}/{total_paginas} | Rescatados: {len(todos_los_pisos)} | 🎫 Cuota: {cuota}")
            pagina_actual += 1
            time.sleep(5) # AUMENTA EL TIEMPO a 5 segundos para que no te vuelvan a banear
        else:
            print(f"   ⚠️ Falló de nuevo en pág {pagina_actual}. Para y espera 15 min.")
            break

    if todos_los_pisos:
        # Guardamos con un nombre distinto para no sobreescribir el anterior
        filename = f"madrid_{nombre}_PARTE_2.json"
        with open(filename, "w", encoding="utf-8") as f:
            json.dump(todos_los_pisos, f, indent=4, ensure_ascii=False)
        print(f"\n💾 GUARDADA PARTE 2: {filename}")


if __name__ == "__main__":
    descargar_un_distrito(DISTRICT_TO_FETCH)
    # descargar_desde_pagina(DISTRICT_TO_FETCH, 34)