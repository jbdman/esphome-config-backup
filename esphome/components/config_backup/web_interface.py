# web_interface.py

import esphome.codegen as cg
from esphome.core import CORE
import logging
from . import utils

logger = utils.CustomAdapter(logging.getLogger(__name__))

def find_index_html_globals():
    """Find and extract the index.html related global statements."""
    index_html = index_html_key = index_html_size = None
    to_remove = []
    
    for expression in CORE.global_statements:
        if type(expression.expression) == cg.RawExpression:
            if "ESPHOME_WEBSERVER_INDEX_HTML" in expression.expression.text:
                # Extract existing index.html data
                # ... (existing extraction logic)
                
    return index_html, index_html_key, index_html_size, to_remove

def inject_script_tags(index_html, config_path, javascript_location, root_path):
    """Inject the required script tags into index.html."""
    config_decrypt_js = "/config-decrypt.js"
    
    if javascript_location == "remote":
        cg.add_define("ESPHOME_CONFIG_BACKUP_NOJS")
        # Get git info for CDN path
        commit_tag = utils.get_git_commit_tag(root_path)
        user_repo = utils.get_git_user_repo(root_path)
        config_decrypt_js = f"https://cdn.jsdelivr.net/gh/{user_repo}@{commit_tag}/cdn/config-decrypt.js"

    script_tag = (
        f'<script>var CONF_PATH="{config_path}";</script>'
        '<script src="https://cdnjs.cloudflare.com/ajax/libs/crypto-js/4.1.1/crypto-js.min.js"></script>'
        f'<script src="{config_decrypt_js}"></script>'
    )
    
    insert_pos = index_html.find("</body>")
    if insert_pos != -1:
        return index_html[:insert_pos] + script_tag + index_html[insert_pos:]
    return index_html

async def setup_gui(config, var):
    """Main function to set up the web interface."""
    index_html, index_html_key, index_html_size, to_remove = find_index_html_globals()
    
    if None in (index_html, index_html_key, index_html_size):
        logger.error("Failed to extract index.html globals")
        return
        
    # Modify index.html
    modified_html = inject_script_tags(
        index_html,
        config.get("config_path"),
        config.get("javascript_location"),
        config.get("root_path")
    )
    
    # Remove old globals and add new ones
    for expr in to_remove:
        CORE.global_statements.remove(expr)
        
    # Add modified index.html globals
    # ... (existing code to add new globals)