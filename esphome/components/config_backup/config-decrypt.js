function waitForElement(selector, root=document) {
    return new Promise( (resolve) => {
        const found = root.querySelector(selector);
        if (found)
            return resolve(found);
        const observer = new MutationObserver( () => {
            const el = root.querySelector(selector);
            if (el) {
                observer.disconnect();
                resolve(el);
            }
        }
        );
        observer.observe(root, {
            childList: true,
            subtree: true
        });
    }
    );
}
function waitForShadowRoot(element) {
    return new Promise( (resolve) => {
        if (element.shadowRoot)
            return resolve(element.shadowRoot);
        const observer = new MutationObserver( () => {
            if (element.shadowRoot) {
                observer.disconnect();
                resolve(element.shadowRoot);
            }
        }
        );
        observer.observe(element, {
            childList: false,
            subtree: false,
            attributes: true
        });
    }
    );
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
    const blob = new Blob([fileContents],{
        type: 'application/octet-stream'
    });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = filename;
    document.body.appendChild(a);
    a.click();
    setTimeout( () => {
        document.body.removeChild(a);
        URL.revokeObjectURL(url);
    }
    , 0);
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
    wrapper.innerHTML = `
        <h2>Config Backup</h2>
        <form id="config-backup-form">
          <input id="decrypt-key" placeholder="Key" />
          <nbsp> </nbsp>
          <input class="btn" type="submit" value="Decrypt">
        </form>
        <pre id="decrypt-output" style="white-space: pre-wrap; margin-top: 10px;"></pre>
    `;

    leftCol.appendChild(wrapper);

    shadow.getElementById("config-backup-form").addEventListener("submit", async (e) => {
        e.preventDefault();

        const srcElement = e.target;
        const passphrase = srcElement.querySelector("#decrypt-key").value;
        srcElement.parentElement.querySelector("#decrypt-output").textContent = "";

        try {
            const response = await fetch("/config.b64");
            const encryption = response.headers.get("X-Encryption-Type");
            const b64 = await response.text();
            let plaintext = "";

            switch(encryption) {
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
        } catch (err) {
            srcElement.parentElement.querySelector("#decrypt-output").textContent =
                "❌ Error: " + err.message;
        }
    });
}

if (document.readyState === "loading") {
    console.log("Attaching listener...")
    document.addEventListener("DOMContentLoaded", injectConfigBackupWidget);
} else {
  injectConfigBackupWidget();
}

