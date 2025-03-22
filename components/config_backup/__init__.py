import esphome.codegen as cg
import esphome.config_validation as cv

# C++ namespace: config_backup::ConfigBackup
CONFIG_BACKUP_NS = cg.global_ns.namespace("config_backup")
ConfigBackup = CONFIG_BACKUP_NS.class_("ConfigBackup", cg.Component)

# Optional ID for referencing this component later
CONFIG_SCHEMA = cv.Schema({
    cv.GenerateID(): cv.declare_id(ConfigBackup),
})

CODEOWNERS = ["@jbdman"]
REQUIRES = ["web_server"]


def to_code(config):
    var = cg.new_Pvariable(config[cv.CONF_ID], ConfigBackup)
    yield cg.register_component(var, config)
