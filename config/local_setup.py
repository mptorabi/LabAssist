"""Create a private local key without starting Django or opening a database."""
import os
from pathlib import Path
import secrets


def initialize(base_dir):
    directory = Path(base_dir) / ".local"
    directory.mkdir(mode=0o700, parents=True, exist_ok=True)
    path = directory / "secret_key"
    try:
        descriptor = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    except FileExistsError:
        return False
    with os.fdopen(descriptor, "w", encoding="utf-8") as stream:
        stream.write(secrets.token_urlsafe(64) + "\n")
    return True


if __name__ == "__main__":
    created = initialize(Path(__file__).resolve().parent.parent)
    print("Local secret key created." if created else "Existing key kept unchanged.")
    print("Protect .local/ with your Windows account permissions; never commit it.")
