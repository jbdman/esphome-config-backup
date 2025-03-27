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

root_path = os.path.join(os.path.dirname(__file__), "..", "..")


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
