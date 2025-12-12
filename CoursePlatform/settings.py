"""
Django settings for IlmSpace project.

Production-ready configuration with environment variable support.
"""
import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# =============================================================================
# CORE SETTINGS
# =============================================================================

SECRET_KEY = os.getenv(
    'SECRET_KEY',
    'django-insecure-dev-only-change-in-production'
)

DEBUG = os.getenv('DEBUG', 'False').lower() in ('true', '1', 'yes')

ALLOWED_HOSTS = [
    host.strip()
    for host in os.getenv('ALLOWED_HOSTS', 'localhost,127.0.0.1').split(',')
    if host.strip()
]

# Add ngrok support for development
if DEBUG:
    ALLOWED_HOSTS.extend(['.ngrok-free.app', '.ngrok.io'])
    
    # Trust all allowed hosts for CSRF
    CSRF_TRUSTED_ORIGINS = [
        'https://*.ngrok-free.app',
        'https://*.ngrok.io',
        'http://localhost:8000',
        'http://127.0.0.1:8000',
        'http://0.0.0.0:8000',
    ]
    
    # Add any other allowed hosts to trusted origins
    for host in ALLOWED_HOSTS:
        if '*' not in host and not host.startswith('.'):
            CSRF_TRUSTED_ORIGINS.append(f'http://{host}:8000')
            CSRF_TRUSTED_ORIGINS.append(f'https://{host}')

# =============================================================================
# APPLICATION DEFINITION
# =============================================================================

INSTALLED_APPS = [
    # Admin theme (must be before django.contrib.admin)
    'jazzmin',
    
    # Django core apps
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.sites',
    
    # Third-party apps
    'allauth',
    'allauth.account',
    'allauth.socialaccount',
    'allauth.socialaccount.providers.google',
    
    # Project apps
    'users.apps.UsersConfig',
    'authors.apps.AuthorsConfig',
    'students.apps.StudentsConfig',
    'courses.apps.CoursesConfig',
    'payments.apps.PaymentsConfig',
    'moderation.apps.ModerationConfig',
]

# Add debug toolbar in development
if DEBUG:
    try:
        import debug_toolbar  # noqa: F401
        INSTALLED_APPS.append('debug_toolbar')
    except ImportError:
        pass

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',  # Serve static files
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'allauth.account.middleware.AccountMiddleware',
]

# Add debug toolbar middleware in development
if DEBUG:
    try:
        import debug_toolbar  # noqa: F401
        MIDDLEWARE.insert(0, 'debug_toolbar.middleware.DebugToolbarMiddleware')
        INTERNAL_IPS = ['127.0.0.1']
    except ImportError:
        pass

ROOT_URLCONF = 'CoursePlatform.urls'

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

WSGI_APPLICATION = 'CoursePlatform.wsgi.application'

# =============================================================================
# DATABASE
# =============================================================================

# Default SQLite for development
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

# Use PostgreSQL in production if DATABASE_URL is set
DATABASE_URL = os.getenv('DATABASE_URL')
if DATABASE_URL and not DEBUG:
    import dj_database_url
    DATABASES['default'] = dj_database_url.parse(DATABASE_URL)

# =============================================================================
# AUTHENTICATION
# =============================================================================

AUTH_USER_MODEL = 'users.User'

AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

LOGIN_URL = '/login/'
LOGIN_REDIRECT_URL = '/'
LOGOUT_REDIRECT_URL = '/'

# =============================================================================
# INTERNATIONALIZATION
# =============================================================================

LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'Asia/Tashkent'
USE_I18N = True
USE_TZ = True

# =============================================================================
# STATIC & MEDIA FILES
# =============================================================================

STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'
STATICFILES_DIRS = [BASE_DIR / 'static']

# WhiteNoise for serving static files in production
# Use CompressedManifestStaticFilesStorage for hashed filenames and compression
if DEBUG:
    STATICFILES_STORAGE = 'django.contrib.staticfiles.storage.StaticFilesStorage'
else:
    STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

# =============================================================================
# SECURITY SETTINGS (Production)
# =============================================================================

if not DEBUG:
    # HTTPS settings - disable SSL redirect if not using HTTPS
    SECURE_SSL_REDIRECT = os.getenv('SECURE_SSL_REDIRECT', 'False').lower() in ('true', '1', 'yes')
    SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
    
    # Cookie settings - only secure if using HTTPS
    SESSION_COOKIE_SECURE = SECURE_SSL_REDIRECT
    CSRF_COOKIE_SECURE = SECURE_SSL_REDIRECT
    
    # Security headers
    SECURE_BROWSER_XSS_FILTER = True
    SECURE_CONTENT_TYPE_NOSNIFF = True
    X_FRAME_OPTIONS = 'SAMEORIGIN'  # Allow iframes from same origin
    
    # HSTS settings - only enable if using HTTPS
    if SECURE_SSL_REDIRECT:
        SECURE_HSTS_SECONDS = 31536000  # 1 year
        SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_PRELOAD = True

# =============================================================================
# DEFAULT AUTO FIELD
# =============================================================================

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# =============================================================================
# LOGGING
# =============================================================================

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {process:d} {thread:d} {message}',
            'style': '{',
        },
        'simple': {
            'format': '{levelname} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'simple',
        },
        'file': {
            'class': 'logging.FileHandler',
            'filename': BASE_DIR / 'logs' / 'django.log',
            'formatter': 'verbose',
        },
    },
    'root': {
        'handlers': ['console'],
        'level': 'INFO',
    },
    'loggers': {
        'django': {
            'handlers': ['console'],
            'level': os.getenv('DJANGO_LOG_LEVEL', 'INFO'),
            'propagate': False,
        },
    },
}

# Create logs directory if it doesn't exist
(BASE_DIR / 'logs').mkdir(exist_ok=True)

# =============================================================================
# JAZZMIN ADMIN CONFIGURATION
# =============================================================================

JAZZMIN_SETTINGS = {
    "site_title": "IlmSpace Admin",
    "site_header": "IlmSpace",
    "site_brand": "IlmSpace",
    "welcome_sign": "Welcome to IlmSpace Admin Panel",
    "copyright": "IlmSpace Educational Platform",
    "search_model": ["users.User", "courses.Course", "authors.AuthorProfile"],
    
    # Top Menu
    "topmenu_links": [
        {"name": "Home", "url": "admin:index", "permissions": ["auth.view_user"]},
        {"name": "Site", "url": "/", "new_window": True},
        {"model": "users.User"},
        {"app": "courses"},
    ],
    
    # Side Menu
    "show_sidebar": True,
    "navigation_expanded": True,
    
    # Icons
    "icons": {
        "auth": "fas fa-users-cog",
        "auth.Group": "fas fa-users",
        "users.User": "fas fa-user-shield",
        "courses.Course": "fas fa-graduation-cap",
        "courses.Category": "fas fa-folder-open",
        "courses.CourseModule": "fas fa-book",
        "courses.Lesson": "fas fa-play-circle",
        "courses.CourseEnrollment": "fas fa-user-graduate",
        "courses.CourseReview": "fas fa-star",
        "courses.LessonProgress": "fas fa-tasks",
        "authors.AuthorProfile": "fas fa-chalkboard-teacher",
        "authors.AuthorBalance": "fas fa-wallet",
        "authors.PayoutRequest": "fas fa-money-bill-wave",
        "students.StudentProfile": "fas fa-user-tie",
        "students.WatchHistory": "fas fa-history",
        "students.StudentNote": "fas fa-sticky-note",
        "students.StudentBookmark": "fas fa-bookmark",
        "payments.Transaction": "fas fa-exchange-alt",
        "payments.Refund": "fas fa-undo",
        "payments.PromoCode": "fas fa-tags",
        "moderation.CourseModeration": "fas fa-clipboard-check",
    },
    "default_icon_parents": "fas fa-chevron-circle-right",
    "default_icon_children": "fas fa-circle",
    
    # UI
    "related_modal_active": True,
    "changeform_format": "horizontal_tabs",
    "changeform_format_overrides": {
        "users.User": "collapsible",
        "courses.Course": "horizontal_tabs",
    },
}

JAZZMIN_UI_TWEAKS = {
    "navbar_small_text": False,
    "footer_small_text": False,
    "brand_colour": "navbar-primary",
    "accent": "accent-primary",
    "navbar": "navbar-dark",
    "navbar_fixed": True,
    "sidebar_fixed": True,
    "sidebar": "sidebar-dark-primary",
    "theme": "default",
    "button_classes": {
        "primary": "btn-primary",
        "secondary": "btn-secondary",
        "info": "btn-info",
        "warning": "btn-warning",
        "danger": "btn-danger",
        "success": "btn-success",
    },
}

# =============================================================================
# PAYMENT GATEWAYS (Uzbekistan)
# =============================================================================

PAYMENT_SETTINGS = {
    'CLICK': {
        'MERCHANT_ID': os.getenv('CLICK_MERCHANT_ID', ''),
        'SECRET_KEY': os.getenv('CLICK_SECRET_KEY', ''),
        'SERVICE_ID': os.getenv('CLICK_SERVICE_ID', ''),
    },
    'PAYME': {
        'MERCHANT_ID': os.getenv('PAYME_MERCHANT_ID', ''),
        'SECRET_KEY': os.getenv('PAYME_SECRET_KEY', ''),
    },
    'UZUM': {
        'MERCHANT_ID': os.getenv('UZUM_MERCHANT_ID', ''),
        'SECRET_KEY': os.getenv('UZUM_SECRET_KEY', ''),
    },
}


REDIS_HOST = os.getenv('REDIS_HOST', 'localhost')
REDIS_PORT = os.getenv('REDIS_PORT', '6379')
REDIS_DB = os.getenv('REDIS_DB', '0')
REDIS_URL = f"redis://{REDIS_HOST}:{REDIS_PORT}/{REDIS_DB}"

# Platform commission rate (percentage)
PLATFORM_COMMISSION_RATE = 20  # 20% commission on course sales

# =============================================================================
# DJANGO ALLAUTH CONFIGURATION
# =============================================================================

SITE_ID = 1

AUTHENTICATION_BACKENDS = [
    'django.contrib.auth.backends.ModelBackend',
    'allauth.account.auth_backends.AuthenticationBackend',
]

# Allauth settings (using new API)
ACCOUNT_LOGIN_ON_GET = True
ACCOUNT_LOGOUT_ON_GET = True
ACCOUNT_EMAIL_VERIFICATION = 'optional'
ACCOUNT_UNIQUE_EMAIL = True
ACCOUNT_USER_MODEL_USERNAME_FIELD = 'phone_number'

# New allauth settings (v65+)
ACCOUNT_LOGIN_METHODS = {'email'}
ACCOUNT_SIGNUP_FIELDS = ['email*', 'password1*', 'password2*']

# Custom adapter to handle user creation
ACCOUNT_ADAPTER = 'users.adapters.CustomAccountAdapter'
SOCIALACCOUNT_ADAPTER = 'users.adapters.CustomSocialAccountAdapter'

# Login/Logout redirects
LOGIN_REDIRECT_URL = '/'
LOGOUT_REDIRECT_URL = '/'
ACCOUNT_LOGOUT_REDIRECT_URL = '/'

# Social account settings
SOCIALACCOUNT_AUTO_SIGNUP = True
SOCIALACCOUNT_EMAIL_AUTHENTICATION = True
SOCIALACCOUNT_EMAIL_AUTHENTICATION_AUTO_CONNECT = True
SOCIALACCOUNT_LOGIN_ON_GET = True

# Google OAuth Configuration
SOCIALACCOUNT_PROVIDERS = {
    'google': {
        'SCOPE': [
            'profile',
            'email',
        ],
        'AUTH_PARAMS': {
            'access_type': 'online',
        },
        'OAUTH_PKCE_ENABLED': True,
        'APP': {
            'client_id': os.getenv('GOOGLE_CLIENT_ID', ''),
            'secret': os.getenv('GOOGLE_CLIENT_SECRET', ''),
            'key': ''
        }
    }
}

# =============================================================================
# REDIS CONFIGURATION (for OTP Service)
# =============================================================================

REDIS_URL = os.getenv('REDIS_URL', 'redis://localhost:6379/0')

# =============================================================================
# TELEGRAM BOT CONFIGURATION
# =============================================================================

BOT_TOKEN = os.getenv('BOT_TOKEN', '')
