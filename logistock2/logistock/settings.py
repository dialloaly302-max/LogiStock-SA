# Fichier : logistock\settings.py
import os
from pathlib import Path

from dotenv import load_dotenv

# Dossier racine du projet (celui qui contient manage.py)
BASE_DIR = Path(__file__).resolve().parent.parent

# Lecture du fichier .env (secrets hors du code)
load_dotenv(BASE_DIR / ".env")

SECRET_KEY = os.getenv("SECRET_KEY")
DEBUG = os.getenv("DEBUG", "False") == "True"
ALLOWED_HOSTS = [
    h.strip()
    for h in os.getenv("ALLOWED_HOSTS", ",localhost,127.0.0.1,10.196.217.169").split(",")
    if h.strip()
]

# Applications Django + nos applications
INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "django.contrib.humanize",  # pour afficher 59 000 dans les templates
    # Nos applications
    "comptes",
    "catalogue",
    "stock",
    "clients",
    "ventes",
    "tableau_bord",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "logistock.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
                "comptes.context_processors.menu",
            ],
        },
    },
]

WSGI_APPLICATION = "logistock.wsgi.application"

# Base de données MariaDB (XAMPP) : valeurs lues dans .env
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.mysql",
        "NAME": os.getenv("DB_NAME", "logistock"),
        "USER": os.getenv("DB_USER", "root"),
        "PASSWORD": os.getenv("DB_PASSWORD", ""),
        "HOST": os.getenv("DB_HOST", "127.0.0.1"),
        "PORT": os.getenv("DB_PORT", "3306"),
        "OPTIONS": {"charset": "utf8mb4"},
    }
}

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

# Langue, fuseau horaire et format des nombres
LANGUAGE_CODE = "fr"
TIME_ZONE = "Africa/Bamako"
USE_I18N = True
USE_TZ = True
USE_THOUSAND_SEPARATOR = True  # 59000 devient 59 000

STATIC_URL = "static/"
STATICFILES_DIRS = [BASE_DIR / "static"]

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
# Notre table utilisateur (au lieu de celle de Django)
AUTH_USER_MODEL = "comptes.Utilisateur"

# Connexion et déconnexion
LOGIN_URL = "connexion"
LOGIN_REDIRECT_URL = "accueil"
LOGOUT_REDIRECT_URL = "connexion"

# Blocage après des échecs de connexion
MAX_ECHECS = 5
DUREE_BLOCAGE_MINUTES = 15

# Tests : créer aussi les tables non gérées dans la base temporaire
TEST_RUNNER = "logistock.test_runner.TestRunnerTablesExistantes"
# --- Production : actif seulement si DJANGO_ENV=production (ton PC n'est pas touché) ---
EN_PRODUCTION = os.getenv("DJANGO_ENV") == "production"
STATIC_ROOT = BASE_DIR / "staticfiles"

if EN_PRODUCTION:
    DEBUG = False
    SECRET_KEY = os.environ["DJANGO_SECRET_KEY"]
    ALLOWED_HOSTS = os.environ["DJANGO_ALLOWED_HOSTS"].split(",")
    CSRF_TRUSTED_ORIGINS = ["https://" + h for h in ALLOWED_HOSTS]
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
    SECURE_SSL_REDIRECT = True
