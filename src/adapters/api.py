import os
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Security, Depends
from fastapi.security.api_key import APIKeyHeader
from pydantic import BaseModel
from src.domain.shamir import ShamirScheme

load_dotenv()

# --- NUEVO: Configuración Zero Trust ---
API_KEY_NAME = "x-api-key"
API_KEY = os.getenv("API_KEY")
api_key_header = APIKeyHeader(name=API_KEY_NAME, auto_error=True)

def get_api_key(api_key: str = Security(api_key_header)):
    if API_KEY is None:
        raise HTTPException(status_code=500, detail="Error de configuración: API_KEY no definida en el servidor.")
    if api_key != API_KEY:
        raise HTTPException(status_code=403, detail="Acceso denegado: API Key inválida o faltante (Zero Trust Policy).")
    return api_key

app = FastAPI(
    title="Shamir Storage Node API",
    description="API para fragmentación de secretos del LINSI (Validación criptográfica y Zero Trust incluida)",
    version="1.2.0"
)

# --- Modelos de datos ---
class SplitRequest(BaseModel):
    secret: str
    total_shares: int = 10
    threshold: int = 6

class ShareResponse(BaseModel):
    x: int
    y: str  
    hash: str  

class SplitResponse(BaseModel):
    shares: list[ShareResponse]

class RecoverRequest(BaseModel):
    shares: list[ShareResponse]
    total_shares: int = 10
    threshold: int = 6

class RecoverResponse(BaseModel):
    secret: str

# --- Rutas protegidas ---

# Observá cómo agregamos el parámetro "api_key" a la función para forzar la validación
@app.post("/api/split", response_model=SplitResponse)
def split_secret(request: SplitRequest, api_key: str = Depends(get_api_key)):
    try:
        shamir = ShamirScheme(total_shares=request.total_shares, threshold=request.threshold)
        secret_bytes = request.secret.encode('utf-8')
        raw_shares = shamir.split_secret(secret_bytes)
        
        formatted_shares = [
            ShareResponse(x=share[0], y=share[1].hex(), hash=share[2]) 
            for share in raw_shares
        ]
        
        return SplitResponse(shares=formatted_shares)
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/api/recover", response_model=RecoverResponse)
def recover_secret(request: RecoverRequest, api_key: str = Depends(get_api_key)):
    try:
        shamir = ShamirScheme(total_shares=request.total_shares, threshold=request.threshold)
        
        raw_shares = [
            (share.x, bytes.fromhex(share.y), share.hash)
            for share in request.shares
        ]
        
        secret_bytes = shamir.recover_secret(raw_shares)
        secret_str = secret_bytes.decode('utf-8').replace('\x00', '')
        
        return RecoverResponse(secret=secret_str)
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except UnicodeDecodeError:
        raise HTTPException(
            status_code=400, 
            detail="Error al decodificar. Demasiados fragmentos corruptos o insuficientes."
        )