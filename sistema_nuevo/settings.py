




import sys
import codecs
sys.stdout = codecs.getwriter("utf-8")(sys.stdout.detach())
"""
Django settings for sistema_nuevo project.

Generated by 'django-admin startproject' using Django 5.1.4.

For more information on this file, see
https://docs.djangoproject.com/en/5.1/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/5.1/ref/settings/
"""
from django.utils.html import format_html


from pathlib import Path
import os

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/5.1/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = 'django-insecure-4$)hh34d&^v#l$t0mk7a4uv(t192^=^t@gt_7tavn^=51fy1s6'

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

ALLOWED_HOSTS = []


# Application definition

INSTALLED_APPS = [
    # Aplicaciones de Django
    'jazzmin',
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',

    # Extensiones
    'django_extensions',

    # Aplicaciones personalizadas
    'registro_vuelos',
]

# Detecta si estamos en Render o localmente
IS_RENDER = os.environ.get('IS_RENDER', 'False').lower() == 'true'

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    # Aquí se inserta whitenoise solo en producción
    'whitenoise.middleware.WhiteNoiseMiddleware' if IS_RENDER else None,
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

# Eliminar posibles valores `None` en la lista (por si IS_RENDER es False)
MIDDLEWARE = [m for m in MIDDLEWARE if m is not None]

# Configuración para servir archivos estáticos en producción
if IS_RENDER:
    STATICFILES_STORAGE = "whitenoise.storage.CompressedManifestStaticFilesStorage"

ROOT_URLCONF = 'sistema_nuevo.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'sistema_nuevo.wsgi.application'


# Database
# https://docs.djangoproject.com/en/5.1/ref/settings/#databases


if IS_RENDER:
    # Configuración para Render (usando variables de entorno)
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.postgresql',
            'NAME': os.environ.get('DB_NAME', 'arenas'),
            'USER': os.environ.get('DB_USER', 'vuelo_admin'),
            'PASSWORD': os.environ.get('DB_PASSWORD', 'foAE0tjSDPGtNpoAW24UGis6caUmxmcm'),
            'HOST': os.environ.get('DB_HOST', 'dpg-cv3lcqlsvqrc73ec8tpg-a'),
            'PORT': os.environ.get('DB_PORT', '5432'),
        }
    }
    # Asegurar que ALLOWED_HOSTS no tenga espacios extra o errores
    ALLOWED_HOSTS = os.environ.get("ALLOWED_HOSTS", "sistema-arenas.onrender.com").split(",")
    
    # Eliminar espacios en blanco y evitar problemas si hay una lista de hosts
    ALLOWED_HOSTS = [host.strip() for host in ALLOWED_HOSTS if host.strip()]
else:
    # Configuración para local (usando localhost o tu base local)
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.postgresql',
            'NAME': 'arenas',
            'USER': 'vuelo_admin',
            'PASSWORD': 'HCAviones*1705',  # O tu contraseña local
            'HOST': '127.0.0.1',
            'PORT': '5432',
        }
    }
    ALLOWED_HOSTS = ["127.0.0.1", "localhost"]


# Password validation
# https://docs.djangoproject.com/en/5.1/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]


# Internationalization
# https://docs.djangoproject.com/en/5.1/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_TZ = True

import os


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/5.1/howto/static-files/

STATIC_URL = 'static/'
STATIC_ROOT = os.path.join(BASE_DIR, "staticfiles")

# Agregar la ubicación de archivos estáticos personalizados
if not IS_RENDER:
    STATICFILES_DIRS = [
        os.path.join(BASE_DIR, 'registro_vuelos', 'static'),
    ]

# Default primary key field type
# https://docs.djangoproject.com/en/5.1/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Configuraciones para HTTPS y seguridad
# SECURE_SSL_REDIRECT = True
# CSRF_COOKIE_SECURE = True
# SESSION_COOKIE_SECURE = True


# Ruta donde se guardarán los logs
LOG_DIR = os.path.join(BASE_DIR, 'logs')
os.makedirs(LOG_DIR, exist_ok=True)  # 🔹 Asegura que la carpeta existe

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} [{filename}:{lineno}] {message}',
            'style': '{',
        },
        'simple': {
            'format': '{levelname} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'file_django': {
            'level': 'DEBUG',
            'class': 'logging.FileHandler',
            'filename': os.path.join(LOG_DIR, 'django.log'),  # 🔹 Logs de Django
            'formatter': 'verbose',
        },
        'file_arenas': {
            'level': 'DEBUG',
            'class': 'logging.FileHandler',
            'filename': os.path.join(LOG_DIR, 'arenas.log'),  # 🔹 Logs de ARENAS
            'formatter': 'verbose',
        },
    },
    'loggers': {
        'django': {
            'handlers': ['file_django'],
            'level': 'DEBUG',
            'propagate': True,
        },
        'arenas': {  # 🔹 Logger específico para ARENAS
            'handlers': ['file_arenas'],
            'level': 'DEBUG',
            'propagate': False,
        },
    },
}

# Configuración de Jazzmin
JAZZMIN_SETTINGS = {
    # Configuración de título y marca
    "site_title": "Arenas Airlines Admin",
    "site_header": "Arenas Airlines",
    "site_brand": "Sistema de Gestión",
    "site_logo": None,
    "login_logo": None,
    "welcome_sign": "Bienvenido al Sistema de Gestión Arenas Airlines",
    
    # Configuración del menú principal reorganizado
    "menu": [
        # Configuración del Sistema
        {
            "name": "Configuración del Sistema",
            "icon": "fas fa-cogs",
            "models": [
                "registro_vuelos.avion",
                "registro_vuelos.empleado", 
                "registro_vuelos.cliente",
                "registro_vuelos.trayectocosto",
                "registro_vuelos.seriefactura",
                "registro_vuelos.destino",
                "registro_vuelos.moneda"
            ]
        },
        # Operaciones de Vuelo
        {
            "name": "Vuelos",
            "icon": "fas fa-plane-departure",
            "models": [
                "registro_vuelos.vuelo", 
                "registro_vuelos.tramovuelo"
            ]
        },
        # Gestión de Empleados y Pagos
        {
            "name": "Gestión de Empleados",
            "icon": "fas fa-users",
            "models": [
                "registro_vuelos.pagoempleado", 
                "registro_vuelos.saldoempleado"
            ]
        },
        # Inventario de Oro
        {
            "name": "Inventario de Oro",
            "icon": "fas fa-coins",
            "models": [
                "registro_vuelos.inventariooro",
                "registro_vuelos.barra"
            ]
        },
        # Finanzas
        {
            "name": "Finanzas",
            "icon": "fas fa-money-bill-wave",
            "models": [
                "registro_vuelos.cajachica",
                "registro_vuelos.movimientocaja",
                "registro_vuelos.cuentagasto",
                "registro_vuelos.movimientogasto"
            ]
        },
        # Clientes y Transacciones
        {
            "name": "Transacciones con Clientes",
            "icon": "fas fa-handshake",
            "models": [
                "registro_vuelos.historialtransacciones"
            ]
        },
        # Administración del sistema
        {
            "name": "Administración",
            "icon": "fas fa-users-cog",
            "models": [
                "auth.user",
                "auth.group",
            ]
        },
    ],
    
    # Iconos para modelos individuales
    "icons": {
        # Configuración
        "registro_vuelos.avion": "fas fa-plane",
        "registro_vuelos.empleado": "fas fa-user-tie",
        "registro_vuelos.cliente": "fas fa-user-friends",
        "registro_vuelos.trayectocosto": "fas fa-money-check",
        "registro_vuelos.seriefactura": "fas fa-file-invoice",
        "registro_vuelos.destino": "fas fa-map-marker-alt",
        "registro_vuelos.moneda": "fas fa-dollar-sign",
        
        # Vuelos
        "registro_vuelos.vuelo": "fas fa-route",
        "registro_vuelos.tramovuelo": "fas fa-map-signs",
        
        # Empleados
        "registro_vuelos.pagoempleado": "fas fa-hand-holding-usd",
        "registro_vuelos.saldoempleado": "fas fa-balance-scale",
        
        # Inventario
        "registro_vuelos.inventariooro": "fas fa-coins",
        "registro_vuelos.barra": "fas fa-cube",
        
        # Finanzas
        "registro_vuelos.cajachica": "fas fa-cash-register",
        "registro_vuelos.movimientocaja": "fas fa-exchange-alt",
        "registro_vuelos.cuentagasto": "fas fa-file-invoice-dollar",
        "registro_vuelos.movimientogasto": "fas fa-receipt",
        
        # Transacciones
        "registro_vuelos.historialtransacciones": "fas fa-history",
    },
    
    # Otras configuraciones (se mantienen igual)
    "show_ui_builder": True,
    "navigation_expanded": True,
    "custom_links": {},
    "changeform_format": "horizontal_tabs",
    "custom_css": None,
    "custom_js": None,
}

# Iconos para los grupos de usuario
JAZZMIN_UI_TWEAKS = {
    "navbar_small_text": False,
    "footer_small_text": False,
    "body_small_text": False,
    "brand_small_text": False,
    "brand_colour": "navbar-primary",
    "accent": "accent-primary",
    "navbar": "navbar-dark",
    "no_navbar_border": False,
    "navbar_fixed": True,
    "layout_boxed": False,
    "footer_fixed": False,
    "sidebar_fixed": True,
    "sidebar": "sidebar-dark-primary",
    "sidebar_nav_small_text": False,
    "sidebar_disable_expand": False,
    "sidebar_nav_child_indent": True,
    "sidebar_nav_compact_style": False,
    "sidebar_nav_legacy_style": False,
    "sidebar_nav_flat_style": False,
    "theme": "default",
    "dark_mode_theme": None,
    "button_classes": {
        "primary": "btn-primary",
        "secondary": "btn-secondary",
        "info": "btn-info",
        "warning": "btn-warning",
        "danger": "btn-danger",
        "success": "btn-success"
    }
}
