# ESPHome Config Backup Component

This project provides a custom ESPHome component for backing up a device's active configuration. It embeds the encoded, compressed, and encrypted yaml config in the embedded firmware. It allows export of the config via a web interface, supporting AES256 encryption, XOR, and plaintext.

## 🧩 Features

- Backup ESPHome device configuration at compile time
- Encrypt configuration backups using AES256 or XOR
- Serve config data through an endpoint on the integrated web_server
- Optional GUI widget for in-browser config decryption and download
- External component for easy integration

---

## 🛠️ Installation

1. Add this repository as an external component in your ESPHome YAML:

```yaml
external_components:
  - source: github://jbdman/esphome-config-backup
    components: [ config_backup ]
```

2. Add the `config_backup` component block:

```yaml
config_backup:
  encryption: aes256  # Options: none, xor, aes256
  key: !secret config_backup_key
  # debug: print.b64  # Optional: enable debugging logs
  # gui: True         # Optional: enable GUI on web server
```

3. Example of a complete minimal ESPHome config:

```yaml
esphome:
  name: config-backup-demo
  platform: ESP32
  board: esp32dev

wifi:
  ssid: !secret wifi_ssid
  password: !secret wifi_password
  fast_connect: true

web_server:
  port: 80

external_components:
  - source: github://jbdman/esphome-config-backup
    components: [ config_backup ]

config_backup:
  encryption: aes256
  key: !secret config_backup_key
```

---

## 🔐 Encryption Methods

The config data can be encrypted before transmission:

- `none`: No encryption (plaintext)
- `xor`: Basic XOR-based obfuscation using a password
- `aes256`: Secure encryption using AES-256 with a password used to derive a key (default)

---

## 🧪 Decoder Scripts

To decrypt the exported config files, use one of the included decoder tools in the `bin/` directory, or try the web gui component (enabled by default).

### 🔧 Decoder Tools:

- **Windows**  
  `decode.bat` — Wrapper script to launch the decoder in Windows

- **Linux/macOS**  
  `decode.sh` — Shell launcher for the Python decoder

- **Cross-platform / Direct**  
  `bin/Python/decode.py` — Main decoder logic (requires Python 3 and the `cryptography` library)

---

### ✅ Usage

```bash
python3 bin/Python/decode.py <input_file_or_url> [--key KEY] [--encryption TYPE] [--compression TYPE] [-o [OUTPUT]]
```

### 🔑 Arguments

| Flag               | Description                                                                 |
|--------------------|-----------------------------------------------------------------------------|
| `<input>`          | Input file path **or** direct URL (e.g. `http://device_ip/config.b64`)     |
| `--key`            | Decryption key (required for XOR/AES256)                                    |
| `--encryption`     | Force decryption method: `none` (default), `xor`, or `aes256`               |
| `--compression`    | Decompression method: `none` (default) or `gzip`                            |
| `-o`, `--output`   | Optional output path. If omitted, config is printed. If no filename given, embedded filename is used if present |

---

### 🔄 Examples

#### Decrypt from local file:

```bash
python3 bin/Python/decode.py backup.b64 --key mysecretkey --encryption aes256 --compression gzip -o
```

#### Decrypt directly from a device over HTTP:

```bash
python3 bin/Python/decode.py http://192.168.4.1/config.b64 --key mysecretkey --encryption xor -o config.yaml
```

If `-o` is used without a filename, and the embedded config contains a filename, that will be used.

---

## 📁 Repository Structure

```
.
├── esphome/
│   └── components/
│       └── config_backup/
│           ├── __init__.py         # Component registration
│           ├── config_backup.h     # Main C++ logic
│           └── config-decrypt.js   # Decryption script (XOR & AES256)
├── example.yaml                    # Sample device config
├── example-config-aes256-mysecretkey/
├── example-config-xor-mysecretkey/
├── .gitignore
├── .gitmodules
├── LICENSE
└── bin/                            # (Contains utilities)
```

---

## 📄 License

This project is licensed under the [GNU GPLv3](LICENSE).

---

## 🙌 Credits

Created by [jbdman](https://github.com/jbdman)  
Designed for hobbyist and advanced ESPHome users who want a fallback or secure backup of device configuration.
