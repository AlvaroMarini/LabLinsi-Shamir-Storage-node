# Shamir Storage Node (PoC) 🔐

> Prueba de Concepto (PoC) para un Sistema de Almacenamiento Distribuido de Alta Seguridad utilizando Criptografía de Umbral y Validación de Integridad (VSS). Desarrollado para el Laboratorio de Investigación en Sistemas de Información (LINSI).

## 📌 Descripción del Proyecto
Este proyecto implementa el **Esquema de Compartición de Secretos de Shamir (Shamir's Secret Sharing)** en un entorno de red. Su objetivo es mitigar los riesgos de almacenamiento centralizado dividiendo un secreto (claves, credenciales, datos sensibles) en $n$ fragmentos distribuidos. El sistema garantiza matemáticamente que el secreto solo puede reconstruirse si se reúne un umbral mínimo de $k$ fragmentos, asegurando confidencialidad y disponibilidad ante fallos o brechas de seguridad.

Para evitar ataques de corrupción de datos o la intercepción de nodos comprometidos, el motor matemático integra validaciones de integridad criptográfica mediante funciones hash (SHA-256), descartando automáticamente fragmentos alterados antes de la interpolación polinomial.

## 📚 Marco Teórico y Referencias Académicas
El diseño arquitectónico y las defensas criptográficas de este laboratorio se fundamentan en los siguientes consensos científicos y literatura de alto impacto:

### Criptografía de Umbral y Verificabilidad
* **Shamir, A. (1979).** *How to Share a Secret*. Publicado en Communications of the ACM. **(Indexado en ACM Digital Library)**. Constituye la base matemática del fraccionamiento sobre campos finitos utilizado en el dominio del proyecto.
* **Feldman, P. (1987).** *A Verifiable Secret Sharing Scheme*. Publicado en Proceedings of the 28th Annual Symposium on Foundations of Computer Science (IEEE FOCS). **(Indexado en IEEE Xplore)**. Respalda la necesidad de implementar mecanismos (como nuestra validación SHA-256) para detectar y descartar nodos que envíen fragmentos corruptos durante la reconstrucción.

### Arquitectura de Nodos y Zero Trust
* *Security and Privacy in Cloud Storage Using Threshold Cryptography: A Review*. Publicado en IEEE Access. **(Indexado en IEEE Xplore)**.
* *A Clean-Slate Look at Zero Trust Architecture in Containerized Environments*. Publicado en ACM SIGCOMM Computer Communication Review. **(Indexado en ACM Digital Library)**. Utilizado como referencia para el aislamiento de endpoints y microsegmentación requerida en la capa de red.

### Prevención de Impacto (Ransomware y Entropía)
* **Scaife, N., Carter, H., Traynor, P., & Butler, T.** *An Early Detection and Mitigation System for Ransomware Attacks Based on Information Entropy*. Publicado en IEEE Transactions on Dependable and Secure Computing. **(Indexado en IEEE Xplore)**.
* *CryptoDrop: Early Detection of Ransomware Attacks*. Proceedings of the 2016 ACM International Workshop on Security and Privacy Analytics. **(Indexado en ACM Digital Library)**

## 🏗️ Arquitectura
El desarrollo sigue el patrón de **Arquitectura Hexagonal (Ports & Adapters)** para garantizar el desacoplamiento total de las reglas de negocio:
* **Domain:** Contiene la lógica criptográfica pura, aritmética sobre campos finitos y validación de integridad SHA-256. No posee dependencias externas.
* **Adapters:** Expone el dominio a través de una API REST de alto rendimiento utilizando **FastAPI**.
* **Tests:** Suite de pruebas unitarias (TDD) para garantizar la integridad de las operaciones matemáticas de fraccionamiento, recuperación y tolerancia a datos corruptos.

## 📂 Estructura del Repositorio

```text
shamir-storage-node/
├── src/
│   ├── adapters/
│   │   └── api.py           # Endpoints REST (FastAPI)
│   ├── domain/
│   │   ├── __init__.py
│   │   └── shamir.py        # Core criptográfico (Polinomios de Lagrange + Hashing)
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
El núcleo criptográfico está validado mediante pruebas automatizadas (división, recuperación exacta y rechazo automático de fragmentos alterados). Para ejecutar la suite completa de pruebas, simplemente corre:

```bash
pytest
```

## 🛣️ Roadmap / Próximos Pasos
- [x] Motor matemático criptográfico sobre Campos Finitos.
- [x] Validación de integridad de fragmentos (SHA-256).
- [x] API REST para división (`/split`) y recuperación (`/recover`).
- [x] Desarrollo del cliente "Prover" (Frontend / Dashboard Web).
- [ ] Infraestructura de Nodos Distribuida (Dockerización de contenedores aislados).
- [ ] Protocolos de comunicación Zero Trust entre el cliente y los nodos.
