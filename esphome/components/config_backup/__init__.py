import sys
import os
import subprocess
import base64
import secrets
import logging

import esphome.codegen as cg
import esphome.config_validation as cv
from esphome import git
from esphome.components import web_server_base
from esphome.components.web_server_base import CONF_WEB_SERVER_BASE_ID
from esphome.const import CONF_ID
from esphome.core import CORE, coroutine_with_priority

# --------------------------------------------------------------------
# Setup Python logging
# --------------------------------------------------------------------
class CustomAdapter(logging.LoggerAdapter):
    def process(self, msg, kwargs):
        return f"[config_backup] {msg}", kwargs

logger = CustomAdapter(logging.getLogger(__name__))
logging.basicConfig(level=logging.INFO)

# --------------------------------------------------------------------
# (Optional) Ensure required packages are installed.
# --------------------------------------------------------------------
def ensure_package(package_name, import_name=None):
    """
    Ensure the specified Python package is installed. If not, prompt the user to install it.

    :param package_name: The name of the package to ensure.
    :param import_name: The module name to import (if different than the package).
    """
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
            logger.error(f"Please install '{package_name}' manually and re-run.")
            sys.exit(1)

ensure_package('cryptography')
ensure_package('mini-racer', 'py_mini_racer')

# --------------------------------------------------------------------
# Git submodule initialization if needed.
# --------------------------------------------------------------------
ROOT_COMPONENT_PATH = os.path.join(os.path.dirname(__file__), "..", "..", "..")

submodule_status = git.run_git_command([
    "git", "submodule", "status"
], ROOT_COMPONENT_PATH)

if submodule_status.startswith('-'):
    logger.info("Initializing submodules...")
    git.run_git_command([
        "git", "submodule", "update", "--init"
    ], ROOT_COMPONENT_PATH)

# Add custom path for additional Python modules.
sys.path.append(
    os.path.join(ROOT_COMPONENT_PATH, "bin", "Python")
)
import globalv
import uglify_wrapper


# --------------------------------------------------------------------
# Embed logic (compression, encryption, placeholder replacement, etc.).
# --------------------------------------------------------------------
import gzip

# We now switch fully to the "cryptography" library for AES:
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC


def xor_encrypt(data: bytes, key: bytes) -> bytes:
    """Simple XOR encryption (demonstration only)."""
    return bytes(d ^ key[i % len(key)] for i, d in enumerate(data))


def aes256_encrypt(data: bytes, key: bytes) -> bytes:
    """
    AES-256 encryption (CBC) with a random IV prepended.
    This matches the snippet you mentioned, ensuring the key must be 16, 24, or 32 bytes.
    """
    if len(key) not in (16, 24, 32):
        raise ValueError("AES key must be 16, 24, or 32 bytes long")
    iv = secrets.token_bytes(16)
    padder = globalv.aes.padder.python(128).padder()
    padded_data = padder.update(data) + padder.finalize()
    cipher = Cipher(algorithms.AES(key), globalv.aes.mode.python(iv), backend=default_backend())
    encryptor = cipher.encryptor()
    encrypted = encryptor.update(padded_data) + encryptor.finalize()
    return iv + encrypted


def deriveKey(passphrase: str, salt: bytes) -> bytes:
    """
    Derive a 256-bit key from passphrase + salt using PBKDF2/HMAC-SHA256 from cryptography.
    """
    kdf = PBKDF2HMAC(
        algorithm=globalv.aes.PBKDF2.algorithm.python(),
        length=globalv.aes.PBKDF2.length.python,
        salt=salt,
        iterations=globalv.aes.PBKDF2.iterations.python,
        backend=default_backend()
    )
    return kdf.derive(passphrase.encode('utf-8'))


def embedFile(
    path: str,
    read_mode: str = 'text',
    placeholder_replace: dict = None,
    mangle: callable = None,
    compress_first: bool = True,
    encrypt: str = 'none',
    key: str = None,
    final_base64: bool = True,
    compress_after_b64: bool = True,
    add_filename_comment: bool = False
) -> bytes:
    """
    Read a file from `path` (text or binary), optionally insert a filename comment,
    do placeholder replacement, minify if needed, compress, encrypt, base64, etc.
    Returns the final bytes, suitable for embedding.
    """
    if read_mode == 'text':
        with open(path, 'r', encoding='utf-8') as f:
            raw_str = f.read()
        data = raw_str.encode('utf-8')
    else:
        with open(path, 'rb') as f:
            data = f.read()

    if add_filename_comment:
        filename = os.path.basename(path)
        comment = f"# filename: {filename}\n".encode('utf-8')
        data = comment + data

    if placeholder_replace:
        text_str = data.decode('utf-8')
        for old, new in placeholder_replace.items():
            text_str = text_str.replace(old, new)
        data = text_str.encode('utf-8')

    if mangle:
        data = mangle(data)

    if compress_first:
        data = gzip.compress(data)

    if encrypt == 'xor':
        if not key:
            raise ValueError("XOR encryption requires a 'key'.")
        data = xor_encrypt(data, key.encode('utf-8'))
    elif encrypt == 'aes256':
        if not key:
            raise ValueError("AES-256 encryption requires a 'key'.")
        salt_bytes = secrets.token_bytes(16)
        derived_key = deriveKey(key, salt_bytes)
        data = salt_bytes + aes256_encrypt(data, derived_key)
    elif encrypt == 'none':
        pass
    else:
        raise ValueError(f"Unsupported encryption type: {encrypt}")

    if final_base64:
        data = base64.b64encode(data)

    if compress_after_b64:
        data = gzip.compress(data)

    return data


def to_c_array(data: bytes, array_name: str) -> str:
    """
    Convert bytes to comma-separated integers in a C++ array, plus size variable.
    Example:
        const uint8_t CONFIG_B64[123] PROGMEM = { ... };
        const size_t CONFIG_B64_SIZE = 123;
    """
    bytes_as_int = ", ".join(str(b) for b in data)
    length = len(data)
    return (f"const uint8_t {array_name}[{length}] PROGMEM = {{{bytes_as_int}}};\n"
            f"const size_t {array_name}_SIZE = {length};")

def to_int_list_string(data: bytes) -> str:
    return ", ".join(str(b) for b in data)

def from_int_list_string(data_str: str) -> bytes:
    """
    Converts a comma-and-space-separated string of integers into a bytes object.
    
    Example:
        "65, 66, 67" → b'ABC'
    """
    return bytes(int(x) for x in data_str.split(','))


# --------------------------------------------------------------------
# Setup the config_backup component.
# --------------------------------------------------------------------
CONFIG_BACKUP_NS = cg.esphome_ns.namespace("config_backup")
ConfigBackup = CONFIG_BACKUP_NS.class_(
    "ConfigBackup",
    cg.Component,
    cg.global_ns.class_("AsyncWebHandler")
)

# Configuration Constants
CONF_KEY = "key"
CONF_ENCRYPTION = "encryption"
CONF_DEBUG = "debug"
CONF_GUI = "gui"
CONF_COMPRESS = "compression"
CONF_CONFIG_PATH = "config_path"
CONF_JAVASCRIPT = "javascript_location"

ENCRYPTION_TYPES = ["none", "xor", "aes256"]
JAVASCRIPT_LOCATIONS = ["remote", "local"]
COMPRESSION_TYPES = ["none", "gzip"]

CONFIG_SCHEMA = cv.Schema({
    cv.GenerateID(): cv.declare_id(ConfigBackup),
    cv.GenerateID(CONF_WEB_SERVER_BASE_ID): cv.use_id(web_server_base.WebServerBase),
    cv.Optional(CONF_ENCRYPTION, default="none"): cv.one_of(*ENCRYPTION_TYPES, lower=True),
    cv.Optional(CONF_GUI, default=True): cv.boolean,
    cv.Optional(CONF_COMPRESS, default="gzip"): cv.one_of(*COMPRESSION_TYPES),
    cv.Optional(CONF_JAVASCRIPT, default="remote"): cv.one_of(*JAVASCRIPT_LOCATIONS),
    cv.Optional(CONF_KEY): cv.string,
    cv.Optional(CONF_DEBUG): cv.string,
    cv.Optional(CONF_CONFIG_PATH, default="/config.b64"): cv.string
}).extend(cv.COMPONENT_SCHEMA)

AUTO_LOAD = ["web_server_base"]
REQUIRES = ["web_server_base"]
CODEOWNERS = ["@jbdman"]
REQUIRED_PYTHON_MODULES = ['cryptography','jsmin']

@coroutine_with_priority(0.0)
async def to_code(config):
    """
    ESPHome build function that embeds, compresses, and optionally encrypts
    the user's YAML configuration into the compiled binary, plus optional JS.
    """
    encryption = config[CONF_ENCRYPTION]
    key = config.get(CONF_KEY)
    debug = config.get(CONF_DEBUG)
    gui = config.get(CONF_GUI)
    compression_type = config.get(CONF_COMPRESS)

    if compression_type == "gzip":
        do_compress = True
    else:
        do_compress = False

    config_path = config.get(CONF_CONFIG_PATH)
    javascript_location = config.get(CONF_JAVASCRIPT)

    # If GUI is enabled, inject index.html
    if gui:
        INDEX_HTML = INDEX_HTML_KEY = INDEX_HTML_SIZE = None

        to_remove = []
        for expression in CORE.global_statements:
            if type(expression.expression) == cg.RawExpression:
                if "ESPHOME_WEBSERVER_INDEX_HTML" in expression.expression.text:
                    if "uint8_t" in expression.expression.text:
                        value = expression.expression.text
                        [INDEX_HTML_KEY, value] = value.split("{")
                        value = value.split("}")[0]
                        INDEX_HTML = from_int_list_string(value).decode("utf-8")
                        INDEX_HTML_KEY = INDEX_HTML_KEY.split('[')
                        INDEX_HTML_KEY[1] = INDEX_HTML_KEY[1].split(']')[1]
    
                        config_decrypt_js = "/config-decrypt.js"
                        if javascript_location == "remote":
                            cg.add_define("ESPHOME_CONFIG_BACKUP_NOJS")
                            try:
                                commit_tag = git.run_git_command(['git', 'describe', '--tags', '--always', '--dirty'], ROOT_COMPONENT_PATH)
                            except:
                                logger.warning("Failed to extract git commit tag")
                                commit_tag = "main"
                            try:
                                user_repo = git.run_git_command(['git', 'remote', 'get-url', 'origin'], ROOT_COMPONENT_PATH).replace("https://github.com/","").replace(".git","")
                            except:
                                logger.warning("Failed to extract git user and repo name")
                                user_repo = "jbdman/esphome-config-backup"
                            
                            config_decrypt_js = f"https://cdn.jsdelivr.net/gh/{user_repo}@{commit_tag}/cdn/config-decrypt.js"
    
                        # Script tags to be injected
                        script_tag = (
                            f'<script>var CONF_PATH="{config_path}";</script>'
                            '<script src="https://cdnjs.cloudflare.com/ajax/libs/crypto-js/4.1.1/crypto-js.min.js"></script>'
                            f'<script src="{config_decrypt_js}"></script>'
                        )
                        
                        # Find where to inject the script tags
                        insert_pos = INDEX_HTML.find("</body>")
                        if insert_pos != -1:
                            INDEX_HTML = INDEX_HTML[:insert_pos] + script_tag + INDEX_HTML[insert_pos:]
                    else:
                        value = expression.expression.text
                        INDEX_HTML_SIZE = value.split('=')[0]
                    to_remove.append(expression)

        # Check to make sure we got what we need from the above, otherwise throw an error
        if not None in (INDEX_HTML, INDEX_HTML_KEY, INDEX_HTML_SIZE):
            # Create the new expressions
            final_int_string = to_int_list_string(INDEX_HTML.encode("utf-8"))
            final_size = len(INDEX_HTML)
            final_expression = (f'[{final_size}]'.join(INDEX_HTML_KEY)) + f"{{{final_int_string}}};"
            final_size_expression = INDEX_HTML_SIZE + f"= {final_size}"

            # Remove the designated expressions from the global list
            for expression in to_remove:
                CORE.global_statements.remove(expression)

            # Add the new ones
            cg.add_global(cg.RawExpression(final_expression))
            cg.add_global(cg.RawExpression(final_size_expression))
        else:
            # Log the states
            logger.warning(f"INDEX_HTML: {INDEX_HTML}\nINDEX_HTML_KEY: {INDEX_HTML_KEY}\nINDEX_HTML_SIZE: {INDEX_HTML_SIZE}")
            # Grab the GH user
            try:
                user_repo = git.run_git_command(['git', 'remote', 'get-url', 'origin'], ROOT_COMPONENT_PATH).replace("https://github.com/","").replace(".git","")
            except:
                logger.warning("Failed to extract git user and repo name")
                user_repo = "jbdman/esphome-config-backup"
            # Raise the exception
            raise Exception(f"Missing value from parsing INDEX_HTML. Please report this to @{user_repo.split('/')[0]} on github.")

        if javascript_location == "local":
            js_file = os.path.join(os.path.dirname(__file__), "config-decrypt.js")

            def mangle_js(input_bytes: bytes) -> bytes:
                js_str = input_bytes.decode('utf-8')
                return uglify_wrapper.minify_js(js_str).encode('utf-8')
    
            embedded_js = embedFile(
                path=js_file,
                read_mode='text',
                placeholder_replace={"{{aes.padder}}": globalv.aes.padder.javascript,
                                     "{{aes.mode}}": globalv.aes.mode.javascript,
                                     "{{aes.PBKDF2.algorithm}}": globalv.aes.PBKDF2.algorithm.javascript,
                                     "{{aes.PBKDF2.iterations}}": globalv.aes.PBKDF2.iterations.javascript,
                                     "{{aes.PBKDF2.length}}": globalv.aes.PBKDF2.length.javascript},
                mangle=mangle_js,
                compress_first=True,
                encrypt='none',
                key=None,
                final_base64=False,
                compress_after_b64=False,
                add_filename_comment=False
            )
            # Convert to C++ array
            js_c_array = to_c_array(embedded_js, "CONFIG_DECRYPT_JS")
            lines = js_c_array.split("\n")
            cg.add_global(cg.RawExpression(lines[0]))
            cg.add_global(cg.RawExpression(lines[1]))

    # Embed the main YAML.
    yaml_file = CORE.config_path
    embedded_yaml = embedFile(
        path=yaml_file,
        read_mode='binary',
        add_filename_comment=True,
        compress_first=do_compress,
        encrypt=encryption,
        key=key,
        final_base64=True,
        compress_after_b64=True
    )

    # For debugging, if the user wants to see the final base64, we can only warn because
    # it is double-compressed.
    if debug in ("print.b64", "print.*", "*"):
        try:
            decompressed_b64 = gzip.decompress(embedded_yaml)
            base64_str = decompressed_b64.decode('utf-8', errors='ignore')
            logger.info(f"Config: {base64_str}")
        except Exception as e:
            logger.warning(f"Could not decompress final data to display base64: {e}")
    elif debug == "examples.create":
        try:
            dest_path = os.path.dirname(CORE.config_path)
            config_name = os.path.splitext(os.path.basename(CORE.config_path))[0]
            for crypt in ENCRYPTION_TYPES:
                dest_file = os.path.join(dest_path, f"{config_name}-config-{crypt}-{key}")
                with open(dest_file, "w") as f:
                    f.write(embedFile(
                                path=yaml_file,
                                read_mode='binary',
                                add_filename_comment=True,
                                compress_first=do_compress,
                                encrypt=crypt,
                                key=key,
                                final_base64=True,
                                compress_after_b64=False
                            ).decode("utf-8"))
        except Exception as e:
            logger.warning(f"Could not create examples: {e}")
    # Convert final YAML data to a C++ array.
    yaml_c_array = to_c_array(embedded_yaml, "CONFIG_B64")
    lines = yaml_c_array.split("\n")
    cg.add_global(cg.RawExpression(lines[0]))
    cg.add_global(cg.RawExpression(lines[1]))

    # Log the embed status.
    if encryption == 'none':
        logger.info("Embedded config without encryption")
    else:
        logger.info(f"Encrypted and embedded config using {encryption.upper()}")

    # Create the component instance
    server = await cg.get_variable(config[CONF_WEB_SERVER_BASE_ID])
    var = cg.new_Pvariable(config[CONF_ID], server)
    await cg.register_component(var, config)

    # C++ class needs to know the encryption method, compression type, and config_path
    cg.add(var.set_encryption(encryption))
    cg.add(var.set_compression(compression_type))
    cg.add(var.set_config_path(config_path))
