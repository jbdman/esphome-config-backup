from esphome.components import custom_component
from esphome import automation, config_validation as cv
import esphome.codegen as cg

CONFIG_SCHEMA = cv.Schema({}).extend({})

CODEOWNERS = ["@yourgithubusername"]

def to_code(config):
    cg.add_define("USE_CONFIG_BACKUP")
    yield cg.register_component(cg.new_Pvariable("config_backup"), config)
