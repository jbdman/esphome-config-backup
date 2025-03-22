import os
import base64

def xor_encrypt(data: bytes, key: bytes) -> bytes:
    return bytes([b ^ key[i % len(key)] for i, b in enumerate(data)])

def generate_embed_header(source_file, out_file, key):
    with open(source_file, "rb") as f:
        plaintext = f.read()

    encrypted = xor_encrypt(plaintext, key.encode("utf-8"))
    encoded = base64.b64encode(encrypted).decode("utf-8")

    with open(out_file, "w") as f:
        f.write('#pragma once\n\n')
        f.write('const char CONFIG_B64[] PROGMEM = R"rawliteral(\n')
        f.write(encoded)
        f.write('\n)rawliteral";\n')

def build(config):
    config_path = config["config_path"]
    build_path = config["build_path"]
    out_file = os.path.join(build_path, "src", "config_embed.h")

    password = os.environ.get("CONFIG_BACKUP_KEY")
    if not password:
        raise Exception("Missing CONFIG_BACKUP_KEY environment variable!")

    if not os.path.exists(config_path):
        raise Exception(f"Config file not found: {config_path}")

    print(f"[config_backup] Embedding {config_path} → config_embed.h")
    generate_embed_header(config_path, out_file, password)
