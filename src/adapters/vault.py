import os
import json
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

app = FastAPI(title="Storage Vault Node")

class ShareData(BaseModel):
    x: int
    y: str
    hash: str

# Guardamos usando el ID en la ruta
@app.post("/store/{secret_id}")
def store_share(secret_id: str, share: ShareData, api_key: str = Depends(get_api_key)):
    file_name = f"share_{secret_id}.json"
    with open(file_name, "w") as f:
        json.dump(share.model_dump(), f)
    return {"status": "Fragmento asegurado en bóveda local"}

# Recuperamos buscando el archivo con el ID específico
@app.get("/retrieve/{secret_id}")
def retrieve_share(secret_id: str, api_key: str = Depends(get_api_key)):
    file_name = f"share_{secret_id}.json"
    if not os.path.exists(file_name):
        raise HTTPException(status_code=404, detail="Fragmento no encontrado en esta bóveda")
    with open(file_name, "r") as f:
        return json.load(f)