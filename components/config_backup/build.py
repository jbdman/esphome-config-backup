import os
import hashlib
from base64 import b64encode

def xor_encrypt(data: bytes, key: bytes) -> bytes:
    return bytes([b ^ key[i % len(key)] for i, b in enumerate(data)])

def generate_embed_header(source_file, out_file, key):
    with open(source_file, "rb") as f:
        plaintext = f.read()
    enc = xor_encrypt(plaintext, key.encode())
    b64 = b64encode(enc).decode("utf-8")

    with open(out_file, "w") as f:
        f.write(f'#pragma once\n\nconst char CONFIG_B64[] PROGMEM = R"rawliteral(\n{b64}\n)rawliteral";\n')

def build(config):
    source_path = os.path.join(config["build_path"], "config_backup.yaml")
    out_path = os.path.join(config["build_path"], "src", "config_embed.h")

    key = os.environ.get("CONFIG_BACKUP_KEY", "")
    if not key:
        raise Exception("Missing CONFIG_BACKUP_KEY env var!")

    if not os.path.exists(source_path):
        raise Exception(f"Missing config file: {source_path}")

    print(f"Encrypting {source_path} -> {out_path}")
    generate_embed_header(source_path, out_path, key)
