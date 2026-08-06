import os
import asyncio
import httpx
import hashlib
import jwt
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Security, Depends
from fastapi.security import APIKeyHeader, HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
from src.domain.shamir import ShamirScheme

load_dotenv()

# --- SEGMENTACIÓN DE CREDENCIALES ---
PUBLIC_API_KEY = os.getenv("PUBLIC_API_KEY")
INTERNAL_CLUSTER_KEY = os.getenv("INTERNAL_CLUSTER_KEY")

api_key_header = APIKeyHeader(name="x-api-key", auto_error=True)
security_bearer = HTTPBearer()

def validate_public_key(api_key: str = Security(api_key_header)):
    if PUBLIC_API_KEY is None or api_key != PUBLIC_API_KEY:
        raise HTTPException(status_code=403, detail="Acceso denegado: Llave pública inválida (Gateway DMZ).")
    return api_key

# --- NUEVO: VALIDACIÓN DE IDENTIDAD FEDERADA (JWT) ---
async def get_current_user(credentials: HTTPAuthorizationCredentials = Security(security_bearer)):
    token = credentials.credentials
    try:
        # Consultamos las llaves públicas de Keycloak (JWKS) en la red interna
        async with httpx.AsyncClient() as client:
            resp = await client.get("http://keycloak:8080/realms/shamir-realm/protocol/openid-connect/certs")
            jwks = resp.json()

        public_keys = {}
        for jwk in jwks['keys']:
            kid = jwk['kid']
            public_keys[kid] = jwt.algorithms.RSAAlgorithm.from_jwk(jwk)

        unverified_header = jwt.get_unverified_header(token)
        rsa_key = public_keys.get(unverified_header['kid'])
        
        if not rsa_key:
            raise HTTPException(status_code=401, detail="Firma del token desconocida.")

        # Validamos criptográficamente el token
        payload = jwt.decode(
            token,
            rsa_key,
            algorithms=["RS256"],
            options={"verify_aud": False} # Simplificación para la PoC
        )
        
        # Extraemos la identidad blindada
        return payload.get("preferred_username") or payload.get("sub")
        
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="El token de sesión expiró.")
    except Exception as e:
        raise HTTPException(status_code=401, detail="Acceso denegado: Token adulterado o inválido.")

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
async def split_secret(request: SplitRequest, api_key: str = Depends(validate_public_key), current_user: str = Depends(get_current_user)):
    try:
        shamir = ShamirScheme(total_shares=request.total_shares, threshold=request.threshold)
        secret_bytes = request.secret.encode('utf-8')
        raw_shares = shamir.split_secret(secret_bytes)

        # ZERO TRUST: Hasheamos la identidad validada por Keycloak, ignorando el request del cliente
        hashed_owner = hashlib.sha256(current_user.encode('utf-8')).hexdigest()

        vault_requests = [
            VaultStoreRequest(x=share[0], y=share[1].hex(), hash=share[2], owner_id=hashed_owner) 
            for share in raw_shares
        ]
        
        async with httpx.AsyncClient(timeout=10.0) as client:
            headers = {"x-api-key": INTERNAL_CLUSTER_KEY}
            tasks = []
            for i, share_req in enumerate(vault_requests):
                if i < len(NODES):
                    url = f"{NODES[i]}/store/{request.secret_id}"
                    tasks.append(client.post(url, json=share_req.model_dump(), headers=headers))
            
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            success_count = sum(1 for r in results if not isinstance(r, Exception) and r.status_code == 200)
            if success_count < request.threshold:
                # Recuperamos el mapeo de errores para ver qué está fallando en la red privada
                errores = [r.status_code if hasattr(r, 'status_code') else type(r).__name__ for r in results]
                raise HTTPException(status_code=500, detail=f"Fallo de escritura en bóvedas. Detalles: {errores}")
            
        return SplitResponse(shares=[ShareResponse(**req.model_dump()) for req in vault_requests])
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/api/recover/{secret_id}", response_model=RecoverResponse)
async def recover_secret(secret_id: str, api_key: str = Depends(validate_public_key), current_user: str = Depends(get_current_user)):
    recovered_shares = []

    # ZERO TRUST: Usamos la identidad criptográfica
    hashed_owner = hashlib.sha256(current_user.encode('utf-8')).hexdigest()

    async with httpx.AsyncClient(timeout=10.0) as client:
        headers = {"x-api-key": INTERNAL_CLUSTER_KEY}
        tasks = [client.get(f"{node}/retrieve/{secret_id}", params={"owner_id": hashed_owner}, headers=headers) for node in NODES]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        for response in results:
            if not isinstance(response, Exception) and response.status_code == 200:
                recovered_shares.append(ShareResponse(**response.json()))

    if len(recovered_shares) < 3:
        # Analizamos las respuestas fallidas para dar un diagnóstico exacto
        denegados = sum(1 for r in results if not isinstance(r, Exception) and r.status_code == 403)
        caidos = sum(1 for r in results if isinstance(r, Exception))

        if denegados >= 3:
            raise HTTPException(status_code=403, detail="Acceso denegado: El archivo pertenece a otro usuario o no existe.")
        elif caidos >= 3:
            raise HTTPException(status_code=503, detail="Red inestable: No hay suficientes bóvedas en línea (se requieren 3).")
        else:
            raise HTTPException(status_code=500, detail="Fragmentos insuficientes o corruptos para reconstruir el archivo.")

    try:
        shamir = ShamirScheme(total_shares=5, threshold=3)
        raw_shares = [(s.x, bytes.fromhex(s.y), s.hash) for s in recovered_shares]
        secret_bytes = shamir.recover_secret(raw_shares)
        return RecoverResponse(secret=secret_bytes.decode('utf-8').replace('\x00', ''))
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error al interpolar: {str(e)}")