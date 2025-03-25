//dummy comment
(function () {
  'use strict';

  /**
   * Waits for an element matching the given selector
   * to appear in the DOM, optionally scoped within the provided root.
   * @param {string} selector - The CSS selector to watch for.
   * @param {HTMLElement|Document} [root=document] - The root element/document to observe.
   * @returns {Promise<HTMLElement>} A promise that resolves with the found element.
   */
  function waitForElement(selector, root = document) {
    return new Promise(function (resolve) {
      const found = root.querySelector(selector);
      if (found) {
        return resolve(found);
      }

      const observer = new MutationObserver(function () {
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

  /**
   * Waits for a shadow root to exist on the given element.
   * @param {HTMLElement} element - The element that should have a shadowRoot.
   * @returns {Promise<ShadowRoot>} A promise that resolves with the element's shadow root.
   */
  function waitForShadowRoot(element) {
    return new Promise(function (resolve) {
      if (element.shadowRoot) {
        return resolve(element.shadowRoot);
      }

      const observer = new MutationObserver(function () {
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

  /**
   * Decrypts an AES-256 (CBC) encrypted, Base64-encoded string.
   * The decrypted result is returned as another Base64 string,
   * which can then be processed further (e.g. GZip decompression).
   * @param {string} base64Data - The encrypted, Base64-encoded data.
   * @param {string} password - The passphrase used for AES decryption.
   * @returns {string} A Base64-encoded string of the decrypted data.
   */
  function aes256DecryptToBase64(base64Data, password) {
    const data = CryptoJS.enc.Base64.parse(base64Data);

    // We need at least 8 words: 4 for the salt, 4 for the IV.
    if (data.words.length < 8) {
      throw new Error('Invalid AES blob (must include salt and IV).');
    }

    const salt = CryptoJS.lib.WordArray.create(data.words.slice(0, 4));
    const iv = CryptoJS.lib.WordArray.create(data.words.slice(4, 8));
    const ciphertext = CryptoJS.lib.WordArray.create(data.words.slice(8));

    // Derive AES key via PBKDF2
    const key = CryptoJS.PBKDF2(password, salt, {
      keySize: 256 / {{aes.PBKDF2.length}},
      iterations: {{aes.PBKDF2.iterations}},
      hasher: {{aes.PBKDF2.algorithm}}
    });

    // Decrypt using AES-256 CBC
    const decrypted = CryptoJS.AES.decrypt({
      ciphertext: ciphertext
    }, key, {
      iv: iv,
      mode: {{aes.mode}},
      padding: {{aes.padder}}
    });

    return CryptoJS.enc.Base64.stringify(decrypted);
  }

  /**
   * Decompresses a GZip-encoded Base64 string using browser DecompressionStream.
   * @param {string} base64Data - The data to decompress, encoded in Base64.
   * @returns {Promise<string>} A promise that resolves to the decompressed string.
   */
  async function decompressGzipBase64(base64Data) {
    // Convert base64 string to a Uint8Array
    const compressedBytes = Uint8Array.from(
      atob(base64Data),
      (c) => c.charCodeAt(0)
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

  /**
   * Decrypts and decompresses a Base64 string based on the encryption type.
   * @param {string} encryptedBase64 - The Base64 data to be decrypted.
   * @param {string} password - The passphrase for AES/XOR.
   * @param {string} encryption - The encryption type ("aes256", "xor", or "none").
   * @returns {Promise<string>} The fully decrypted, decompressed plaintext.
   */
  async function decryptAndDecompress(encryptedBase64, password, encryption) {
    // Default to the raw input; if "aes256" or "xor", decrypt first.
    let gzBase64 = encryptedBase64;

    if (encryption === 'aes256') {
      gzBase64 = aes256DecryptToBase64(encryptedBase64, password);
    } else if (encryption === 'xor') {
      gzBase64 = xorDecryptBase64Base64(encryptedBase64, password);
    }

    // Decompress the resulting GZip data
    const plaintext = await decompressGzipBase64(gzBase64);
    return plaintext;
  }

  /**
   * Decrypts AES-256 (CBC) data from a Base64 string, returning UTF-8 plaintext.
   * @param {string} base64Data - The AES-256 (CBC) encrypted, Base64-encoded data.
   * @param {string} password - The passphrase.
   * @returns {string} The decrypted plaintext in UTF-8.
   */
  function aes256Decrypt(base64Data, password) {
    const data = CryptoJS.enc.Base64.parse(base64Data);

    if (data.words.length < 8) {
      throw new Error('Invalid AES blob (must include salt and IV).');
    }

    const salt = CryptoJS.lib.WordArray.create(data.words.slice(0, 4));
    const iv = CryptoJS.lib.WordArray.create(data.words.slice(4, 8));
    const ciphertext = CryptoJS.lib.WordArray.create(data.words.slice(8));

    const key = CryptoJS.PBKDF2(password, salt, {
      keySize: 256 / {{aes.PBKDF2.length}},
      iterations: {{aes.PBKDF2.iterations}},
      hasher: {{aes.PBKDF2.algorithm}}
    });

    const decrypted = CryptoJS.AES.decrypt({
      ciphertext: ciphertext
    }, key, {
      iv: iv,
      mode: {{aes.mode}},
      padding: {{aes.padder}}
    });

    return CryptoJS.enc.Utf8.stringify(decrypted);
  }

  /**
   * Converts a Base64 string to a Uint8Array.
   * @param {string} base64Str - The Base64-encoded data.
   * @returns {Uint8Array} The raw bytes as a typed array.
   */
  function base64ToUint8Array(base64Str) {
    const binaryStr = atob(base64Str);
    const len = binaryStr.length;
    const bytes = new Uint8Array(len);

    for (let i = 0; i < len; i++) {
      bytes[i] = binaryStr.charCodeAt(i);
    }
    return bytes;
  }

  /**
   * Performs XOR decryption on the input data using the given passphrase,
   * assuming the input is Base64-encoded.
   * @param {string} base64Data - The Base64-encoded ciphertext.
   * @param {string} passphrase - The XOR key.
   * @returns {string} The decrypted text (UTF-8).
   */
  function xorDecryptBase64(base64Data, passphrase) {
    const dataBytes = base64ToUint8Array(base64Data);
    const keyBytes = new TextEncoder().encode(passphrase);
    const output = new Uint8Array(dataBytes.length);

    for (let i = 0; i < dataBytes.length; i++) {
      output[i] = dataBytes[i] ^ keyBytes[i % keyBytes.length];
    }

    return new TextDecoder().decode(output);
  }

  /**
   * Performs XOR decryption on the input data using the given passphrase,
   * returning a Base64-encoded string.
   * @param {string} base64Data - The Base64-encoded ciphertext.
   * @param {string} passphrase - The XOR key.
   * @returns {string} The decrypted data, re-encoded in Base64.
   */
  function xorDecryptBase64Base64(base64Data, passphrase) {
    const dataBytes = base64ToUint8Array(base64Data);
    const keyBytes = new TextEncoder().encode(passphrase);
    const output = new Uint8Array(dataBytes.length);

    for (let i = 0; i < dataBytes.length; i++) {
      output[i] = dataBytes[i] ^ keyBytes[i % keyBytes.length];
    }

    return btoa(output);
  }

  /**
   * Attempts to extract a filename from the first line of the provided text.
   * Expected format: "# filename: some_file.yaml"
   * If not found, a default filename is generated.
   * @param {string} fileText - The text that may contain a filename.
   * @returns {{ filename: string, fileData: string }}
   */
  function extractFilenameAndData(fileText) {
    const newlineIndex = fileText.indexOf('\n');

    if (newlineIndex !== -1) {
      const firstLine = fileText.substring(0, newlineIndex).trim();
      if (firstLine.startsWith('# filename:')) {
        const filename = firstLine.substring('# filename:'.length).trim();
        const fileData = fileText.substring(newlineIndex + 1);
        return { filename, fileData };
      }
    }

    // Fallback if no filename comment is found
    return {
      filename: (window.location.hostname + '.yaml'),
      fileData: fileText
    };
  }

  /**
   * Triggers a file download in the browser for the given text data.
   * @param {string} fileContents - The contents to download.
   * @param {string} [filename] - The name of the file to be saved.
   */
  function triggerDownload(fileContents, filename) {
    if (!filename) {
      const hostname = window.location.hostname || 'download';
      filename = hostname + '.yaml';
    }

    const blob = new Blob([fileContents], { type: 'application/octet-stream' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = filename;
    document.body.appendChild(a);
    a.click();

    setTimeout(function () {
      document.body.removeChild(a);
      URL.revokeObjectURL(url);
    }, 0);
  }

  /**
   * Injects a minimal Config Backup widget into the ESPHome Dashboard interface.
   * This widget allows the user to provide a passphrase and attempt to download
   * a decrypted copy of the firmware configuration.
   */
  async function injectConfigBackupWidget() {
    // Wait for the main <esp-app> element
    const app = await waitForElement('esp-app');
    const shadow = await waitForShadowRoot(app);
    if (!shadow) {
      return console.warn('No shadowRoot on <esp-app>');
    }

    // Wait for the main content area and the left column
    const main = await waitForElement('main.flex-grid-half', shadow);
    const sections = main.querySelectorAll('section.col');
    const leftCol = sections[0];

    // Ensure the standard update form is present before injecting
    await waitForElement('form[action="/update"]', leftCol);

    // Create our wrapper element for the backup UI
    const wrapper = document.createElement('div');
    wrapper.innerHTML =
      '<h2>Config Backup</h2>' +
      '<form id="config-backup-form">' +
        '<input id="decrypt-key" placeholder="Key" />&nbsp;' +
        '<input class="btn" type="submit" value="Decrypt" />' +
      '</form>' +
      '<pre id="decrypt-output" style="white-space: pre-wrap; margin-top: 10px;"></pre>';

    leftCol.appendChild(wrapper);

    // Attach event listener to our newly inserted form
    shadow.getElementById('config-backup-form').addEventListener('submit', async function (e) {
      e.preventDefault();

      const srcElement = e.target;
      const passphrase = srcElement.querySelector('#decrypt-key').value;
      srcElement.parentElement.querySelector('#decrypt-output').textContent = '';

      try {
        const response = await fetch('{{path}}');
        const encryption = response.headers.get('X-Encryption-Type');
        const compress = response.headers.get('X-Compression-Type');
        const b64 = await response.text();
        let plaintext = '';

        // If the data is GZip compressed, attempt to decrypt & decompress
        if (compress === 'gzip') {
          plaintext = await decryptAndDecompress(b64, passphrase, encryption);
        } else {
          // If no compression, handle decryption directly
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
          throw new Error('Decryption failed — possibly wrong key?');
        }

        // Extract optional filename or default to <hostname>.yaml
        const { filename, fileData } = extractFilenameAndData(plaintext);
        triggerDownload(fileData, filename);

      } catch (err) {
        srcElement.parentElement.querySelector('#decrypt-output').textContent =
          '❌ Error: ' + err.message;
        console.error(err);
      }
    });
  }

  // Attach the backup widget once the DOM is loaded, or immediately if already loaded.
  if (document.readyState === 'loading') {
    console.log('Attaching listener...');
    document.addEventListener('DOMContentLoaded', injectConfigBackupWidget);
  } else {
    injectConfigBackupWidget();
  }
})();
