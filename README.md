# Shamir Storage Node (PoC) 🔐

> Prueba de Concepto (PoC) para un Sistema de Almacenamiento Distribuido de Alta Seguridad utilizando Criptografía de Umbral, Validación de Integridad (VSS) y Cifrado AES-256. Desarrollado para el Laboratorio de Investigación en Sistemas de Información (LINSI).

## 📌 Descripción del Proyecto
Este proyecto implementa una arquitectura **Zero Trust** combinada con el **Esquema de Compartición de Secretos de Shamir (Shamir's Secret Sharing)** en un entorno de red distribuido. Su objetivo es mitigar los riesgos de almacenamiento centralizado, garantizando la confidencialidad y disponibilidad de los archivos ante fallos de hardware o brechas de seguridad.

El flujo de protección garantiza que **los archivos originales nunca toquen los servidores**. Toda la encriptación de archivos (AES-256) ocurre localmente en el navegador del cliente mediante la *Web Crypto API*. Únicamente la clave criptográfica resultante es enviada a la red, donde el motor matemático la divide en **n** fragmentos distribuidos. El sistema garantiza que la clave (y por ende, el archivo) solo puede reconstruirse si se reúne un umbral mínimo de **k** fragmentos.

Para evitar ataques de corrupción de datos o la intercepción de nodos comprometidos, se integran validaciones de integridad criptográfica mediante funciones hash (SHA-256), descartando automáticamente fragmentos alterados antes de la interpolación polinomial.

## 📚 Marco Teórico y Referencias Académicas
El diseño arquitectónico y las defensas criptográficas de este laboratorio se fundamentan en los siguientes consensos científicos y literatura de alto impacto:

### Criptografía de Umbral y Verificabilidad
* **Shamir, A. (1979).** *How to Share a Secret*. Publicado en Communications of the ACM. Constituye la base matemática del fraccionamiento sobre campos finitos utilizado en el dominio del proyecto.
* **Feldman, P. (1987).** *A Verifiable Secret Sharing Scheme*. Publicado en IEEE FOCS. Respalda la necesidad de implementar mecanismos (como nuestra validación SHA-256) para detectar y descartar nodos que envíen fragmentos corruptos durante la reconstrucción.

### Arquitectura de Nodos y Zero Trust
* *Security and Privacy in Cloud Storage Using Threshold Cryptography: A Review*. Publicado en IEEE Access.
* *A Clean-Slate Look at Zero Trust Architecture in Containerized Environments*. Publicado en ACM SIGCOMM. Utilizado como referencia para el aislamiento de endpoints y microsegmentación requerida en la capa de red interna de Docker.

### Prevención de Impacto (Ransomware y Entropía)
* **Scaife, N., Carter, H., Traynor, P., & Butler, T.** *An Early Detection and Mitigation System for Ransomware Attacks Based on Information Entropy*. Publicado en IEEE Transactions on Dependable and Secure Computing.

## 🏗️ Arquitectura del Sistema
El desarrollo sigue el patrón de **Arquitectura Hexagonal (Ports & Adapters)** en el backend y una clara separación de responsabilidades en la red:

* **Cliente Frontend (React/Vite):** Responsable de generar llaves AES-256, cifrar/descifrar archivos localmente y comunicarse de forma segura con el Gateway.
* **Gateway (Nodo Coordinador):** Expuesto al cliente. Recibe la llave AES, ejecuta la matemática de Shamir y distribuye los fragmentos a través de la red privada.
* **Storage Vaults (Nodos Bóveda):** Contenedores aislados sin acceso a internet público. Actúan como bóvedas ciegas ("dumb storage") para persistir los fragmentos de forma segura.

## 📂 Estructura del Repositorio

```text
shamir-storage-node/
├── client/                  # Frontend en React (Cifrado AES local)
│   ├── public/              # Assets estáticos (iconos, favicons)
│   ├── src/                 # Código fuente React (App.jsx, main.jsx, estilos)
│   ├── package.json         # Dependencias de npm
│   └── vite.config.js       # Configuración del bundler y proxy
├── src/                     # Backend API (Python)
│   ├── adapters/
│   │   ├── api.py           # Gateway y Endpoints REST (FastAPI)
│   │   └── vault.py         # Lógica y almacenamiento de Bóvedas
│   └── domain/
│       └── shamir.py        # Core criptográfico (Polinomios + Hashing)
├── tests/
│   └── test_shamir.py       # Suite de TDD (Pytest)
├── docker-compose.yml       # Orquestación de la red Zero Trust
├── Dockerfile               # Instrucciones de construcción de imagen
├── pyproject.toml           # Configuración de dependencias (uv)
└── README.md
```

## 🌐 Escenarios de Despliegue y Persistencia
El sistema está diseñado para escalar desde una prueba local hasta una infraestructura distribuida real. Dependiendo del entorno, la persistencia de los fragmentos varía:

### 1. Entorno Local (Desarrollo / Simulador)
Para pruebas en una sola computadora, el proyecto utiliza **Docker Bind Mounts**. Los 5 nodos simulados guardan sus fragmentos en una carpeta visible (`bovedas_locales/`) en el disco duro del desarrollador. Esto permite visualizar el proceso, aunque la computadora actúa como un Punto Único de Falla (SPOF) temporal.

### 2. Servidor Único (Ej: Servidor LINSI)
Al migrar el proyecto a un servidor centralizado en un laboratorio, se implementa **Defensa en Profundidad**. En lugar de carpetas visibles, se configuran **Volúmenes Gestionados de Docker**. Los fragmentos se almacenan en particiones ocultas y protegidas por los permisos estrictos del núcleo de Linux (`/var/lib/docker/volumes/`), previniendo el acceso directo incluso si un atacante vulnera la aplicación web.

### 3. Red Distribuida Multi-Clúster (Producción Real / Zero Trust)
El estado ideal de la arquitectura. El `docker-compose.yml` centralizado se divide, desplegando cada Nodo Bóveda en un servidor físico o proveedor de nube diferente. Un atacante necesitaría vulnerar infraestructuras independientes y geográficamente separadas de forma simultánea para lograr recolectar el umbral mínimo de fragmentos y comprometer una llave.

## 🚀 Instalación y Ejecución

**1. Clonar el repositorio:**
```bash
git clone [https://github.com/AlvaroMarini/LabLinsi-Shamir-Storage-node.git](https://github.com/AlvaroMarini/LabLinsi-Shamir-Storage-node.git)
cd LabLinsi-Shamir-Storage-node
```

**2. Levantar la Infraestructura Zero Trust (Backend):**
Asegúrate de tener Docker instalado y ejecutándose.
```bash
docker compose up -d --build
```
*El Gateway estará escuchando en `http://localhost:8000`. Los 5 nodos bóveda quedarán operando en la red interna aislada.*

**3. Iniciar el Cliente de Usuario (Frontend):**
En una nueva terminal, navega a la carpeta del cliente e instala las dependencias:
```bash
cd client
npm install
npm run dev
```
Accede al panel de control desde tu navegador en `http://localhost:5173`.

## 🧪 Testing y Tolerancia a Fallas
El núcleo criptográfico está validado mediante pruebas automatizadas (TDD). Para ejecutar la suite completa en el entorno backend:
```bash
# Dentro de tu entorno virtual de Python
pytest
```
**Demostración de Alta Disponibilidad:** Con el sistema en ejecución, puedes apagar intencionalmente hasta 2 nodos bóveda (`docker stop shamir-node-4 shamir-node-5`) y observar cómo el Gateway recupera exitosamente la clave AES comunicándose con los nodos sobrevivientes para alcanzar el umbral necesario.

## 🛣️ Roadmap Completado
- [x] Motor matemático criptográfico sobre Campos Finitos.
- [x] Validación de integridad de fragmentos (SHA-256).
- [x] Arquitectura de red aislada (Gateway + Vaults).
- [x] Cifrado y Descifrado local AES-256 mediante Web Crypto API.
- [x] Soporte para persistencia multi-archivo mediante inyección de UUID.
- [x] Infraestructura dockerizada con volúmenes persistentes.