import os
import sqlite3
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Security, Depends
from fastapi.security.api_key import APIKeyHeader
from pydantic import BaseModel

load_dotenv()

API_KEY = os.getenv("API_KEY")
api_key_header = APIKeyHeader(name="x-api-key", auto_error=True)

def get_api_key(api_key: str = Security(api_key_header)):
    if API_KEY is None or api_key != API_KEY:
        raise HTTPException(status_code=403, detail="Acceso denegado: Bóveda sellada (Zero Trust).")
    return api_key

app = FastAPI(title="Storage Vault Node (SQLite)")

class ShareData(BaseModel):
    x: int
    y: str
    hash: str

# --- CONFIGURACIÓN DE LA BASE DE DATOS SQLITE ---
DATA_DIR = "data"
os.makedirs(DATA_DIR, exist_ok=True)
DB_PATH = os.path.join(DATA_DIR, "vault.db")

def init_db():
    """Inicializa la tabla SQL si no existe al encender el contenedor."""
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS fragments (
                secret_id TEXT PRIMARY KEY,
                x INTEGER,
                y TEXT,
                hash TEXT
            )
        ''')
        conn.commit()

# Ejecutamos la inicialización
init_db()

@app.post("/store/{secret_id}")
def store_share(secret_id: str, share: ShareData, api_key: str = Depends(get_api_key)):
    try:
        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.cursor()
            # Usamos INSERT OR REPLACE para sobrescribir si el ID ya existe
            cursor.execute('''
                INSERT OR REPLACE INTO fragments (secret_id, x, y, hash)
                VALUES (?, ?, ?, ?)
            ''', (secret_id, share.x, share.y, share.hash))
            conn.commit()
        return {"status": "Fragmento asegurado en bóveda SQLite"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error interno de base de datos: {str(e)}")

@app.get("/retrieve/{secret_id}")
def retrieve_share(secret_id: str, api_key: str = Depends(get_api_key)):
    with sqlite3.connect(DB_PATH) as conn:
        # Configuramos SQLite para que devuelva un diccionario y FastAPI lo transforme a JSON fácil
        conn.row_factory = sqlite3.Row 
        cursor = conn.cursor()
        
        cursor.execute('SELECT x, y, hash FROM fragments WHERE secret_id = ?', (secret_id,))
        row = cursor.fetchone()
        
        if row is None:
            raise HTTPException(status_code=404, detail="Fragmento no encontrado en esta bóveda")
            
        return dict(row)