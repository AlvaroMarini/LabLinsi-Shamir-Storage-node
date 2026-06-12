from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from src.domain.shamir import ShamirScheme

app = FastAPI(
    title="Shamir Storage Node API",
    description="API para fragmentación de secretos del LINSI (Validación criptográfica incluida)",
    version="1.1.0"
)

# --- Modelos de datos ---

class SplitRequest(BaseModel):
    secret: str
    total_shares: int = 5
    threshold: int = 3

class ShareResponse(BaseModel):
    x: int
    y: str  
    hash: str

class SplitResponse(BaseModel):
    shares: list[ShareResponse]

class RecoverRequest(BaseModel):
    shares: list[ShareResponse]
    total_shares: int = 5
    threshold: int = 3

class RecoverResponse(BaseModel):
    secret: str

# --- Rutas ---

@app.post("/api/split", response_model=SplitResponse)
def split_secret(request: SplitRequest):
    try:
        shamir = ShamirScheme(total_shares=request.total_shares, threshold=request.threshold)
        secret_bytes = request.secret.encode('utf-8')
        raw_shares = shamir.split_secret(secret_bytes)
        
        # Desempaquetamos los 3 elementos (x, y, hash)
        formatted_shares = [
            ShareResponse(x=share[0], y=share[1].hex(), hash=share[2]) 
            for share in raw_shares
        ]
        
        return SplitResponse(shares=formatted_shares)
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/api/recover", response_model=RecoverResponse)
def recover_secret(request: RecoverRequest):
    try:
        shamir = ShamirScheme(total_shares=request.total_shares, threshold=request.threshold)
        
        # Volvemos a armar la tupla con los 3 elementos para enviarlos al Dominio
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