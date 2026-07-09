import os
import asyncio
import httpx
import hashlib
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Security, Depends
from fastapi.security.api_key import APIKeyHeader
from pydantic import BaseModel
from src.domain.shamir import ShamirScheme

load_dotenv()

# --- SEGMENTACIÓN DE CREDENCIALES ---
PUBLIC_API_KEY = os.getenv("PUBLIC_API_KEY")
INTERNAL_CLUSTER_KEY = os.getenv("INTERNAL_CLUSTER_KEY")

api_key_header = APIKeyHeader(name="x-api-key", auto_error=True)

def validate_public_key(api_key: str = Security(api_key_header)):
    """Valida la petición entrante desde el Frontend."""
    if PUBLIC_API_KEY is None or api_key != PUBLIC_API_KEY:
        raise HTTPException(status_code=403, detail="Acceso denegado: Llave pública inválida (Gateway DMZ).")
    return api_key

app = FastAPI(title="Shamir Gateway Node")

NODES = [
    "http://node-1:8000",
    "http://node-2:8000",
    "http://node-3:8000",
    "http://node-4:8000",
    "http://node-5:8000"
]

class SplitRequest(BaseModel):
    secret_id: str
    secret: str
    owner_id: str
    total_shares: int = 5
    threshold: int = 3

class ShareResponse(BaseModel):
    x: int
    y: str  
    hash: str  

class VaultStoreRequest(BaseModel):
    x: int
    y: str
    hash: str
    owner_id: str

class SplitResponse(BaseModel):
    shares: list[ShareResponse]

class RecoverResponse(BaseModel):
    secret: str

@app.post("/api/split", response_model=SplitResponse)
async def split_secret(request: SplitRequest, api_key: str = Depends(validate_public_key)):
    try:
        shamir = ShamirScheme(total_shares=request.total_shares, threshold=request.threshold)
        secret_bytes = request.secret.encode('utf-8')
        raw_shares = shamir.split_secret(secret_bytes)

        hashed_owner = hashlib.sha256(request.owner_id.encode('utf-8')).hexdigest()

        vault_requests = [
            VaultStoreRequest(x=share[0], y=share[1].hex(), hash=share[2], owner_id=hashed_owner) 
            for share in raw_shares
        ]
        
        async with httpx.AsyncClient(timeout=10.0) as client:
            # ENVIAMOS LA LLAVE PRIVADA A LAS BÓVEDAS
            headers = {"x-api-key": INTERNAL_CLUSTER_KEY}
            tasks = []
            for i, share_req in enumerate(vault_requests):
                if i < len(NODES):
                    url = f"{NODES[i]}/store/{request.secret_id}"
                    tasks.append(client.post(url, json=share_req.model_dump(), headers=headers))
            
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            success_count = sum(1 for r in results if not isinstance(r, Exception) and r.status_code == 200)
            if success_count < request.threshold:
                errores = [r.status_code if not isinstance(r, Exception) else type(r).__name__ for r in results]
                raise HTTPException(status_code=500, detail=f"Fallo de escritura en bóvedas. Detalles: {errores}")
            
        return SplitResponse(shares=[ShareResponse(**req.model_dump()) for req in vault_requests])
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/api/recover/{secret_id}", response_model=RecoverResponse)
async def recover_secret(secret_id: str, owner_id: str, api_key: str = Depends(validate_public_key)):
    recovered_shares = []

    hashed_owner = hashlib.sha256(owner_id.encode('utf-8')).hexdigest()

    async with httpx.AsyncClient(timeout=10.0) as client:
        # ENVIAMOS LA LLAVE PRIVADA A LAS BÓVEDAS
        headers = {"x-api-key": INTERNAL_CLUSTER_KEY}
        tasks = [client.get(f"{node}/retrieve/{secret_id}", params={"owner_id": hashed_owner}, headers=headers) for node in NODES]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        for response in results:
            if not isinstance(response, Exception) and response.status_code == 200:
                recovered_shares.append(ShareResponse(**response.json()))

    if len(recovered_shares) < 3:
        raise HTTPException(status_code=403, detail="Nodos insuficientes o acceso denegado.")

    try:
        shamir = ShamirScheme(total_shares=5, threshold=3)
        raw_shares = [(s.x, bytes.fromhex(s.y), s.hash) for s in recovered_shares]
        secret_bytes = shamir.recover_secret(raw_shares)
        return RecoverResponse(secret=secret_bytes.decode('utf-8').replace('\x00', ''))
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error al interpolar: {str(e)}")