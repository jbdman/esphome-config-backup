import sys
import os
import subprocess
import base64
import secrets
import logging

import esphome.codegen as cg
import esphome.config_validation as cv
from esphome.components import web_server_base
from esphome.components.web_server_base import CONF_WEB_SERVER_BASE_ID
from esphome.const import CONF_ID
from esphome.core import CORE, coroutine_with_priority

from . import utils
from . import git_handler as git
from . import web_interface as web
from . import file_handling as fileh

from . import globalv

utils.ensure_package('cryptography')

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
    config_path = config.get(CONF_CONFIG_PATH)
    javascript_location = config.get(CONF_JAVASCRIPT)

    if compression_type == "gzip":
        do_compress = True
    else:
        do_compress = False

    if javascript_location == "local":
        # Initialize git submodules if needed
        if git.get_submodules_status().startswith('-'):
            git.init_submodules()

    # If GUI is enabled, inject index.html
    if gui:
        await web.setup_gui(config)

    # Embed the main YAML.
    yaml_file = CORE.config_path
    embedded_yaml = fileh.embed_file(
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
    if debug == "print.b64":
        try:
            decompressed_b64 = gzip.decompress(embedded_yaml)
            base64_str = decompressed_b64.decode('utf-8', errors='ignore')
            utils.logger.info(f"Config: {base64_str}")
        except Exception as e:
            utils.logger.warning(f"Could not decompress final data to display base64: {e}")
    elif debug == "examples.create":
        try:
            dest_path = os.path.dirname(CORE.config_path)
            config_name = os.path.splitext(os.path.basename(CORE.config_path))[0]
            for crypt in ENCRYPTION_TYPES:
                dest_file = os.path.join(dest_path, f"{config_name}-config-{crypt}-{key}")
                with open(dest_file, "w") as f:
                    f.write(fileh.embed_file(
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
            utils.logger.warning(f"Could not create examples: {e}")


    # Convert final YAML data to a C++ array.
    yaml_c_array = fileh.to_c_array(embedded_yaml, "CONFIG_B64")
    lines = yaml_c_array.split("\n")

    # Add the globals
    cg.add_global(cg.RawExpression(lines[0]))
    cg.add_global(cg.RawExpression(lines[1]))

    # Log the embed status.
    if encryption == 'none':
        utils.logger.info("Embedded config without encryption")
    else:
        utils.logger.info(f"Encrypted and embedded config using {encryption.upper()}")

    # Create the component instance
    server = await cg.get_variable(config[CONF_WEB_SERVER_BASE_ID])
    var = cg.new_Pvariable(config[CONF_ID], server)
    await cg.register_component(var, config)

    # C++ class needs to know the encryption method, compression type, and config_path
    cg.add(var.set_encryption(encryption))
    cg.add(var.set_compression(compression_type))
    cg.add(var.set_config_path(config_path))
