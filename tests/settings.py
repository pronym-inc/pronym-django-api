DEBUG = True
INSTALLED_APPS = (
    # Default Django apps
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "tests",
    "pronym_api"
)
ROOT_URLCONF = "tests.urls"
DATABASES = {"default": {"ENGINE": "django.db.backends.sqlite3", "NAME": ":memory:"}}
MIDDLEWARE = (
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.contrib.auth.dmiddleware.AuthenticationMiddleware",  # required for django.contrib.admin
    "django.contrib.messages.middleware.MessageMiddleware",  # required for django.contrib.admin
)
TEST_RUNNER = 'django_nose.NoseTestSuiteRunner'
STATIC_URL = "/static/"
TOKEN_EXPIRATION_MINUTES = 120
API_SECRET = "shhhdontellanyone"
SECRET_KEY = "shhhdontellanyone"
JWT_SUB = "pronym"
JWT_ISS = "pronymapi"
JWT_AUD = "pronym"
USE_TZ = True
TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.contrib.auth.context_processors.auth",
                "django.template.context_processors.debug",
                "django.template.context_processors.i18n",
                "django.template.context_processors.media",
                "django.template.context_processors.static",
                "django.template.context_processors.tz",
                "django.contrib.messages.context_processors.messages",
            ]
        },
    }
]
