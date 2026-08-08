# Shamir Storage Node (PoC)

> Prueba de Concepto (PoC) para un Sistema de Almacenamiento Distribuido de Alta Seguridad utilizando Criptografía de Umbral, Validación de Integridad (VSS), Cifrado AES-256 y Gestión de Identidad Federada (IAM). Desarrollado para el Laboratorio de Investigación en Sistemas de Información (LINSI) de la Universidad Tecnológica Nacional (UTN).

## Descripción del Proyecto
Este proyecto implementa una arquitectura **Zero Trust** combinada con el **Esquema de Compartición de Secretos de Shamir (Shamir's Secret Sharing)** en un entorno de red distribuido. Su objetivo es mitigar los riesgos de almacenamiento centralizado, garantizando la confidencialidad, integridad y disponibilidad de los archivos ante fallos de hardware o brechas de seguridad severas.

El flujo de protección garantiza que **los archivos originales nunca toquen los servidores**. Toda la encriptación de archivos (AES-256) ocurre localmente en el navegador del cliente mediante la *Web Crypto API*. Únicamente la clave criptográfica resultante es enviada a la red, donde el motor matemático del Gateway la divide en fragmentos distribuidos. 

Para evitar ataques de corrupción de datos, intercepción de nodos comprometidos o robo de credenciales, el sistema integra validaciones de integridad criptográfica (SHA-256) tanto para los fragmentos de datos como para la identidad del propietario.

## Marco Teórico y Referencias Académicas
El diseño arquitectónico y las defensas criptográficas de este laboratorio se fundamentan en los siguientes consensos científicos:

* **Shamir, A. (1979).** *How to Share a Secret*. Base matemática del fraccionamiento sobre campos finitos.
* **Feldman, P. (1987).** *A Verifiable Secret Sharing Scheme*. Respalda la implementación de validaciones SHA-256 para descartar nodos que envíen fragmentos corruptos.
* **Zero Trust Architecture & OAuth 2.0 / OpenID Connect.** Estándares de la industria para la delegación de autorización y microsegmentación en entornos contenerizados.

## Arquitectura del Sistema
El desarrollo sigue el patrón de **Arquitectura Hexagonal (Ports & Adapters)** y una estricta separación de responsabilidades dentro de una estructura monorepo:

* **Cliente Frontend (React + Vite):** Responsable de generar llaves AES-256, cifrar/descifrar archivos localmente y comunicarse con el Gateway de forma segura adjuntando el Token JWT. Opera en una red pública aislada detrás de un WAF (ModSecurity).
* **Identity Provider (Keycloak + PostgreSQL):** Gestor de identidad federada encargado de la autenticación de usuarios. Emite y firma matemáticamente los tokens de sesión (JWT), eliminando el uso de contraseñas o PINs en texto plano dentro de la aplicación.
* **Gateway (Nodo Coordinador / DMZ):** Desarrollado en FastAPI. Expuesto al cliente. Valida criptográficamente el JWT contra Keycloak, extrae la identidad blindada, ejecuta la matemática de Shamir y distribuye la carga a la red interna.
* **Storage Vaults (Nodos Bóveda):** 5 contenedores aislados en una red privada. Operan motores de base de datos **SQLite** independientes para persistir los fragmentos. Desconocen la naturaleza del dato original y la identidad real del usuario, almacenando únicamente un hash SHA-256 irreversible de la identidad.

## Estructura del Repositorio

```text
shamir-storage-node/
├── backend/                 # Backend API y Lógica Central (Python / FastAPI)
│   ├── src/                 # Endpoints REST, Vaults y Core Criptográfico
│   ├── tests/               # Suite de pruebas unitarias (Pytest)
│   ├── Dockerfile           # Instrucciones de construcción del backend
│   └── pyproject.toml       # Dependencias
├── client/                  # Frontend interactivo (React)
│   ├── src/                 # Lógica de interfaz (Cifrado AES local)
│   ├── Dockerfile           # Compilación estática y proxy Nginx
│   └── nginx.conf           # Configuración de enrutamiento
├── bovedas_locales/         # Persistencia de datos SQLite de los nodos
├── keycloak_data/           # Persistencia de la base de datos IAM (PostgreSQL)
├── docker-compose.yml       # Orquestación de clúster, WAF y redes (public_net / private_net)
└── README.md                # Documentación del proyecto
```

## Tolerancia a Fallas y Manejo Granular de Errores
El sistema está diseñado para soportar la caída de nodos sin pérdida de datos. Con el clúster en ejecución, es posible detener contenedores intencionalmente (ej: Nodo 4 y Nodo 5). El Gateway procesará las respuestas y ejecutará diagnósticos inteligentes:
* **Error 403 (Acceso Denegado):** Identifica si un usuario intenta reconstruir un archivo utilizando una identidad criptográfica que no corresponde a los fragmentos almacenados.
* **Error 503 (Red Inestable):** Detecta cuando la cantidad de bóvedas caídas impide alcanzar el umbral matemático necesario para la interpolación de Lagrange.

## Instalación y Ejecución

**1. Clonar el repositorio:**
```bash
git clone [https://github.com/AlvaroMarini/LabLinsi-Shamir-Storage-node.git](https://github.com/AlvaroMarini/LabLinsi-Shamir-Storage-node.git)
cd LabLinsi-Shamir-Storage-node
```

**2. Configurar Credenciales:**
Crear un archivo `.env` en la raíz del proyecto con el siguiente formato:
```env
PUBLIC_API_KEY=tu_clave_publica
INTERNAL_CLUSTER_KEY=tu_clave_privada_interna
```

**3. Levantar la Infraestructura Completa:**
```bash
docker compose up -d --build
```
*El sistema levantará automáticamente las redes segmentadas, el WAF, el Frontend, Keycloak con su BD, el Gateway DMZ y las 5 Bóvedas aisladas.*

**4. Configuración del Reino (Primera ejecución):**
* Acceder a `http://localhost:8080/admin` (admin/admin).
* Crear el Realm `shamir-realm`.
* Registrar un cliente `shamir-react-client`.
* Dar de alta a los usuarios del laboratorio.

**5. Acceso a la Plataforma:**
Ingresar a la interfaz gráfica protegida a través de `http://localhost:5173`.

