# Sistema de Detección de Hernias con Inteligencia Artificial

  Sistema de Detección de Hernias es un proyecto diseñado para ayudar a los profesionales de la salud en el diagnóstico de hernias mediante el análisis de imágenes de resonancias magnéticas. Este sistema utiliza inteligencia artificial para detectar y clasificar hernias, además de ofrecer un módulo de chatbot para responder preguntas comunes.

# Tabla de Contenidos
- [Características principales](#características-principales)
- [Instalación](#instalación)
  - [Requisitos previos](#requisitos-previos)
  - [Clonar el repositorio](#clonar-el-repositorio)
  - [Crear y activar un entorno virtual](#crear-y-activar-un-entorno-virtual)
  - [Instalar las dependencias](#instalar-las-dependencias)
  - [Configurar la base de datos](#configurar-la-base-de-datos)
  - [Aplicar migraciones y crear un superusuario](#aplicar-migraciones-y-crear-un-superusuario)
  - [Configurar AWS S3](#configurar-aws-s3)
  - [Ejecutar el servidor](#ejecutar-el-servidor)
- [Flujo del Sistema](#flujo-del-sistema)
- [Guía de Usuario](#guía-de-usuario)
  - [Registro e inicio de sesión](#registro-e-inicio-de-sesión)
  - [Carga de Imágenes](#carga-de-imágenes)
  - [Visualización de Resultados](#visualización-de-resultados)
  - [Generación de Reportes en PDF](#generación-de-reportes-en-pdf)
  - [Uso del Chatbot](#uso-del-chatbot)
- [Tecnologías Utilizadas](#tecnologías-utilizadas)

# Características principales

Carga y almacenamiento seguro de imágenes: Los médicos pueden cargar imágenes de resonancias magnéticas, que se almacenan de forma segura en AWS S3.

Análisis de imágenes con IA: Las imágenes cargadas son procesadas por un modelo de IA entrenado, que clasifica las imágenes para detectar la presencia de hernias y el tipo específico.
Generación de reportes en PDF: Los resultados del análisis se pueden exportar a un archivo PDF para un mejor seguimiento.

Chatbot informativo: Responde a preguntas sobre el sistema y diagnósticos de hernias, orientado a los profesionales de la salud.

# Instalación

  # Requisitos previos
  
  Asegúrate de contar con los siguientes componentes instalados en tu sistema:

  Python 3.12.3+
  Django 4.0+
  PostgreSQL 14.13
  AWS CLI configurado para AWS S3
  Virtualenv
  Clonar el repositorio
  Clona el repositorio del proyecto a tu máquina local:
  
    git clone https://github.com/tu_usuario/proy_medical.git
    cd proy_medical
  # Crear y activar un entorno virtual
  
  Crea y activa un entorno virtual para aislar las dependencias del proyecto:
  
    python -m venv venv
    source venv/bin/activate 
  # En Windows usa 
    `venv\Scripts\activate`

# Instalar las dependencias
  
  Instala las dependencias necesarias desde el archivo requirements.txt:

    pip install -r requirements.txt
# Configurar la base de datos
  
  Configura la base de datos PostgreSQL. Ve a tu settings.py del proyecto y define las siguientes variables(agrega tu configuración de tu base de datos):
      
      DB_ENGINE=django.db.backends.postgresql
      DB_NAME=nombre_de_la_base_de_datos
      DB_USER=usuario
      DB_PASSWORD=contraseña
      DB_HOST=localhost
      DB_PORT=5432
      
# Aplicar migraciones y crear un superusuario
  Ejecuta las migraciones para crear las tablas de la base de datos y configura un superusuario para acceder al panel administrativo:

    python manage.py migrate
    python manage.py createsuperuser

# Configurar AWS S3
  Para almacenar imágenes en AWS S3, configura las credenciales en el archivo .env:
  
    AWS_ACCESS_KEY_ID=tu_access_key
    AWS_SECRET_ACCESS_KEY=tu_secret_key
    AWS_STORAGE_BUCKET_NAME=nombre_del_bucket
    
# Ejecutar el servidor
  Inicia el servidor de desarrollo de Django:

    python manage.py runserver
  El servidor estará disponible en http://127.0.0.1:8000/.

# Flujo del Sistema
  # Registro e inicio de sesión
  
  Los usuarios pueden registrarse proporcionando su correo electrónico y una contraseña.
  Una vez registrados, pueden iniciar sesión con sus credenciales para acceder a las funcionalidades del sistema.
  # Carga de Imágenes
  
  Los profesionales de la salud pueden cargar imágenes de resonancias magnéticas a través de la interfaz.
  El sistema almacena las imágenes en AWS S3 y las prepara para su análisis.
  Análisis de Imágenes y Diagnóstico
  Una vez cargadas, el modelo de IA analiza las imágenes y determina la presencia de hernias.
  El sistema también detecta donde está la hernia presente para ofrecer un diagnóstico más detallado.
# Visualización de Resultados
  
  Los resultados del análisis se presentan en una interfaz amigable para los profesionales de la salud.
# Generación de Reportes en PDF
  
  Los resultados del análisis se pueden exportar en formato PDF para archivarlos o compartirlos.
# Uso del Chatbot
  
  El chatbot permite a los usuarios hacer preguntas relacionadas con el análisis de hernias, diagnóstico y sobre cómo usar el sistema.

# Guía de Usuario
  # Registro e inicio de sesión

  Los nuevos usuarios deben registrarse con su correo electrónico y una contraseña.
  Una vez registrados, pueden iniciar sesión para acceder a todas las funcionalidades del sistema.
  
  # Carga de Imágenes
  
  Accede a la sección de carga de imágenes desde el menú principal.
  Selecciona la imagen de resonancia magnética para cargarla al sistema y espera a la confirmación.
  
  # Visualización de Resultados
  
  Los resultados del análisis se presentan visualmente junto con las probabilidades de diagnóstico.
  
  # Generación de Reportes en PDF
  
  Haz clic en la opción de generar PDF para crear un reporte de los resultados del análisis.
  
  # Uso del Chatbot
  Accede al chatbot desde la barra de navegación y realiza preguntas sobre el análisis y diagnóstico de hernias.
  
  # Tecnologías Utilizadas
  
  # Django: 
  Framework principal para el desarrollo del sistema web.
  
  # PostgreSQL:
  Base de datos para almacenar información de usuarios y resultados.
  # Scikit-learn:
  Para el modelo de análisis de imágenes y clasificación de hernias.
  # AWS S3:
  Almacenamiento seguro para las imágenes de resonancias magnéticas.
  # HTML, CSS y JavaScript:
  Para el diseño e interactividad de la interfaz.

## Video de Presentación

[![Presentación del Proyecto](https://img.youtube.com/vi/2xaNaZ9taGk/maxresdefault.jpg)](https://www.youtube.com/watch?v=2xaNaZ9taGk)
