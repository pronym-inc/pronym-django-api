"""
A standalone test runner script, configuring the minimum settings required for django-marina tests to execute.

Re-use at your own risk: many Django applications will require full
settings and/or templates in order to execute their tests, while
django-marina does not.

Adapted from James Bennett's https://github.com/ubernostrum/pwned-passwords-django
"""

import os
import sys

# Make sure the app is (at least temporarily) on the import path.
APP_DIR = os.path.abspath(os.path.dirname(__file__))
sys.path.insert(0, APP_DIR)

# # Minimum settings for the app's tests.
# DEBUG = True
#
# SECRET_KEY = "bootstrap4isawesome"
#
# DATABASES = {"default": {"ENGINE": "django.db.backends.sqlite3", "NAME": ":memory:"}}
#
# INSTALLED_APPS = (
#     # We test this one
#     "bootstrap4",
# )


SETTINGS_DICT = {
    "INSTALLED_APPS": (
        # Default Django apps
        "django.contrib.auth",
        "django.contrib.contenttypes",
        "django.contrib.sessions",
        "pronym_api"
    ),
    "ROOT_URLCONF": "tests.conf.urls",
    "DATABASES": {"default": {"ENGINE": "django.db.backends.sqlite3", "NAME": ":memory:"}},
    "MIDDLEWARE": (
        "django.contrib.sessions.middleware.SessionMiddleware",
        "django.contrib.auth.middleware.AuthenticationMiddleware",  # required for django.contrib.admin
        "django.contrib.messages.middleware.MessageMiddleware",  # required for django.contrib.admin
    ),
    "TEST_RUNNER": 'django_nose.NoseTestSuiteRunner',
    "STATIC_URL": "/static/",
    "TEMPLATES": [
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
}


def run_tests():
    # Making Django run this way is a two-step process. First, call
    # settings.configure() to give Django settings to work with:
    from django.conf import settings

    settings.configure(**SETTINGS_DICT)

    # Then, call django.setup() to initialize the application registry
    # and other bits:
    import django

    django.setup()

    # Now we instantiate a test runner...
    from django.test.utils import get_runner

    TestRunner = get_runner(settings)

    # And then we run tests and return the results.
    test_runner = TestRunner(verbosity=2, interactive=True)
    failures = test_runner.run_tests(["tests"])
    sys.exit(failures)


if __name__ == "__main__":
    run_tests()
