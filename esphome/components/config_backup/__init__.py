import esphome.codegen as cg
import esphome.config_validation as cv
from esphome.components import web_server_base
from esphome.components.web_server_base import CONF_WEB_SERVER_BASE_ID
from esphome.const import CONF_ID
from esphome.core import CORE, coroutine_with_priority

import os
import base64

CONFIG_BACKUP_NS = cg.esphome_ns.namespace("config_backup")
ConfigBackup = CONFIG_BACKUP_NS.class_(
    "ConfigBackup",
    cg.Component,
    cg.global_ns.class_("AsyncWebHandler")
)

CONF_KEY = "key"
CONF_ENCRYPTION = "encryption"

ENCRYPTION_TYPES = ["none", "xor"]

CONFIG_SCHEMA = cv.Schema(
    {
        cv.GenerateID(): cv.declare_id(ConfigBackup),
        cv.GenerateID(CONF_WEB_SERVER_BASE_ID): cv.use_id(web_server_base.WebServerBase),
        cv.Optional(CONF_ENCRYPTION, default="none"): cv.one_of(*ENCRYPTION_TYPES, lower=True),
        cv.Optional(CONF_KEY): cv.string,
    }
).extend(cv.COMPONENT_SCHEMA)

AUTO_LOAD = ["web_server_base"]
REQUIRES = ["web_server_base"]
CODEOWNERS = ["@jbdman"]

def xor_encrypt(data: bytes, key: bytes) -> bytes:
    return bytes([b ^ key[i % len(key)] for i, b in enumerate(data)])

@coroutine_with_priority(64.0)
async def to_code(config):
    encryption = config[CONF_ENCRYPTION]
    key = config.get(CONF_KEY)

    input_file = CORE.config_path
    output_file = os.path.join(os.path.dirname(__file__), "config_embed.h")

    with open(input_file, "rb") as f:
        yaml_bytes = f.read()

    if encryption == "xor":
        if not key:
            raise cv.Invalid("Encryption type 'xor' requires a 'key' to be specified.")
        print("[config_backup] Encrypting config using XOR")
        final_bytes = xor_encrypt(yaml_bytes, key.encode("utf-8"))
    elif encryption == "none":
        print("[config_backup] Embedding config without encryption")
        final_bytes = yaml_bytes
    else:
        raise cv.Invalid(f"Unsupported encryption type: {encryption}")

    b64_encoded = base64.b64encode(final_bytes).decode("utf-8")

    os.makedirs(os.path.dirname(output_file), exist_ok=True)
    with open(output_file, "w", encoding="utf-8") as f:
        f.write('#pragma once\n\n')
        f.write('// Embedded config file (base64-encoded)\n')
        f.write('const char CONFIG_B64[] =\n')
        for i in range(0, len(b64_encoded), 80):
            f.write(f'"{b64_encoded[i:i+80]}"\n')
        f.write(';\n')

    print(f"[config_backup] Embedded config from {input_file} → {output_file} "
          f"({'encrypted' if encryption != 'none' else 'plain'})")

    server = await cg.get_variable(config[CONF_WEB_SERVER_BASE_ID])
    var = cg.new_Pvariable(config[CONF_ID], server)
    await cg.register_component(var, config)
