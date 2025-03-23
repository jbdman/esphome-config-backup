function waitForElement(selector, root = document) {
    return new Promise((resolve) => {
        const found = root.querySelector(selector);
        if (found) return resolve(found);
        const observer = new MutationObserver(() => {
            const el = root.querySelector(selector);
            if (el) {
                observer.disconnect();
                resolve(el);
            }
        });
        observer.observe(root, { childList: true, subtree: true });
    });
}

function waitForShadowRoot(element) {
  return new Promise((resolve) => {
    if (element.shadowRoot) return resolve(element.shadowRoot);

    const observer = new MutationObserver(() => {
      if (element.shadowRoot) {
        observer.disconnect();
        resolve(element.shadowRoot);
      }
    });

    observer.observe(element, { childList: false, subtree: false, attributes: true });
  });
}


function aes256Decrypt(base64Data, password) {
  // Parse the Base64-encoded data into a CryptoJS WordArray.
  const data = CryptoJS.enc.Base64.parse(base64Data);

  // In CryptoJS, WordArrays are organized by 32-bit words (4 bytes each).
  // So:
  //   - Salt (16 bytes) is 16 / 4 = 4 words
  //   - IV   (16 bytes) is another 4 words
  //   - The rest is the ciphertext
  if (data.words.length < 8) {
    throw new Error("Invalid AES blob (must include salt and IV).");
  }

  // Extract salt, IV, and ciphertext from the WordArray
  const salt       = CryptoJS.lib.WordArray.create(data.words.slice(0, 4));
  const iv         = CryptoJS.lib.WordArray.create(data.words.slice(4, 8));
  const ciphertext = CryptoJS.lib.WordArray.create(data.words.slice(8));

  // Derive the AES-256 key via PBKDF2 (100,000 iterations),
  // matching dkLen=32 bytes from the Python example
  const key = CryptoJS.PBKDF2(password, salt, {
    keySize: 256 / 32,       // 256 bits / 32 bits per word = 8 words
    iterations: 100000
  });

  // Perform AES-256-CBC decryption
  // Note the object structure { ciphertext: ... } is required for CryptoJS
  const decrypted = CryptoJS.AES.decrypt(
    { ciphertext: ciphertext },
    key,
    {
      iv: iv,
      mode: CryptoJS.mode.CBC,
      padding: CryptoJS.pad.Pkcs7
    }
  );

  // Convert decrypted WordArray into a UTF-8 string
  // (or handle as needed if you want raw bytes)
  return CryptoJS.enc.Utf8.stringify(decrypted);
}

/**
 * Decodes a Base64 string to a Uint8Array
 *
 * @param {string} base64Str - The Base64-encoded string
 * @returns {Uint8Array} - Decoded bytes
 */
function base64ToUint8Array(base64Str) {
  // Decode base64 into a standard ASCII string
  const binaryStr = atob(base64Str);

  // Create a new Uint8Array of the same length
  const len = binaryStr.length;
  const bytes = new Uint8Array(len);

  // Populate the array
  for (let i = 0; i < len; i++) {
    bytes[i] = binaryStr.charCodeAt(i);
  }
  return bytes;
}

/**
 * XOR decrypts a Base64-encoded payload using the provided passphrase (string).
 * The passphrase is treated as UTF-8 bytes. The decrypted output is returned as a UTF-8 string.
 *
 * @param {string} base64Data   - Base64-encoded data to XOR
 * @param {string} passphrase   - The passphrase (string), which is converted into bytes
 * @returns {string} - Decrypted data interpreted as UTF-8 text
 */
function xorDecryptBase64(base64Data, passphrase) {
  // Decode the Base64 data into bytes
  const dataBytes = base64ToUint8Array(base64Data);

  // Convert the passphrase (string) into UTF-8 bytes
  const keyBytes = new TextEncoder().encode(passphrase);

  // XOR the data
  const output = new Uint8Array(dataBytes.length);
  for (let i = 0; i < dataBytes.length; i++) {
    output[i] = dataBytes[i] ^ keyBytes[i % keyBytes.length];
  }

  // Convert the XORed bytes back into a UTF-8 string
  return new TextDecoder().decode(output);
}


/**
 * Extract a filename (if present) from the first line of the text data.
 * The first line must start with "# filename:" to be recognized.
 * 
 * @param {string} fileText - Decrypted file contents (as text).
 * @returns {{ filename: string|null, fileData: string }}
 *   - filename: The extracted filename, or null if not found
 *   - fileData: The remaining file contents (with the filename line removed)
 */
function extractFilenameAndData(fileText) {
  // Look for the first newline
  const newlineIndex = fileText.indexOf('\n');
  if (newlineIndex !== -1) {
    // Extract the first line
    const firstLine = fileText.substring(0, newlineIndex).trim();
    // Check if it starts with '# filename:'
    if (firstLine.startsWith('# filename:')) {
      const filename = firstLine.substring('# filename:'.length).trim();
      const fileData = fileText.substring(newlineIndex + 1);
      return { filename, fileData };
    }
  }

  // No filename found
  return { filename: (window.location.hostname + '.yaml'), fileData: fileText };
}

/**
 * Trigger a browser download for fileText under the specified or derived filename.
 *
 * @param {string|Uint8Array|ArrayBuffer} fileContents - The actual file data (text or binary).
 * @param {string|null} [filename] - The filename to download as. If null/undefined, we default to `${window.location.hostname}.yaml`.
 */
function triggerDownload(fileContents, filename) {
  // If no filename found, default to "hostname.yaml"
  if (!filename) {
    const hostname = window.location.hostname || 'download';
    filename = `${hostname}.yaml`;
  }

  // If fileContents is a string, just pass it in.
  // If fileContents is a Uint8Array or ArrayBuffer, you can also pass that to Blob directly.
  const blob = new Blob([fileContents], { type: 'application/octet-stream' });
  const url = URL.createObjectURL(blob);

  // Create a temporary <a> element to trigger the download
  const a = document.createElement('a');
  a.href = url;
  a.download = filename;
  document.body.appendChild(a);
  a.click();

  // Cleanup
  setTimeout(() => {
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  }, 0);
}



async function injectConfigBackupWidget() {
    const app = await waitForElement("esp-app");
    const shadow = await waitForShadowRoot(app);
    if (!shadow) return console.warn("No shadowRoot on <esp-app>");

    const main = await waitForElement("main.flex-grid-half", shadow);
    const sections = main.querySelectorAll("section.col");
    const leftCol = sections[0]; // first column has the forms

    const wrapper = document.createElement("div");
    wrapper.innerHTML = `
    <h2>Config Backup</h2>
    <form id="config-backup-form">
      <input id="decrypt-key" placeholder="Key" />
      <input class="btn" type="submit" value="Decrypt">
    </form>
    <pre id="decrypt-output" style="white-space: pre-wrap; margin-top: 10px;"></pre>
  `;

    leftCol.appendChild(wrapper);

    shadow.getElementById("config-backup-form").addEventListener("submit", async (e) => {
        e.preventDefault();

        const srcElement = e.target || e.srcElement;
        const passphrase = srcElement.querySelector("#decrypt-key").value;
        srcElement.parentElement.querySelector("#decrypt-output").textContent = "";

        try {
            const response = await fetch("/config.b64");
            const encryption = response.headers.get("X-Encryption-Type");
            const b64 = await response.text();
            var plaintext = "";
            switch(encryption){
              case 'aes256':
                plaintext = aes256Decrypt(b64, passphrase);
                break;
              case 'xor':
                plaintext = xorDecryptBase64(b64, passphrase);
                break;
              case 'none':
              default:
                plaintext = atob(b64);
                break;
            }
            if (!plaintext) {
                throw new Error("Decryption failed — possibly wrong key?");
            }

            const { filename, fileData } = extractFilenameAndData(plaintext);
            triggerDownload(fileData, filename);

            // srcElement.parentElement.querySelector("#decrypt-output").textContent = plaintext;
        } catch (err) {
            srcElement.parentElement.querySelector("#decrypt-output").textContent =
                "❌ Error: " + err.message;
        }
    });
}

injectConfigBackupWidget();
