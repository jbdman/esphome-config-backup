window.addEventListener("DOMContentLoaded", () => {
  const container = document.querySelector(".cards");
  if (!container) return;

  const card = document.createElement("div");
  card.className = "card";
  card.innerHTML = `
    <h2>Decrypt Embedded Config</h2>
    <label>Key: <input type="text" id="decrypt-key"></label><br>
    <label>Salt: <input type="text" id="decrypt-salt"></label><br>
    <button id="decrypt-btn">Decrypt</button>
    <pre id="decrypt-output" style="white-space: pre-wrap; margin-top: 10px;"></pre>
  `;
  container.appendChild(card);

  document.getElementById("decrypt-btn").addEventListener("click", async () => {
    const key = document.getElementById("decrypt-key").value;
    const salt = document.getElementById("decrypt-salt").value;

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
      document.getElementById("decrypt-output").textContent =
        new TextDecoder().decode(decrypted);
    } catch (err) {
      document.getElementById("decrypt-output").textContent = "Error: " + err;
    }
  });
});
