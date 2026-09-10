from pathlib import Path
from datetime import timedelta
import os
from dotenv import load_dotenv
import dj_database_url

BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")

DEBUG = os.getenv("DEBUG", "True").lower() == "true"
SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret-key-change-me")

ALLOWED_HOSTS = [
    h.strip()
    for h in os.getenv(
        "ALLOWED_HOSTS",
        "localhost,127.0.0.1,.localhost"
    ).split(",")
    if h.strip()
]

BASE_DOMAIN = os.getenv("BASE_DOMAIN", "school.bewiseinnovation.com").strip().lower()

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",

    "corsheaders",
    "rest_framework",
    "drf_spectacular",

    "apps.core",
    "apps.accounts",
    "apps.tenants",
    "apps.academics",
    "apps.people",
    "apps.teaching",
    "apps.assessments",
    "apps.report_cards",
    "apps.finance",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "corsheaders.middleware.CorsMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",

    "apps.tenants.middleware.TenantResolutionMiddleware",
]

ROOT_URLCONF = "config.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "config.wsgi.application"

DATABASES = {
    "default": dj_database_url.config(
        default=f"sqlite:///{BASE_DIR / 'db.sqlite3'}",
        conn_max_age=60,
    )
}

AUTH_PASSWORD_VALIDATORS = []

LANGUAGE_CODE = "fr-fr"
TIME_ZONE = "Africa/Douala"
USE_I18N = True
USE_TZ = True

STATIC_URL = "/static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
STORAGES = {
    "default": {"BACKEND": "django.core.files.storage.FileSystemStorage"},
    "staticfiles": {"BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage"},
}
MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

AUTH_USER_MODEL = "accounts.User"

REST_FRAMEWORK = {
    # Important: DRF reserves ?format= for renderer negotiation by default.
    # We disable that override because file exports use their own format parameter.
    "URL_FORMAT_OVERRIDE": None,
    "DEFAULT_SCHEMA_CLASS": "drf_spectacular.openapi.AutoSchema",
    "DEFAULT_AUTHENTICATION_CLASSES": (
        "rest_framework_simplejwt.authentication.JWTAuthentication",
    ),
    "DEFAULT_PERMISSION_CLASSES": (
        "rest_framework.permissions.IsAuthenticated",
    ),
}

CORS_ALLOW_ALL_ORIGINS = (
    os.getenv("CORS_ALLOW_ALL_ORIGINS", "True").lower() == "true"
)

CORS_ALLOW_HEADERS = [
    "accept",
    "authorization",
    "content-type",
    "origin",
    "user-agent",
    "x-csrftoken",
    "x-requested-with",
    "x-tenant-slug",
]

CSRF_TRUSTED_ORIGINS = [
    value.strip()
    for value in os.getenv("CSRF_TRUSTED_ORIGINS", "").split(",")
    if value.strip()
]
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
SESSION_COOKIE_SECURE = not DEBUG
CSRF_COOKIE_SECURE = not DEBUG


SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": timedelta(minutes=15),
    "REFRESH_TOKEN_LIFETIME": timedelta(days=7),
    "ROTATE_REFRESH_TOKENS": False,
    "BLACKLIST_AFTER_ROTATION": False,
    "UPDATE_LAST_LOGIN": True,
}


# OpenAPI / Swagger documentation.
SPECTACULAR_SETTINGS = {
    "TITLE": "BE WISE School API",
    "DESCRIPTION": (
        "API REST multi-tenant de BE WISE School. "
        "En développement local, utilisez X-Tenant-Slug si nécessaire."
    ),
    "VERSION": "0.7.0",
    "SERVE_INCLUDE_SCHEMA": False,
    "COMPONENT_SPLIT_REQUEST": True,
    "SCHEMA_PATH_PREFIX": r"/api",
    "POSTPROCESSING_HOOKS": [
        "apps.core.schema_hooks.add_tenant_header_parameter",
    ],
    "TAGS": [
        {"name": "Authentication", "description": "Connexion et renouvellement JWT."},
        {"name": "Tenants", "description": "Établissement et configuration tenant."},
        {"name": "Academics", "description": "Structure académique, matières et notation."},
        {"name": "People", "description": "Élèves, enseignants, parents et inscriptions."},
        {"name": "Teaching", "description": "Affectations pédagogiques, responsables de classe et accès enseignants."},
        {"name": "Assessments", "description": "Évaluations, saisie sécurisée des notes, validation et résultats."},
        {"name": "Report Cards", "description": "Exploration des résultats, bulletins PDF, versions et vérification publique."},
        {"name": "Finance", "description": "Plans de pension, tranches, comptes élèves, paiements et reçus."},
    ],
}


REPORT_CARD_VERIFY_BASE_URL = os.getenv("REPORT_CARD_VERIFY_BASE_URL", "").strip()
