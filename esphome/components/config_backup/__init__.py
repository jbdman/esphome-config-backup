import esphome.codegen as cg
import esphome.config_validation as cv
import os
import base64
from esphome.core import CORE

CONFIG_BACKUP_NS = cg.global_ns.namespace("config_backup")
ConfigBackup = CONFIG_BACKUP_NS.class_("ConfigBackup", cg.Component)

CONFIG_SCHEMA = cv.Schema({
    cv.GenerateID(): cv.declare_id(ConfigBackup),
})

CODEOWNERS = ["@jbdman"]
REQUIRES = ["web_server"]


def xor_encrypt(data: bytes, key: bytes) -> bytes:
    return bytes([b ^ key[i % len(key)] for i, b in enumerate(data)])


def to_code(config):
    # Handle encryption + header generation inline
    key = os.environ.get("CONFIG_BACKUP_KEY")
    if not key:
        raise Exception("CONFIG_BACKUP_KEY not set in environment")

    input_file = CORE.config_path
    output_file = os.path.join(os.path.dirname(__file__), "src", "config_embed.h")

    with open(input_file, "rb") as f:
        yaml_bytes = f.read()

    encrypted = xor_encrypt(yaml_bytes, key.encode("utf-8"))
    b64_encoded = base64.b64encode(encrypted).decode("utf-8")

    os.makedirs(os.path.dirname(output_file), exist_ok=True)
    with open(output_file, "w", encoding="utf-8") as f:
        f.write('#pragma once\n\n')
        f.write('const char CONFIG_B64[] PROGMEM = R"rawliteral(\n')
        f.write(b64_encoded)
        f.write('\n)rawliteral";\n')

    print(f"[config_backup] Embedded encrypted config from {input_file} → {output_file}")

    # Register the component
    var = cg.new_Pvariable(config[cv.CONF_ID], ConfigBackup)
    yield cg.register_component(var, config)
