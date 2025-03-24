# uglify_wrapper.py

import os
from py_mini_racer import MiniRacer

# Path to the UglifyJS /lib directory
UGLIFY_LIB_PATH = os.path.join(os.path.dirname(__file__), "UglifyJS", "lib")

MODULE_ORDER = [
    "..\\..\\v8_polyfills.js",
    "utils.js",
    "ast.js",
    "parse.js",
    "transform.js",
    "scope.js",
    "output.js",
    "compress.js",
    "propmangle.js",
    "minify.js"
]

ctx = MiniRacer()

for module in MODULE_ORDER:
    module_path = os.path.join(UGLIFY_LIB_PATH, module)
    with open(module_path, "r", encoding="utf-8") as f:
        ctx.eval(f.read())

def minify_js_file(path=(os.path.join(os.path.dirname(__file__),"esphome","components","config_backup","config-decrypt.js"))):
    with open(os.path.join(os.path.dirname(__file__),"uglify_config.json"), "r", encoding="utf-8") as f:
        uglify_options = f.read()
    with open(path, "r", encoding="utf-8") as f:
        js_code = f.read()
    ctx.eval('this')['js_code'] = js_code
    ctx.eval('this')['uglify_options'] = uglify_options
    return (ctx.execute(f"""minify(this.js_code, JSON.parse(this.uglify_options)).code"""))

# Example use
if __name__ == "__main__":
    print(minify_js_file())
