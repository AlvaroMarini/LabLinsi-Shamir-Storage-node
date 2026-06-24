# Usamos una imagen oficial y liviana de Python
FROM python:3.10-slim

# Directorio de trabajo dentro del contenedor
WORKDIR /app

# Instalamos dependencias usando uv para máxima velocidad
COPY pyproject.toml .
RUN pip install uv && uv pip install --system fastapi uvicorn pydantic python-dotenv httpx

# Copiamos el código fuente (Arquitectura Hexagonal)
COPY src/ ./src/

# Exponemos el puerto interno del contenedor
EXPOSE 8000

# Comando para encender el nodo
CMD ["uvicorn", "src.adapters.api:app", "--host", "0.0.0.0", "--port", "8000"]