# web_interface.py

import esphome.codegen as cg
from esphome.core import CORE
import logging
from . import utils
from . import git_handler as git
from . import file_handling as fileh

logger = utils.CustomAdapter(logging.getLogger(__name__))

def find_index_html_globals():
    """Find and extract the index.html related global statements."""
    index_html = index_html_key = index_html_size = None
    to_remove = []
    
    for expression in CORE.global_statements:
        if type(expression.expression) == cg.RawExpression:
            if "ESPHOME_WEBSERVER_INDEX_HTML" in expression.expression.text:
                if "uint8_t" in expression.expression.text:
                    value = expression.expression.text
                    [index_html_key, value] = value.split("{")
                    value = value.split("}")[0]
                    index_html = fileh.from_int_list_string(value).decode("utf-8")
                    index_html_key = index_html_key.split('[')
                    index_html_key[1] = index_html_key[1].split(']')[1]
                else:
                    value = expression.expression.text
                    index_html_size = value.split('=')[0]
                to_remove.append(expression)    
    return index_html, index_html_key, index_html_size, to_remove

def inject_script_tags(index_html, config_path, javascript_location, root_path):
    """Inject the required script tags into index.html."""
    config_decrypt_js = "/config-decrypt.js"
    
    if javascript_location == "remote":
        cg.add_define("ESPHOME_CONFIG_BACKUP_NOJS")
        # Get git info for CDN path
        commit_tag = git.get_commit_tag()
        user_repo = git.get_user_repo_name()
        config_decrypt_js = f"https://cdn.jsdelivr.net/gh/{user_repo}@{commit_tag}/cdn/config-decrypt.js"
    elif javascript_location == "local":
        js_file = os.path.join(os.path.dirname(__file__), "config-decrypt.js")
        ##################################################################
        utils.ensure_package('mini-racer', 'py_mini_racer')
        # Add custom path for necessary Python module. 
        import sys
        sys.path.append(
            os.path.join(utils.root_path, "bin", "Python")
        )
        import uglify_wrapper
        ##################################################################
        def mangle_js(input_bytes: bytes) -> bytes:
            js_str = input_bytes.decode('utf-8')
            return uglify_wrapper.minify_js(js_str).encode('utf-8')
        embedded_js = fileh.embed_file(
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
        js_c_array = fileh.to_c_array(embedded_js, "CONFIG_DECRYPT_JS")
        lines = js_c_array.split("\n")
        cg.add_global(cg.RawExpression(lines[0]))
        cg.add_global(cg.RawExpression(lines[1]))
    else:
        logger.error(f"Unknown javascript_location: {javascript_location}")
        return

    script_tag = (
        f'<script>var CONF_PATH="{config_path}";</script>'
        '<script src="https://cdnjs.cloudflare.com/ajax/libs/crypto-js/4.1.1/crypto-js.min.js"></script>'
        f'<script src="{config_decrypt_js}"></script>'
    )
    
    insert_pos = index_html.find("</body>")
    if insert_pos != -1:
        return index_html[:insert_pos] + script_tag + index_html[insert_pos:]
    return index_html

async def setup_gui(config):
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
        # logger.info(f"Removing {expr.expression.text}")
        CORE.global_statements.remove(expr)
        
    ## Add modified index.html globals
    # Create the new expressions
    final_int_string = fileh.to_int_list_string(modified_html.encode("utf-8"))
    final_size = len(modified_html)
    final_expression = (f'[{final_size}]'.join(index_html_key)) + f"{{{final_int_string}}};"
    final_size_expression = index_html_size + f"= {final_size}"

    # logger.info("Adding the new index.html")
    # Add the new expressions
    cg.add_global(cg.RawExpression(final_expression))
    cg.add_global(cg.RawExpression(final_size_expression))