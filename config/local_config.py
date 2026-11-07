"""Small, explicit configuration helpers for a loopback-only installation."""
import os
from pathlib import Path

from django.core.exceptions import ImproperlyConfigured


def load_secret_key(base_dir, environ=None):
    environ = os.environ if environ is None else environ
    key = environ.get("LABASSIST_SECRET_KEY")
    if key is None:
        try:
            key = (Path(base_dir) / ".local" / "secret_key").read_text(
                encoding="utf-8"
            ).strip()
        except FileNotFoundError as exc:
            raise ImproperlyConfigured(
                "Local secret key is missing. Run: python -m config.local_setup "
                "(or set LABASSIST_SECRET_KEY)."
            ) from exc
    if len(key) < 50 or len(set(key)) < 5 or key.startswith("django-insecure-"):
        raise ImproperlyConfigured(
            "LABASSIST_SECRET_KEY must be a private, randomly generated key "
            "of at least 50 characters, not the old development key."
        )
    return key


def load_debug(environ=None):
    environ = os.environ if environ is None else environ
    value = environ.get("LABASSIST_DEBUG", "false").strip().lower()
    if value not in {"true", "false", "1", "0"}:
        raise ImproperlyConfigured("LABASSIST_DEBUG must be true, false, 1 or 0.")
    return value in {"true", "1"}
