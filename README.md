# Shamir Storage Node (PoC)

> Prueba de Concepto (PoC) para un Sistema de Almacenamiento Distribuido de Alta Seguridad utilizando Criptografía de Umbral, Validación de Integridad (VSS), Cifrado AES-256 y Gestión de Identidad Ciega. Desarrollado para el Laboratorio de Investigación en Sistemas de Información (LINSI).

## Descripción del Proyecto
Este proyecto implementa una arquitectura **Zero Trust** combinada con el **Esquema de Compartición de Secretos de Shamir (Shamir's Secret Sharing)** en un entorno de red distribuido. Su objetivo es mitigar los riesgos de almacenamiento centralizado, garantizando la confidencialidad, integridad y disponibilidad de los archivos ante fallos de hardware o brechas de seguridad severas.

El flujo de protección garantiza que **los archivos originales nunca toquen los servidores**. Toda la encriptación de archivos (AES-256) ocurre localmente en el navegador del cliente mediante la *Web Crypto API*. Únicamente la clave criptográfica resultante es enviada a la red, donde el motor matemático del Gateway la divide en fragmentos distribuidos. 

Para evitar ataques de corrupción de datos, intercepción de nodos comprometidos o robo de credenciales, el sistema integra validaciones de integridad criptográfica (SHA-256) tanto para los fragmentos de datos como para la identidad del propietario.

## Marco Teórico y Referencias Académicas
El diseño arquitectónico y las defensas criptográficas de este laboratorio se fundamentan en los siguientes consensos científicos:

* **Shamir, A. (1979).** *How to Share a Secret*. Publicado en Communications of the ACM. Base matemática del fraccionamiento sobre campos finitos.
* **Feldman, P. (1987).** *A Verifiable Secret Sharing Scheme*. Publicado en IEEE FOCS. Respalda la implementación de validaciones SHA-256 para descartar nodos que envíen fragmentos corruptos.
* **Zero Trust Architecture.** Basado en lineamientos de microsegmentación en entornos contenerizados (ACM SIGCOMM).

## Arquitectura del Sistema
El desarrollo sigue el patrón de **Arquitectura Hexagonal (Ports & Adapters)** y una estricta separación de responsabilidades:

* **Cliente Frontend (React/Vite):** Responsable de generar llaves AES-256, cifrar/descifrar archivos localmente y comunicarse con el Gateway de forma segura.
* **Gateway (Nodo Coordinador):** Expuesto al cliente. Recibe la llave AES, aplica funciones de hashing unidireccional a las credenciales de identidad, ejecuta la matemática de Shamir y distribuye la carga.
* **Storage Vaults (Nodos Bóveda):** Contenedores aislados en una red privada. Operan motores de base de datos **SQLite** independientes para persistir los fragmentos. Desconocen la naturaleza del dato original y la identidad real del usuario.

### Capa de Identidad Ciega (Blind IAM)
La autenticación de propiedad de los archivos se realiza mediante un PIN o identificador de usuario. Para mantener el modelo Zero Trust y evitar vulnerabilidades de credenciales en texto plano en la base de datos, el Gateway aplica un hash SHA-256 sobre el identificador antes de enviarlo a la red de nodos. Las bóvedas almacenan y validan únicamente este hash, haciendo matemáticamente imposible la ingeniería inversa por parte de un atacante que logre vulnerar el almacenamiento físico.

## Estructura del Repositorio

```text
shamir-storage-node/
├── client/                  # Frontend interactivo (Cifrado AES local)
│   ├── public/              # Assets estáticos
│   ├── src/                 # Lógica de interfaz y Drag & Drop
│   └── vite.config.js       # Configuración del bundler y proxy de red
├── src/                     # Backend API (Python)
│   ├── adapters/
│   │   ├── api.py           # Gateway, IAM Hashing y Endpoints REST (FastAPI)
│   │   └── vault.py         # Lógica de Bóvedas y motor relacional SQLite
│   └── domain/
│       └── shamir.py        # Core criptográfico (Polinomios + Verificabilidad)
├── tests/
│   └── test_shamir.py       # Suite de pruebas unitarias (Pytest)
├── docker-compose.yml       # Orquestación de clúster local
├── Dockerfile               # Instrucciones de construcción de imagen
└── pyproject.toml           # Configuración de dependencias
```

## Escenarios de Despliegue y Persistencia

### 1. Entorno Local (Desarrollo / Simulador)
Para pruebas en una computadora de escritorio, el proyecto utiliza **Docker Bind Mounts**. Las bases de datos SQLite de los 5 nodos simulados se exponen en una carpeta local (`bovedas_locales/`). Esto facilita la depuración y visualización educativa.

### 2. Servidor Único (Despliegue Centralizado - LINSI)
Al migrar el proyecto a una máquina virtual en un entorno de laboratorio, se implementa **Defensa en Profundidad**. Las bases de datos SQLite operan dentro de **Volúmenes Gestionados de Docker**, almacenados en particiones protegidas por los permisos estrictos del núcleo de Linux (`/var/lib/docker/volumes/`), previniendo el acceso no autorizado al disco físico.

### 3. Red Distribuida Multi-Clúster (Producción Real)
El estado ideal de la arquitectura. El clúster se desacopla, desplegando cada Nodo Bóveda en infraestructuras físicas independientes. Un atacante necesitaría vulnerar servidores geográficamente separados de forma simultánea para recolectar el umbral mínimo de fragmentos.

## Instalación y Ejecución

**1. Clonar el repositorio:**
```bash
git clone [https://github.com/AlvaroMarini/LabLinsi-Shamir-Storage-node.git](https://github.com/AlvaroMarini/LabLinsi-Shamir-Storage-node.git)
cd LabLinsi-Shamir-Storage-node
```

**2. Levantar la Infraestructura (Backend):**
```bash
docker compose up -d --build
```
*El Gateway estará escuchando en `http://localhost:8000`. Los nodos operarán en su propia red interna.*

**3. Iniciar el Cliente de Usuario (Frontend):**
```bash
cd client
npm install
npm run dev
```
Acceso a la interfaz gráfica: `http://localhost:5173`.

## Tolerancia a Fallas
El sistema está diseñado para soportar la caída de nodos sin pérdida de datos. Con el clúster en ejecución, es posible detener contenedores intencionalmente (ej: `docker stop shamir-node-4 shamir-node-5`). El Gateway procesará un timeout controlado y recuperará exitosamente la clave consultando exclusivamente a los nodos sobrevivientes que alcancen el umbral establecido.

## Roadmap Completado
- [x] Motor matemático criptográfico sobre Campos Finitos.
- [x] Validación de integridad de fragmentos (VSS).
- [x] Arquitectura de red aislada (Gateway + Vaults).
- [x] Cifrado y Descifrado local AES-256 mediante Web Crypto API.
- [x] Interfaz de usuario interactiva con soporte Drag & Drop.
- [x] Persistencia relacional distribuida mediante motores SQLite independientes.
- [x] Capa de Identidad y Accesos (IAM) aislada mediante hashing unidireccional.