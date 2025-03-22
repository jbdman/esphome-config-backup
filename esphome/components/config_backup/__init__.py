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

CONFIG_SCHEMA = cv.Schema(
    {
        cv.GenerateID(): cv.declare_id(ConfigBackup),
        cv.GenerateID(CONF_WEB_SERVER_BASE_ID): cv.use_id(web_server_base.WebServerBase),
    }
).extend(cv.COMPONENT_SCHEMA)

AUTO_LOAD = ["web_server_base"]
REQUIRES = ["web_server_base"]
CODEOWNERS = ["@jbdman"]

def xor_encrypt(data: bytes, key: bytes) -> bytes:
    return bytes([b ^ key[i % len(key)] for i, b in enumerate(data)])

@coroutine_with_priority(64.0)
async def to_code(config):
    key = os.environ.get("CONFIG_BACKUP_KEY")
    if not key:
        raise Exception("CONFIG_BACKUP_KEY not set in environment")

    input_file = CORE.config_path
    output_file = os.path.join(os.path.dirname(__file__), "config_embed.h")

    with open(input_file, "rb") as f:
        yaml_bytes = f.read()

    encrypted = xor_encrypt(yaml_bytes, key.encode("utf-8"))
    b64_encoded = base64.b64encode(encrypted).decode("utf-8")

    os.makedirs(os.path.dirname(output_file), exist_ok=True)
    with open(output_file, "w", encoding="utf-8") as f:
        f.write('#pragma once\n\n')
        f.write('const char CONFIG_B64[] =\n')
        for i in range(0, len(b64_encoded), 80):
            f.write(f'"{b64_encoded[i:i+80]}"\n')
        f.write(';\n')

    print(f"[config_backup] Embedded encrypted config from {input_file} → {output_file}")

    server = await cg.get_variable(config[CONF_WEB_SERVER_BASE_ID])
    var = cg.new_Pvariable(config[CONF_ID], server)
    await cg.register_component(var, config)
