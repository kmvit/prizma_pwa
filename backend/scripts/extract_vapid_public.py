#!/usr/bin/env python3
"""
Извлечь VAPID публичный ключ (base64url) из private_key.pem.
Результат нужно прописать в .env как VAPID_PUBLIC_KEY.

Запуск из backend/: python -m scripts.extract_vapid_public
"""
import sys
from pathlib import Path

# backend/scripts -> backend, добавить в path
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
DEFAULT_PRIVATE = ROOT / "private_key.pem"


def extract_public_key(pem_path: Path) -> str:
    from app.utils.vapid_keys import extract_public_key_from_pem
    return extract_public_key_from_pem(pem_path)


def main():
    path = Path(sys.argv[1]) if len(sys.argv) > 1 else DEFAULT_PRIVATE
    if not path.exists():
        print(f"Файл не найден: {path}", file=sys.stderr)
        print("Сгенерируйте ключи: python -m py_vapid --gen", file=sys.stderr)
        sys.exit(1)
    key = extract_public_key(path)
    print(f"\nДобавьте в .env:\nVAPID_PUBLIC_KEY={key}\n")


if __name__ == "__main__":
    main()
