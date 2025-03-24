function waitForElement(selector, root=(document)) {
    return new Promise((resolve) => {
        const found = root.querySelector(selector);
        if (found)
            return resolve(found);
        const observer = new MutationObserver(() => {
            const el = root.querySelector(selector);
            if (el) {
                observer.disconnect();
                resolve(el);
            }
        });
        observer.observe(root, {
            childList: true,
            subtree: true
        });
    });
}

function waitForShadowRoot(element) {
    return new Promise((resolve) => {
        if (element.shadowRoot)
            return resolve(element.shadowRoot);
        const observer = new MutationObserver(() => {
            if (element.shadowRoot) {
                observer.disconnect();
                resolve(element.shadowRoot);
            }
        });
        observer.observe(element, {
            childList: false,
            subtree: false,
            attributes: true
        });
    });
}

// 1) Decrypt the AES blob (AES-256 CBC) using CryptoJS.
//    Our AES function returns a base64-encoded string that
//    actually contains GZIP-compressed bytes.
function aes256DecryptToBase64(base64Data, password) {
    const data = CryptoJS.enc.Base64.parse(base64Data);
    if (data.words.length < 8) {
        throw new Error("Invalid AES blob (must include salt and IV).");
    }
    const salt = CryptoJS.lib.WordArray.create(data.words.slice(0, 4));
    const iv = CryptoJS.lib.WordArray.create(data.words.slice(4, 8));
    const ciphertext = CryptoJS.lib.WordArray.create(data.words.slice(8));
    const key = CryptoJS.PBKDF2(password, salt, {
        keySize: 256 / 32,
        iterations: 100000
    });
    const decrypted = CryptoJS.AES.decrypt({
        ciphertext: ciphertext
    }, key, {
        iv: iv,
        mode: CryptoJS.mode.CBC,
        padding: CryptoJS.pad.Pkcs7
    });
    return CryptoJS.enc.Base64.stringify(decrypted);
}

// 2) Decompress the GZIP from a base64 string using the built-in
//    DecompressionStream in modern browsers.
async function decompressGzipBase64(base64Data) {
    // Convert base64 string to a Uint8Array
    const compressedBytes = Uint8Array.from(
        atob(base64Data),
        c => c.charCodeAt(0)
    );

    // Create a GZIP DecompressionStream
    const cs = new DecompressionStream('gzip');
    const writer = cs.writable.getWriter();

    // Feed in the compressed bytes
    writer.write(compressedBytes);
    writer.close();

    // Read the decompressed result as ArrayBuffer, then decode
    const arrayBuffer = await new Response(cs.readable).arrayBuffer();
    return new TextDecoder().decode(arrayBuffer);
}

// 3) Put it all together in a single helper function.
async function decryptAndDecompress(encryptedBase64, password, encryption) {
    // AES-decrypt to base64-encoded GZIP bytes
    var gzBase64 = encryptedBase64;
    if (encryption == "aes256") {
        gzBase64 = aes256DecryptToBase64(encryptedBase64, password);
    } else if (encryption == "xor") {
        gzBase64 = xorDecryptBase64Base64(encryptedBase64, password);
    }

    // Decompress the GZIP
    const plaintext = await decompressGzipBase64(gzBase64);
    return plaintext;
}

function aes256Decrypt(base64Data, password) {
    const data = CryptoJS.enc.Base64.parse(base64Data);
    if (data.words.length < 8) {
        throw new Error("Invalid AES blob (must include salt and IV).");
    }
    const salt = CryptoJS.lib.WordArray.create(data.words.slice(0, 4));
    const iv = CryptoJS.lib.WordArray.create(data.words.slice(4, 8));
    const ciphertext = CryptoJS.lib.WordArray.create(data.words.slice(8));
    const key = CryptoJS.PBKDF2(password, salt, {
        keySize: 256 / 32,
        iterations: 100000
    });
    const decrypted = CryptoJS.AES.decrypt({
        ciphertext: ciphertext
    }, key, {
        iv: iv,
        mode: CryptoJS.mode.CBC,
        padding: CryptoJS.pad.Pkcs7
    });
    return CryptoJS.enc.Utf8.stringify(decrypted);
}

function base64ToUint8Array(base64Str) {
    const binaryStr = atob(base64Str);
    const len = binaryStr.length;
    const bytes = new Uint8Array(len);
    for (let i = 0; i < len; i++) {
        bytes[i] = binaryStr.charCodeAt(i);
    }
    return bytes;
}

function xorDecryptBase64(base64Data, passphrase) {
    const dataBytes = base64ToUint8Array(base64Data);
    const keyBytes = new TextEncoder().encode(passphrase);
    const output = new Uint8Array(dataBytes.length);
    for (let i = 0; i < dataBytes.length; i++) {
        output[i] = dataBytes[i] ^ keyBytes[i % keyBytes.length];
    }
    return new TextDecoder().decode(output);
}

function xorDecryptBase64Base64(base64Data, passphrase) {
    const dataBytes = base64ToUint8Array(base64Data);
    const keyBytes = new TextEncoder().encode(passphrase);
    const output = new Uint8Array(dataBytes.length);
    for (let i = 0; i < dataBytes.length; i++) {
        output[i] = dataBytes[i] ^ keyBytes[i % keyBytes.length];
    }
    return btoa(output);
}

function extractFilenameAndData(fileText) {
    const newlineIndex = fileText.indexOf('\n');
    if (newlineIndex !== -1) {
        const firstLine = fileText.substring(0, newlineIndex).trim();
        if (firstLine.startsWith('# filename:')) {
            const filename = firstLine.substring('# filename:'.length).trim();
            const fileData = fileText.substring(newlineIndex + 1);
            return {
                filename,
                fileData
            };
        }
    }
    return {
        filename: (window.location.hostname + '.yaml'),
        fileData: fileText
    };
}

function triggerDownload(fileContents, filename) {
    if (!filename) {
        const hostname = window.location.hostname || 'download';
        filename = `${hostname}.yaml`;
    }
    const blob = new Blob([fileContents], {
        type: 'application/octet-stream'
    });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = filename;
    document.body.appendChild(a);
    a.click();
    setTimeout(() => {
        document.body.removeChild(a);
        URL.revokeObjectURL(url);
    }, 0);
}
async function injectConfigBackupWidget() {
    // console.log("Injecting");
    const app = await waitForElement("esp-app");
    // console.log("Rendered.");
    const shadow = await waitForShadowRoot(app);
    if (!shadow) return console.warn("No shadowRoot on <esp-app>");

    const main = await waitForElement("main.flex-grid-half", shadow);
    const sections = main.querySelectorAll("section.col");
    const leftCol = sections[0];

    await waitForElement('form[action="/update"]', leftCol);

    const wrapper = document.createElement("div");
    wrapper.innerHTML = `<h2>Config Backup</h2><form id="config-backup-form"><input id="decrypt-key" placeholder="Key" />&nbsp;<input class="btn" type="submit" value="Decrypt"></form><pre id="decrypt-output" style="white-space: pre-wrap; margin-top: 10px;"></pre>`;

    leftCol.appendChild(wrapper);

    shadow.getElementById("config-backup-form").addEventListener("submit", async (e) => {
        e.preventDefault();

        const srcElement = e.target;
        const passphrase = srcElement.querySelector("#decrypt-key").value;
        srcElement.parentElement.querySelector("#decrypt-output").textContent = "";

        try {
            const response = await fetch("{{path}}");
            const encryption = response.headers.get("X-Encryption-Type");
            const compress = response.headers.get("X-Compression-Type");
            const b64 = await response.text();
            let plaintext = "";
            if (compress == "gzip") {
                plaintext = await decryptAndDecompress(b64, passphrase, encryption)
            } else {
                switch (encryption) {
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
            }

            if (!plaintext) {
                throw new Error("Decryption failed — possibly wrong key?");
            }

            const { filename, fileData } = extractFilenameAndData(plaintext);
            triggerDownload(fileData, filename);
        } catch (err) {
            srcElement.parentElement.querySelector("#decrypt-output").textContent =
                "❌ Error: " + err.message;
                console.error(err);
        }
    });
}

if (document.readyState === "loading") {
    console.log("Attaching listener...")
    document.addEventListener("DOMContentLoaded", injectConfigBackupWidget);
} else {
    injectConfigBackupWidget();
}