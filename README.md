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
El desarrollo sigue el patrón de **Arquitectura Hexagonal (Ports & Adapters)** y una estricta separación de responsabilidades dentro de una estructura monorepo:

* **Cliente Frontend (React + Nginx):** Responsable de generar llaves AES-256, cifrar/descifrar archivos localmente y comunicarse con el Gateway de forma segura. Opera en una red pública aislada.
* **Gateway (Nodo Coordinador / DMZ):** Expuesto al cliente. Recibe la llave AES, aplica funciones de hashing unidireccional a las credenciales de identidad, ejecuta la matemática de Shamir y distribuye la carga a la red interna.
* **Storage Vaults (Nodos Bóveda):** Contenedores aislados en una red privada. Operan motores de base de datos **SQLite** independientes para persistir los fragmentos. Desconocen la naturaleza del dato original y la identidad real del usuario.

### Capa de Identidad Ciega y Segmentación de Llaves (IAM)
La arquitectura implementa **Segmentación de Credenciales por Red**. El Frontend utiliza una llave de acceso pública para comunicarse con el Gateway, mientras que el Gateway utiliza una llave de clúster interna de alto privilegio para comunicarse con las bóvedas. 

Adicionalmente, la autenticación de propiedad de los archivos se realiza mediante un PIN. El Gateway aplica un hash SHA-256 sobre este identificador antes de enviarlo a la red interna. Las bóvedas almacenan y validan únicamente este hash, haciendo matemáticamente imposible la ingeniería inversa.

## Estructura del Repositorio

```text
shamir-storage-node/
├── backend/                 # Backend API y Lógica Central (Python)
│   ├── src/                 # Endpoints REST (FastAPI), Vaults y Core Criptográfico
│   ├── tests/               # Suite de pruebas unitarias (Pytest)
│   ├── Dockerfile           # Instrucciones de construcción del backend
│   └── pyproject.toml       # Dependencias
├── client/                  # Frontend interactivo (React)
│   ├── public/              # Assets estáticos
│   ├── src/                 # Lógica de interfaz (Cifrado AES local)
│   ├── Dockerfile           # Compilación estática y proxy Nginx
│   └── nginx.conf           # Configuración de enrutamiento
├── bovedas_locales/         # Persistencia de datos SQLite (Bind Mounts)
├── docker-compose.yml       # Orquestación de clúster y redes (public_net / private_net)
└── README.md                # Documentación del proyecto
```

## Escenarios de Despliegue y Persistencia

### 1. Entorno Local (Desarrollo / Simulador)
Para pruebas en una computadora de escritorio, el proyecto utiliza **Docker Bind Mounts**. Las bases de datos SQLite de los 5 nodos simulados se exponen en la carpeta local `bovedas_locales/`. Esto facilita la depuración y visualización educativa.

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
*El sistema levantará automáticamente las redes segmentadas, el proxy Nginx en el puerto 5173, el Gateway DMZ y las 5 Bóvedas aisladas.*

**4. Acceso:**
Ingresar a la interfaz gráfica a través de `http://localhost:5173`.

## Tolerancia a Fallas
El sistema está diseñado para soportar la caída de nodos sin pérdida de datos. Con el clúster en ejecución, es posible detener contenedores intencionalmente (ej: `docker stop shamir-node-4 shamir-node-5`). El Gateway procesará un timeout controlado y recuperará exitosamente la clave consultando exclusivamente a los nodos sobrevivientes que alcancen el umbral establecido.