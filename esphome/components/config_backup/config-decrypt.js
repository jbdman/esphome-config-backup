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

async function injectConfigBackupWidget() {
  const app = await waitForElement("esp-app");
  const shadow = app.shadowRoot;
  if (!shadow) return console.warn("No shadowRoot on <esp-app>");

  const main = await waitForElement("main.flex-grid-half", shadow);
  const sections = main.querySelectorAll("section.col");
  const leftCol = sections[0]; // first column has the forms

  const wrapper = document.createElement("div");
  wrapper.innerHTML = `
    <h2>Config Backup</h2>
    <form id="config-backup-form">
      <input id="decrypt-key" placeholder="Key" />
      <input id="decrypt-salt" placeholder="Salt (optional)" />
      <input class="btn" type="submit" value="Decrypt">
    </form>
    <pre id="decrypt-output" style="white-space: pre-wrap; margin-top: 10px;"></pre>
  `;

  leftCol.appendChild(wrapper);

  shadow.getElementById("config-backup-form").addEventListener("submit", async (e) => {
    e.preventDefault();

    const srcElement = (e.target||e.srcElement)
    const key = srcElement.querySelector("#decrypt-key").value;
    const salt = srcElement.querySelector("#decrypt-salt").value;

    try {
      const response = await fetch("/config.b64");
      const b64 = await response.text();
      const raw = atob(b64);
      const bytes = new Uint8Array([...raw].map(c => c.charCodeAt(0)));

      const saltBytes = bytes.slice(0, 16);
      const iv = bytes.slice(16, 32);
      const ciphertext = bytes.slice(32);

      const keyMaterial = await crypto.subtle.importKey(
        "raw", new TextEncoder().encode(key),
        { name: "PBKDF2" }, false, ["deriveKey"]
      );

      const aesKey = await crypto.subtle.deriveKey({
        name: "PBKDF2",
        salt: salt ? new TextEncoder().encode(salt) : saltBytes,
        iterations: 100000,
        hash: "SHA-256"
      }, keyMaterial, {
        name: "AES-CBC",
        length: 256
      }, false, ["decrypt"]);

      const decrypted = await crypto.subtle.decrypt({ name: "AES-CBC", iv }, aesKey, ciphertext);
      srcElement.parentElement.querySelector("#decrypt-output").textContent =
        new TextDecoder().decode(decrypted);
    } catch (err) {
      srcElement.parentElement.querySelector("#decrypt-output").textContent = "Error: " + err;
    }
  });
}

injectConfigBackupWidget();
