"""Извлечение VAPID публичного ключа из PEM для Web Push."""

import base64
from pathlib import Path


def extract_public_key_from_pem(pem_path: Path) -> str:
    """Извлечь raw public key (65 bytes) и закодировать в base64url."""
    from cryptography.hazmat.primitives.serialization import load_pem_private_key
    from cryptography.hazmat.backends import default_backend

    pem_bytes = pem_path.read_bytes()
    key = load_pem_private_key(pem_bytes, password=None, backend=default_backend())
    pub = key.public_key()
    raw = b"\x04" + pub.public_numbers().x.to_bytes(32, "big") + pub.public_numbers().y.to_bytes(32, "big")
    return base64.urlsafe_b64encode(raw).decode("ascii").rstrip("=")
