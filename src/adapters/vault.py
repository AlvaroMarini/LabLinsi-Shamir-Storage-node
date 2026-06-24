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

# Archivo local donde este nodo guardará su fragmento
VAULT_FILE = "secret_share.json"

@app.post("/store")
def store_share(share: ShareData, api_key: str = Depends(get_api_key)):
    with open(VAULT_FILE, "w") as f:
        # Guardamos los datos en formato JSON
        json.dump(share.model_dump(), f)
    return {"status": "Fragmento asegurado en bóveda local"}

@app.get("/retrieve")
def retrieve_share(api_key: str = Depends(get_api_key)):
    if not os.path.exists(VAULT_FILE):
        raise HTTPException(status_code=404, detail="Bóveda vacía")
    with open(VAULT_FILE, "r") as f:
        return json.load(f)