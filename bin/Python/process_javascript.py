import os
import globalv
import uglify_wrapper

repository_root = os.path.join(os.path.dirname(__file__), "..", "..")
javascript_file = os.path.join(repository_root, "esphome/components/config_backup/config-decrypt.js")
output_path = os.path.join(repository_root, "cdn/config-decrypt.js")

placeholder_replace={"{{path}}": "/config.b64", 
                     "{{aes.padder}}": globalv.aes.padder.javascript,
                     "{{aes.mode}}": globalv.aes.mode.javascript,
                     "{{aes.PBKDF2.algorithm}}": globalv.aes.PBKDF2.algorithm.javascript,
                     "{{aes.PBKDF2.iterations}}": globalv.aes.PBKDF2.iterations.javascript,
                     "{{aes.PBKDF2.length}}": globalv.aes.PBKDF2.length.javascript}

with open(javascript_file, 'r', encoding='utf-8') as f:
    javascript = f.read()

for old, new in placeholder_replace.items():
    javascript = javascript.replace(old, new)

javascript = uglify_wrapper.minify_js(javascript)

with open(output_path, "wb") as out:
    out.write(javascript.encode("utf-8"))