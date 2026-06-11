# Shamir Storage Node (PoC) 🔐

> Prueba de Concepto (PoC) para un Sistema de Almacenamiento Distribuido de Alta Seguridad utilizando Criptografía de Umbral. Desarrollado para el Laboratorio de Investigación en Sistemas de Información (LINSI).

## 📌 Descripción del Proyecto
Este proyecto implementa el **Esquema de Compartición de Secretos de Shamir (Shamir's Secret Sharing)** en un entorno de red. Su objetivo es mitigar los riesgos de almacenamiento centralizado dividiendo un secreto (claves, credenciales, datos sensibles) en $n$ fragmentos distribuidos. El sistema garantiza matemáticamente que el secreto solo puede reconstruirse si se reúne un umbral mínimo de $k$ fragmentos, asegurando confidencialidad y disponibilidad ante fallos o brechas de seguridad.

Actualmente, el proyecto contiene el **Core Matemático** y la **API REST** (Backend), diseñados bajo principios estrictos de Arquitectura de Software.

## 🏗️ Arquitectura
El desarrollo sigue el patrón de **Arquitectura Hexagonal (Ports & Adapters)** para garantizar el desacoplamiento total de las reglas de negocio:
* **Domain:** Contiene la lógica criptográfica pura y la aritmética sobre campos finitos. No posee dependencias externas.
* **Adapters:** Expone el dominio a través de una API REST de alto rendimiento utilizando **FastAPI**.
* **Tests:** Suite de pruebas unitarias (TDD) para garantizar la integridad de las operaciones matemáticas de fraccionamiento y recuperación.

## 📂 Estructura del Repositorio

```text
shamir-storage-node/
├── src/
│   ├── adapters/
│   │   └── api.py           # Endpoints REST (FastAPI)
│   ├── domain/
│   │   ├── __init__.py
│   │   └── shamir.py        # Core criptográfico (Polinomios de Lagrange)
│   └── __init__.py
├── tests/
│   └── test_shamir.py       # Suite de TDD (Pytest)
├── pyproject.toml           # Configuración de herramientas
├── .gitignore
└── README.md
```

## ⚙️ Requisitos Previos
Para ejecutar este proyecto de forma local, necesitarás:
* **Python 3.10+**
* **uv** (Gestor de paquetes y entornos de ultra alta velocidad)

## 🚀 Instalación y Configuración

**1. Clonar el repositorio:**
```bash
git clone [https://github.com/TU_USUARIO/shamir-storage-node.git](https://github.com/TU_USUARIO/shamir-storage-node.git)
cd shamir-storage-node
```

**2. Crear y activar el entorno virtual:**
```bash
# Crear el entorno
uv venv

# Activar en Windows (Git Bash / PowerShell)
source .venv/Scripts/activate
# (En Linux/macOS usar: source .venv/bin/activate)
```

**3. Instalar dependencias:**
```bash
uv pip install fastapi uvicorn pytest
```

## 💻 Ejecución del Servidor de Desarrollo

Para levantar la API REST de forma local, ejecuta el siguiente comando:

```bash
uvicorn src.adapters.api:app --reload
```

El servidor estará disponible en `http://localhost:8000`. 
Puedes acceder a la **documentación interactiva y consola de pruebas (Swagger UI)** navegando a:
👉 `http://localhost:8000/docs`

## 🧪 Testing (TDD)
El núcleo criptográfico está validado mediante pruebas automatizadas. Para ejecutar la suite completa de pruebas, simplemente corre:

```bash
pytest
```

## 🛣️ Roadmap / Próximos Pasos
- [x] Motor matemático criptográfico sobre Campos Finitos.
- [x] API REST para división (`/split`) y recuperación (`/recover`).
- [ ] Desarrollo del cliente "Prover" (Frontend / Dashboard Web).
- [ ] Infraestructura de Nodos Distribuida (Dockerización de contenedores aislados).
- [ ] Protocolos de comunicación Zero Trust entre el cliente y los nodos.