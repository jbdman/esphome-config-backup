import argparse
import base64
import sys

def xor_decrypt(data: bytes, key: bytes) -> bytes:
    return bytes([b ^ key[i % len(key)] for i, b in enumerate(data)])

def main():
    parser = argparse.ArgumentParser(description="Decode ESPHome embedded config.b64")
    parser.add_argument("input", help="Input file or URL (e.g. config.b64 or http://<device_ip>/config.b64)")
    parser.add_argument("--key", help="XOR decryption key (if encrypted)")
    parser.add_argument("-o", "--output", help="Write output to file instead of stdout")
    args = parser.parse_args()

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
    blob = base64.b64decode(b64)

    if args.key:
        print("[*] Decrypting using XOR...")
        blob = xor_decrypt(blob, args.key.encode("utf-8"))
    else:
        print("[*] No key provided — assuming unencrypted")

    if args.output:
        with open(args.output, "wb") as out:
            out.write(blob)
        print(f"[+] Written decoded config to {args.output}")
    else:
        print("[+] Decoded config:\n")
        print(blob.decode("utf-8", errors="replace"))

if __name__ == "__main__":
    main()
