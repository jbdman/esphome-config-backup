import subprocess
import sys

def ensure_package(package_name, import_name=None):
    import_name = import_name or package_name
    try:
        __import__(import_name)
    except ImportError:
        response = input(
            f"The required package '{package_name}' is not installed.\n"
            f"Would you like to install it now? [y/N]: "
        ).strip().lower()
        if response == 'y':
            subprocess.check_call([sys.executable, "-m", "pip", "install", package_name])
        else:
            print(f"Please install '{package_name}' manually and re-run.")
            sys.exit(1)

# Check and install packages as needed
ensure_package('cryptography')
ensure_package('pycryptodome', 'Crypto')
ensure_package('jsmin')


import esphome.codegen as cg
import esphome.config_validation as cv
from esphome.components import web_server_base
from esphome.components.web_server_base import CONF_WEB_SERVER_BASE_ID
from esphome.const import CONF_ID
from esphome.core import CORE, coroutine_with_priority
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.primitives import padding as aes_padding
from cryptography.hazmat.backends import default_backend
from Crypto.Protocol.KDF import PBKDF2
import secrets
import os
import base64
import gzip

CONFIG_BACKUP_NS = cg.esphome_ns.namespace("config_backup")
ConfigBackup = CONFIG_BACKUP_NS.class_(
    "ConfigBackup",
    cg.Component,
    cg.global_ns.class_("AsyncWebHandler")
)

CONF_KEY = "key"
CONF_ENCRYPTION = "encryption"
CONF_DEBUG = "debug"
CONF_GUI="gui"

ENCRYPTION_TYPES = ["none", "xor", "aes256"]

CONFIG_SCHEMA = cv.Schema(
    {
        cv.GenerateID(): cv.declare_id(ConfigBackup),
        cv.GenerateID(CONF_WEB_SERVER_BASE_ID): cv.use_id(web_server_base.WebServerBase),
        cv.Optional(CONF_ENCRYPTION, default="none"): cv.one_of(*ENCRYPTION_TYPES, lower=True),
        cv.Optional(CONF_GUI, default=True): cv.boolean,
        cv.Optional(CONF_KEY): cv.string,
        cv.Optional(CONF_DEBUG): cv.string,
    }
).extend(cv.COMPONENT_SCHEMA)

AUTO_LOAD = ["web_server_base"]
REQUIRES = ["web_server_base"]
CODEOWNERS = ["@jbdman"]
REQUIRED_PYTHON_MODULES = [
    'cryptography',
    'pycryptodome',
    'jsmin',
]

def xor_encrypt(data: bytes, key: bytes) -> bytes:
    return bytes([b ^ key[i % len(key)] for i, b in enumerate(data)])

def aes256_encrypt(data: bytes, key: bytes) -> bytes:
    if len(key) not in (16, 24, 32):
        raise ValueError("AES key must be 16, 24, or 32 bytes long")
    iv = secrets.token_bytes(16)
    padder = aes_padding.PKCS7(128).padder()
    padded = padder.update(data) + padder.finalize()
    cipher = Cipher(algorithms.AES(key), modes.CBC(iv), backend=default_backend())
    encryptor = cipher.encryptor()
    encrypted = encryptor.update(padded) + encryptor.finalize()
    return iv + encrypted  # prepend IV for decoder

def deriveKey(password: str, salt: bytes):
    return PBKDF2(password, salt=salt, dkLen=32, count=100000)


@coroutine_with_priority(64.0)
async def to_code(config):
    encryption = config[CONF_ENCRYPTION]
    key = config.get(CONF_KEY)
    debug = config.get(CONF_DEBUG)
    gui = config.get(CONF_GUI)

    jsPath = os.path.join(os.path.dirname(__file__), "config-decrypt.h")
    if os.path.exists(jsPath): os.remove(jsPath)
    if gui: 
        exec(open(os.path.join(os.path.dirname(__file__), "embed_js.py")).read())
        cg.add_define("ESPHOME_CONFIG_BACKUP_GUI")

    input_file = CORE.config_path
    output_file = os.path.join(os.path.dirname(__file__), "config_embed.h")

    with open(input_file, "rb") as f:
        yaml_bytes = f.read()

    filename = os.path.basename(input_file)
    yaml_with_comment = f"# filename: {filename}\n".encode("utf-8") + yaml_bytes

    if encryption == "xor":
        if not key:
            raise cv.Invalid("Encryption type 'xor' requires a 'key' to be specified.")
        print("[config_backup] Encrypting config using XOR")
        final_bytes = xor_encrypt(yaml_with_comment, key.encode("utf-8"))
    elif encryption == "aes256":
        if not key:
            raise cv.Invalid("Encryption type 'aes256' requires a 'key' to be specified.")
        print("[config_backup] Encrypting config using AES-256")
        salt_bytes = secrets.token_bytes(16)
        derived_key = deriveKey(key, salt_bytes)
        final_bytes = salt_bytes + aes256_encrypt(yaml_with_comment, derived_key)
    elif encryption == "none":
        print("[config_backup] Embedding config without encryption")
        final_bytes = yaml_with_comment
    else:
        raise cv.Invalid(f"Unsupported encryption type: {encryption}")

    b64_encoded = base64.b64encode(final_bytes).decode("utf-8")
    gzip_compressed = gzip.compress(b64_encoded)

    if debug == "print.b64" or debug == "print.*" or debug == "*":
        print(b64_encoded)

    os.makedirs(os.path.dirname(output_file), exist_ok=True)
    with open(output_file, "w", encoding="utf-8") as f:
        f.write('#pragma once\n\n')
        f.write('// Embedded config file (base64-encoded)\n')
        f.write('static const char CONFIG_B64[] PROGMEM =\n')
        for i in range(0, len(gzip_compressed), 80):
            f.write(f'"{gzip_compressed[i:i+80]}"\n')
        f.write(';\n')

    print(f"[config_backup] Embedded config from {input_file} → {output_file} "
          f"({'encrypted' if encryption != 'none' else 'plain'})")

    server = await cg.get_variable(config[CONF_WEB_SERVER_BASE_ID])
    var = cg.new_Pvariable(config[CONF_ID], server)
    await cg.register_component(var, config)
    cg.add(var.set_encryption(encryption))
