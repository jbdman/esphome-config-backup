import argparse
import base64
import sys

def xor_decrypt(data: bytes, key: bytes) -> bytes:
    return bytes([b ^ key[i % len(key)] for i, b in enumerate(data)])

def main():
    parser = argparse.ArgumentParser(description="Decode ESPHome embedded config.b64")
    parser.add_argument("input", help="Input file or URL (e.g. config.b64 or http://<device_ip>/config.b64)")
    parser.add_argument("--key", help="Decryption key (required for some encryption types)")
    parser.add_argument("--encryption", choices=["none", "xor"], default="none",
                        help="Encryption type used when embedding (default: none)")
    parser.add_argument("-o", "--output", help="Write output to file instead of stdout")
    args = parser.parse_args()

    # Validate encryption/key combo
    if args.encryption == "none" and args.key:
        print("[!] Error: --key was specified but --encryption is 'none'")
        print("    If the config was not encrypted, remove the --key argument.")
        sys.exit(1)

    if args.encryption == "xor" and not args.key:
        print("[!] Error: --encryption xor requires a --key")
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

    # Handle decryption
    if args.encryption == "xor":
        print("[*] Decrypting using XOR...")
        blob = xor_decrypt(blob, args.key.encode("utf-8"))
    else:
        print("[*] No encryption specified — using plain base64")

    # Output result
    if args.output:
        with open(args.output, "wb") as out:
            out.write(blob)
        print(f"[+] Written decoded config to {args.output}")
    else:
        print("[+] Decoded config:\n")
        print(blob.decode("utf-8", errors="replace"))

if __name__ == "__main__":
    main()
