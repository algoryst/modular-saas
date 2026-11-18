"""
With these settings, tests run faster.
"""

from .base import *  # noqa: F403
from .base import TEMPLATES, env

# GENERAL
# ------------------------------------------------------------------------------
# https://docs.djangoproject.com/en/dev/ref/settings/#secret-key
SECRET_KEY = env(
    "DJANGO_SECRET_KEY",
    default="xCULCHZXDG1XyqVblGMlhXqpaOvGNrsmSdQ0HJa45acnKolPrOPjxGeJnmcsnZs7",
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

# MIDDLEWARE
# ------------------------------------------------------------------------------
# Tests never run collectstatic, so WhiteNoise would warn about a missing STATIC_ROOT.
MIDDLEWARE = [
    m for m in MIDDLEWARE if m != "whitenoise.middleware.WhiteNoiseMiddleware"
]

# DEBUGGING FOR TEMPLATES
# ------------------------------------------------------------------------------
TEMPLATES[0]["OPTIONS"]["debug"] = True  # type: ignore[index]

# MEDIA
# ------------------------------------------------------------------------------
# https://docs.djangoproject.com/en/dev/ref/settings/#media-url
MEDIA_URL = "http://media.testserver/"
# Your stuff...
# ------------------------------------------------------------------------------
# LocMemCache is per-process, so django-ratelimit flags it as not shared. That is
# fine for a single dev/test process; production uses Redis.
SILENCED_SYSTEM_CHECKS = ["django_ratelimit.E003", "django_ratelimit.W001"]
