from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from src.domain.shamir import ShamirScheme

# Inicializamos la API
app = FastAPI(
    title="Shamir Storage Node API",
    description="API para fragmentación de secretos del LINSI",
    version="1.0.0"
)

# --- Modelos de datos (Pydantic) ---
# Definen la forma exacta del JSON que esperamos recibir y enviar

class SplitRequest(BaseModel):
    secret: str
    total_shares: int = 5
    threshold: int = 3

class ShareResponse(BaseModel):
    x: int
    y: str  # Los bytes los mandamos como texto hexadecimal

class SplitResponse(BaseModel):
    shares: list[ShareResponse]

# --- Rutas (Endpoints) ---

@app.post("/api/split", response_model=SplitResponse)
def split_secret(request: SplitRequest):
    try:
        # 1. Instanciamos nuestra clase del Dominio
        shamir = ShamirScheme(total_shares=request.total_shares, threshold=request.threshold)
        
        # 2. Convertimos el texto que llegó por la red a bytes
        secret_bytes = request.secret.encode('utf-8')
        
        # 3. Ejecutamos la matemática pura
        raw_shares = shamir.split_secret(secret_bytes)
        
        # 4. Formateamos los resultados para enviarlos por internet
        formatted_shares = [
            ShareResponse(x=share[0], y=share[1].hex()) 
            for share in raw_shares
        ]
        
        return SplitResponse(shares=formatted_shares)
        
    except ValueError as e:
        # Si la regla de negocio falla (ej: k > n), devolvemos un error HTTP 400
        raise HTTPException(status_code=400, detail=str(e))
    
# --- Nuevos Modelos para Recuperación ---

class RecoverRequest(BaseModel):
    shares: list[ShareResponse]
    total_shares: int = 5
    threshold: int = 3

class RecoverResponse(BaseModel):
    secret: str

# --- Nuevo Endpoint ---

@app.post("/api/recover", response_model=RecoverResponse)
def recover_secret(request: RecoverRequest):
    try:
        # 1. Instanciamos el Dominio
        shamir = ShamirScheme(total_shares=request.total_shares, threshold=request.threshold)
        
        # 2. Convertimos los fragmentos de hexadecimal (red) de vuelta a bytes (matemática)
        raw_shares = [
            (share.x, bytes.fromhex(share.y))
            for share in request.shares
        ]
        
        # 3. Ejecutamos la matemática de interpolación
        secret_bytes = shamir.recover_secret(raw_shares)
        
        # 4. Decodificamos los bytes a texto legible
        # (Usamos replace para limpiar caracteres nulos que puedan quedar del padding matemático)
        secret_str = secret_bytes.decode('utf-8').replace('\x00', '')
        
        return RecoverResponse(secret=secret_str)
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except UnicodeDecodeError:
        raise HTTPException(
            status_code=400, 
            detail="Error al decodificar. Los fragmentos no coinciden o no alcanzan el umbral."
        )