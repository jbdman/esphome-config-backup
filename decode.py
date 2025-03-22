import argparse
import base64
import sys
import os
from Crypto.Cipher import AES
from Crypto.Util.Padding import unpad
from Crypto.Protocol.KDF import PBKDF2


def xor_decrypt(data: bytes, key: bytes) -> bytes:
    return bytes([b ^ key[i % len(key)] for i, b in enumerate(data)])

def aes256_decrypt(data: bytes, password: str) -> bytes:
    if len(data) < 32:
        raise ValueError("Invalid AES blob (must include salt and IV)")

    salt = data[:16]
    iv = data[16:32]
    ciphertext = data[32:]

    key = PBKDF2(password, salt=salt, dkLen=32, count=100000)
    cipher = AES.new(key, AES.MODE_CBC, iv)
    return unpad(cipher.decrypt(ciphertext), AES.block_size)


def derive_key(password: str, salt: str) -> bytes:
    print(f"[*] Deriving AES key from password and salt...")
    return PBKDF2(password, salt=salt.encode("utf-8"), dkLen=32, count=100000)

def extract_filename(blob: bytes) -> (str, bytes):
    try:
        first_line_end = blob.index(b"\n")
        first_line = blob[:first_line_end].decode("utf-8").strip()
        if first_line.startswith("# filename:"):
            filename = first_line[len("# filename:"):].strip()
            return filename, blob[first_line_end + 1 :]
    except Exception:
        pass
    return None, blob  # No filename found

def main():
    parser = argparse.ArgumentParser(description="Decode ESPHome embedded config.b64")
    parser.add_argument("input", help="Input file or URL (e.g. config.b64 or http://<device_ip>/config.b64)")
    parser.add_argument("--key", help="Decryption key (required for some encryption types)")
    parser.add_argument("--encryption", choices=["none", "xor", "aes256"], default="none",
                        help="Encryption type used when embedding (default: none)")
    parser.add_argument("-o", "--output", nargs="?", const=True,
                        help="Write output to file. If no filename is given, use embedded filename.")

    args = parser.parse_args()

    # Validate encryption/key/salt combos
    if args.encryption == "none" and args.key:
        print("[!] Error: --key was specified but --encryption is 'none'")
        sys.exit(1)

    if args.encryption == "xor" and not args.key:
        print("[!] Error: --encryption xor requires a --key")
        sys.exit(1)

    if args.encryption == "aes256":
        if not args.key:
            print("[!] Error: --encryption aes256 requires a --key")
            sys.exit(1)

    # Load file or URL
    if args.input.startswith("http://") or args.input.startswith("https://"):
        import requests
        print(f"[*] Downloading: {args.input}")
        resp = requests.get(args.input)
        if not resp.ok:
            print(f"[!] Failed to fetch: {resp.status_code}")
            sys.exit(1)
        b64 = resp.text.strip()
    else:
        with open(args.input, "r", encoding="utf-8") as f:
            b64 = f.read().strip()

    print("[*] Decoding base64...")
    try:
        blob = base64.b64decode(b64)
    except Exception as e:
        print(f"[!] Failed to decode base64: {e}")
        sys.exit(1)

    if args.encryption == "xor":
        print("[*] Decrypting using XOR...")
        blob = xor_decrypt(blob, args.key.encode("utf-8"))
    elif args.encryption == "aes256":
        print("[*] Decrypting using AES-256 (salt and IV extracted from blob)...")
        try:
            blob = aes256_decrypt(blob, args.key)
        except Exception as e:
            print(f"[!] AES decryption failed: {e}")
            sys.exit(1)
    else:
        print("[*] No encryption specified — using plain base64")

    embedded_filename, content = extract_filename(blob)

    if embedded_filename:
        print(f"[*] Embedded filename: {embedded_filename}")
    else:
        print("[*] No embedded filename found")

    # Handle output
    if args.output is None:
        print("[+] Decoded config:\n")
        print(content.decode("utf-8", errors="replace"))
    else:
        if args.output is True:  # User passed just -o with no filename
            if not embedded_filename:
                print("[!] No embedded filename found — cannot infer output filename")
                sys.exit(1)
            output_path = embedded_filename
        else:
            output_path = args.output

        with open(output_path, "wb") as out:
            out.write(content)
        print(f"[+] Written decoded config to {output_path}")

if __name__ == "__main__":
    main()
