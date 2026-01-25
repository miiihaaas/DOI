"""
With these settings, tests run faster.
"""
import os

# Set DATABASE_URL before importing base settings to avoid KeyError
# This will be overridden below with SQLite for tests
os.environ.setdefault("DATABASE_URL", "sqlite://:memory:")

from .base import *  # noqa: F403
from .base import TEMPLATES
from .base import env

# DATABASES
# ------------------------------------------------------------------------------
# Use SQLite for tests to avoid requiring PostgreSQL
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": ":memory:",
    }
}

# GENERAL
# ------------------------------------------------------------------------------
# https://docs.djangoproject.com/en/dev/ref/settings/#secret-key
SECRET_KEY = env(
    "DJANGO_SECRET_KEY",
    default="test-only-secret-key-not-for-production-xK9mN2wL5vT8jR3fE6hC1bA4dU7zPQ0yS",
)
# https://docs.djangoproject.com/en/dev/ref/settings/#test-runner
TEST_RUNNER = "django.test.runner.DiscoverRunner"

# PASSWORDS
# ------------------------------------------------------------------------------
# https://docs.djangoproject.com/en/dev/ref/settings/#password-hashers
PASSWORD_HASHERS = ["django.contrib.auth.hashers.MD5PasswordHasher"]

# EMAIL
# ------------------------------------------------------------------------------
# https://docs.djangoproject.com/en/dev/ref/settings/#email-backend
EMAIL_BACKEND = "django.core.mail.backends.locmem.EmailBackend"

# DEBUGGING FOR TEMPLATES
# ------------------------------------------------------------------------------
TEMPLATES[0]["OPTIONS"]["debug"] = True  # type: ignore[index]

# MEDIA
# ------------------------------------------------------------------------------
# https://docs.djangoproject.com/en/dev/ref/settings/#media-url
MEDIA_URL = "http://media.testserver/"

# CELERY
# ------------------------------------------------------------------------------
# https://docs.celeryq.dev/en/stable/userguide/configuration.html#task-always-eager
# Run Celery tasks synchronously in tests
CELERY_TASK_ALWAYS_EAGER = True

# Your stuff...
# ------------------------------------------------------------------------------
