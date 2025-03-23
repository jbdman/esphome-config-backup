import sys
import textwrap

input_file = "config-decrypt.js"
output_file = "config-decrypt.h"

with open(input_file, "r", encoding="utf-8") as f:
    js = f.read()

escaped = js.replace("\\", "\\\\").replace('"', '\\"').replace("\n", "\\n\"\n\"")
lines = textwrap.wrap(escaped, 80)

with open(output_file, "w", encoding="utf-8") as f:
    f.write("#pragma once\n\n")
    f.write("static const char CONFIG_DECRYPT_JS[] PROGMEM = \n")
    f.write("\n".join(f'"{line}"' for line in lines))
    f.write(";\n")
    f.write(f"static const size_t CONFIG_DECRYPT_JS_SIZE = {len(js)};\n")
