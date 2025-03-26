# utils.py

import logging
import subprocess
import sys

# --------------------------------------------------------------------
# Setup Python logging
# --------------------------------------------------------------------
class CustomAdapter(logging.LoggerAdapter):
    def process(self, msg, kwargs):
        return f"[config_backup] {msg}", kwargs

logger = CustomAdapter(logging.getLogger(__name__))


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

async def setup_component(config):
    """Set up the ConfigBackup component with the provided configuration.
    
    Args:
        config: Configuration dictionary containing component settings
        
    Returns:
        The configured ConfigBackup component variable
    """
    # Get required components
    var = cg.new_Pvariable(config[CONF_ID])
    web_server = await cg.get_variable(config[web_server_base.CONF_WEB_SERVER_BASE_ID])
    
    # Register as a component
    await cg.register_component(var, config)
    
    # Add the web server base reference
    cg.add(var.set_parent(web_server))
    
    # Set encryption type
    if "encryption" in config:
        cg.add(var.set_encryption(config["encryption"]))
        
    # Set compression type
    if "compression" in config:
        cg.add(var.set_compression(config["compression"]))
        
    # Set config path
    if "config_path" in config:
        cg.add(var.set_config_path(config["config_path"]))
    
    return var