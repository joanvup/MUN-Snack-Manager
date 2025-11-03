# MUN Snack Manager - Aplicación de Control de Meriendas

Esta es una aplicación web Flask diseñada para gestionar y controlar la entrega de meriendas en un evento académico tipo Modelo de Naciones Unidas (MUN).

## Características

- **Gestión de Datos**: Administra participantes, comités, países e instituciones.
- **Control por QR**: Valida a los participantes y registra la entrega de meriendas mediante el escaneo de un código QR.
- **Roles de Usuario**:
    - **Administrador**: Acceso total al sistema (CRUD, configuración, reportes, importación de datos).
    - **Operador**: Acceso exclusivo a la función de escaneo de QR.
- **Importación Masiva**: Carga de datos inicial a través de un archivo Excel (`.xlsx`).
- **Diseño Responsivo**: Interfaz moderna y adaptable creada con TailwindCSS.

## Requisitos Técnicos

- **Backend**: Python, Flask
- **Frontend**: HTML, TailwindCSS, JavaScript
- **Base de Datos**: SQLite (fácil de cambiar a MySQL en la configuración)
- **Librerías Principales**: Flask-SQLAlchemy, Flask-Login, pandas.

## Instalación y Ejecución Local

Sigue estos pasos para poner en marcha la aplicación en tu entorno local.

### 1. Prerrequisitos

- Tener Python 3.8 o superior instalado.
- Tener `pip` (el gestor de paquetes de Python) instalado.

### 2. Clonar el Repositorio

```bash
git clone <URL_DEL_REPOSITORIO>
cd MUN-Snack-Manager