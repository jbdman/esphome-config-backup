#pragma once

static const char CONFIG_DECRYPT_JS[] PROGMEM = 
"window.addEventListener(\"DOMContentLoaded\", () => {\n" "  const container ="
"document.querySelector(\".cards\");\n" "  if (!container) return;\n" "\n" ""
"const card = document.createElement(\"div\");\n" "  card.className ="
"\"card\";\n" "  card.innerHTML = `\n" "    <h2>Decrypt Embedded Config</h2>\n" ""
"<label>Key: <input type=\"text\" id=\"decrypt-key\"></label><br>\n" ""
"<label>Salt: <input type=\"text\" id=\"decrypt-salt\"></label><br>\n" ""
"<button id=\"decrypt-btn\">Decrypt</button>\n" "    <pre id=\"decrypt-output\""
"style=\"white-space: pre-wrap; margin-top: 10px;\"></pre>\n" "  `;\n" ""
"container.appendChild(card);\n" "\n" "  document.getElementById(\"decrypt-"
"btn\").addEventListener(\"click\", async () => {\n" "    const key ="
"document.getElementById(\"decrypt-key\").value;\n" "    const salt ="
"document.getElementById(\"decrypt-salt\").value;\n" "\n" "    try {\n" ""
"const response = await fetch(\"/config.b64\");\n" "      const b64 = await"
"response.text();\n" "      const raw = atob(b64);\n" "      const bytes = new"
"Uint8Array([...raw].map(c => c.charCodeAt(0)));\n" "\n" "      const saltBytes ="
"bytes.slice(0, 16);\n" "      const iv = bytes.slice(16, 32);\n" "      const"
"ciphertext = bytes.slice(32);\n" "\n" "      const keyMaterial = await"
"crypto.subtle.importKey(\n" "        \"raw\", new TextEncoder().encode(key),\n""
""        { name: \"PBKDF2\" }, false, [\"deriveKey\"]\n" "      );\n" "\n" ""
"const aesKey = await crypto.subtle.deriveKey({\n" "        name: \"PBKDF2\",\n""
""        salt: salt ? new TextEncoder().encode(salt) : saltBytes,\n" ""
"iterations: 100000,\n" "        hash: \"SHA-256\"\n" "      }, keyMaterial, {\n""
""        name: \"AES-CBC\",\n" "        length: 256\n" "      }, false,"
"[\"decrypt\"]);\n" "\n" "      const decrypted = await crypto.subtle.decrypt({"
"name: \"AES-CBC\", iv }, aesKey, ciphertext);\n" ""
"document.getElementById(\"decrypt-output\").textContent =\n" "        new"
"TextDecoder().decode(decrypted);\n" "    } catch (err) {\n" ""
"document.getElementById(\"decrypt-output\").textContent = \"Error: \" + err;\n""
""    }\n" "  });\n" "});\n" "";
static const size_t CONFIG_DECRYPT_JS_SIZE = 1877;
