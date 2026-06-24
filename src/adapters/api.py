import os
import asyncio
import httpx
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Security, Depends
from fastapi.security.api_key import APIKeyHeader
from pydantic import BaseModel
from src.domain.shamir import ShamirScheme

load_dotenv()

API_KEY_NAME = "x-api-key"
API_KEY = os.getenv("API_KEY")
api_key_header = APIKeyHeader(name=API_KEY_NAME, auto_error=True)

def get_api_key(api_key: str = Security(api_key_header)):
    if API_KEY is None:
        raise HTTPException(status_code=500, detail="Error de configuración: API_KEY no definida.")
    if api_key != API_KEY:
        raise HTTPException(status_code=403, detail="Acceso denegado (Zero Trust Policy).")
    return api_key

app = FastAPI(title="Shamir Gateway Node")

# --- Nodos internos de la red Docker ---
NODES = [
    "http://node-1:8000",
    "http://node-2:8000",
    "http://node-3:8000",
    "http://node-4:8000",
    "http://node-5:8000"
]

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

class RecoverResponse(BaseModel):
    secret: str

@app.post("/api/split", response_model=SplitResponse)
async def split_secret(request: SplitRequest, api_key: str = Depends(get_api_key)):
    try:
        shamir = ShamirScheme(total_shares=request.total_shares, threshold=request.threshold)
        secret_bytes = request.secret.encode('utf-8')
        raw_shares = shamir.split_secret(secret_bytes)
        
        formatted_shares = [
            ShareResponse(x=share[0], y=share[1].hex(), hash=share[2]) 
            for share in raw_shares
        ]
        
        # --- NUEVO: Distribuir fragmentos a las bóvedas ---
        async with httpx.AsyncClient(timeout=1.0) as client:
            headers = {"x-api-key": API_KEY}
            tasks = []
            
            for i, share in enumerate(formatted_shares):
                if i < len(NODES):
                    url = f"{NODES[i]}/store"
                    tasks.append(client.post(url, json=share.model_dump(), headers=headers))
            
            # Disparamos las 5 peticiones HTTP al mismo tiempo
            await asyncio.gather(*tasks, return_exceptions=True)
            
        return SplitResponse(shares=formatted_shares)
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/api/recover", response_model=RecoverResponse)
async def recover_secret(api_key: str = Depends(get_api_key)):
    recovered_shares = []
    
    # --- NUEVO: Recolectar fragmentos de las bóvedas ---
    async with httpx.AsyncClient(timeout=1.0) as client:
        headers = {"x-api-key": API_KEY}
        tasks = [client.get(f"{node}/retrieve", headers=headers) for node in NODES]
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        for response in results:
            if not isinstance(response, Exception) and response.status_code == 200:
                data = response.json()
                recovered_shares.append(ShareResponse(**data))

    # Validamos si juntamos el umbral mínimo (3)
    if len(recovered_shares) < 3:
        raise HTTPException(status_code=400, detail=f"Nodos insuficientes. Fragmentos recuperados: {len(recovered_shares)}")

    try:
        shamir = ShamirScheme(total_shares=5, threshold=3)
        raw_shares = [
            (share.x, bytes.fromhex(share.y), share.hash)
            for share in recovered_shares
        ]
        
        secret_bytes = shamir.recover_secret(raw_shares)
        secret_str = secret_bytes.decode('utf-8').replace('\x00', '')
        
        return RecoverResponse(secret=secret_str)
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error al interpolar: {str(e)}")