# embed_js.py
import sys

input_file = "config-decrypt.js"
output_file = "config-decrypt.h"

with open(input_file, "r", encoding="utf-8") as f:
    js = f.read()

with open(output_file, "w", encoding="utf-8") as f:
    f.write("#pragma once\n\n")
    f.write("#include <cstddef>\n")
    f.write("#include <pgmspace.h>\n\n")
    f.write("static const char CONFIG_DECRYPT_JS[] PROGMEM = \n")

    # Escape content line-by-line for valid C string
    for line in js.splitlines():
        escaped = line.replace('\\', '\\\\').replace('"', '\\"')
        f.write(f'"{escaped}\\n"\n')

    f.write(";\n")
    f.write(f"static const size_t CONFIG_DECRYPT_JS_SIZE = {len(js)};\n")
