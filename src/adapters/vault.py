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

app = FastAPI(title="Storage Vault Node (SQLite + IAM)")

class ShareData(BaseModel):
    x: int
    y: str
    hash: str
    owner_id: str  # <-- NUEVO: Identidad del dueño

# --- CONFIGURACIÓN DE LA BASE DE DATOS SQLITE ---
DATA_DIR = "data"
os.makedirs(DATA_DIR, exist_ok=True)
DB_PATH = os.path.join(DATA_DIR, "vault.db")

def init_db():
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        # Modificamos la tabla para incluir al dueño
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS fragments (
                secret_id TEXT PRIMARY KEY,
                owner_id TEXT,
                x INTEGER,
                y TEXT,
                hash TEXT
            )
        ''')
        conn.commit()

init_db()

@app.post("/store/{secret_id}")
def store_share(secret_id: str, share: ShareData, api_key: str = Depends(get_api_key)):
    try:
        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT OR REPLACE INTO fragments (secret_id, owner_id, x, y, hash)
                VALUES (?, ?, ?, ?, ?)
            ''', (secret_id, share.owner_id, share.x, share.y, share.hash))
            conn.commit()
        return {"status": "Fragmento asegurado en bóveda"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# NUEVO: Pedimos el owner_id en la URL
@app.get("/retrieve/{secret_id}")
def retrieve_share(secret_id: str, owner_id: str, api_key: str = Depends(get_api_key)):
    with sqlite3.connect(DB_PATH) as conn:
        conn.row_factory = sqlite3.Row 
        cursor = conn.cursor()
        
        # La bóveda ahora exige que el dueño coincida para soltar el fragmento
        cursor.execute('SELECT x, y, hash FROM fragments WHERE secret_id = ? AND owner_id = ?', (secret_id, owner_id))
        row = cursor.fetchone()
        
        if row is None:
            raise HTTPException(status_code=403, detail="Acceso denegado o archivo inexistente.")
            
        return dict(row)