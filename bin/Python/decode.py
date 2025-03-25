import argparse
import base64
import sys
import os
import gzip
import globalv

# We now switch fully to the "cryptography" library for AES:
#from cryptography.hazmat.primitives import padding as aes_padding
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms #, modes
from cryptography.hazmat.backends import default_backend
#from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC



def xor_decrypt(data: bytes, key: bytes) -> bytes:
    return bytes([b ^ key[i % len(key)] for i, b in enumerate(data)])

def aes256_decrypt(data: bytes, password: str) -> bytes:
    if len(data) < 32:
        raise ValueError("Invalid AES blob (must include salt and IV)")

    salt = data[:16]
    iv = data[16:32]
    ciphertext = data[32:]

    key = deriveKey(password, salt)
    cipher = Cipher(algorithms.AES(key), globalv.aes.mode.python(iv), backend=default_backend())
    decryptor = cipher.decryptor()
    decrypted = decryptor.update(ciphertext) + decryptor.finalize()

    unpadder = globalv.aes.padder.python(128).unpadder()
    unpadded = unpadder.update(decrypted) + unpadder.finalize()

    return unpadded


def deriveKey(passphrase: str, salt: bytes) -> bytes:
    """
    Derive a 256-bit key from passphrase + salt using PBKDF2/HMAC-SHA256 from cryptography.
    """
    kdf = PBKDF2HMAC(
        algorithm=globalv.aes.PBKDF2.algorithm.python(),
        length=globalv.aes.PBKDF2.length.python,
        salt=salt,
        iterations=globalv.aes.PBKDF2.iterations.python,
        backend=default_backend()
    )
    return kdf.derive(passphrase.encode('utf-8'))

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
    parser.add_argument("--compression", choices=["none","gzip"], default="none",
                        help="Compression type used when embedding (default: none)"),
    parser.add_argument("-o", "--output", nargs="?", const=True,
                        help="Write output to file. If no filename is given, use embedded filename.")

    args = parser.parse_args()

    # Validate encryption/key/salt combos
    if (args.encryption == "none" and args.key) and not (args.input.startswith("http://") or args.input.startswith("https://")):
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
        encryption = resp.headers['X-Encryption-Type'] if 'X-Encryption-Type' in resp.headers else "none"
        compress = resp.headers['X-Compression-Type'] if 'X-Compression-Type' in resp.headers else "none"
        if args.encryption == "none" and encryption != "none":
            print(f"[*] Read encryption type from X-Encryption-Type header: {encryption}")
            args.encryption = encryption
        if args.compression == "none" and compress != "none":
            print(f"[*] Read compression type from X-Compression-Type header: {compress}")
            args.compression = compress
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

    if args.compression == "gzip":
        print("[*] Decompressing gzip blob...")
        blob = gzip.decompress(blob)

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
