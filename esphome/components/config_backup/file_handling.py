# file_handling.py

import base64
from . import encryption, compression

def embedFile(
    path: str,
    read_mode: str = 'text',
    placeholder_replace: dict = None,
    mangle: callable = None,
    compress_first: bool = True,
    encrypt: str = 'none',
    key: str = None,
    final_base64: bool = True,
    compress_after_b64: bool = True,
    add_filename_comment: bool = False
) -> bytes:
    """
    Read a file from `path` (text or binary), optionally insert a filename comment,
    do placeholder replacement, minify if needed, compress, encrypt, base64, etc.
    Returns the final bytes, suitable for embedding.
    """
    if read_mode == 'text':
        with open(path, 'r', encoding='utf-8') as f:
            raw_str = f.read()
        data = raw_str.encode('utf-8')
    else:
        with open(path, 'rb') as f:
            data = f.read()

    if add_filename_comment:
        filename = os.path.basename(path)
        comment = f"# filename: {filename}\n".encode('utf-8')
        data = comment + data

    if placeholder_replace:
        text_str = data.decode('utf-8')
        for old, new in placeholder_replace.items():
            text_str = text_str.replace(old, new)
        data = text_str.encode('utf-8')

    if mangle:
        data = mangle(data)

    if compress_first:
        data = gzip.compress(data)

    if encrypt == 'xor':
        if not key:
            raise ValueError("XOR encryption requires a 'key'.")
        data = xor_encrypt(data, key.encode('utf-8'))
    elif encrypt == 'aes256':
        if not key:
            raise ValueError("AES-256 encryption requires a 'key'.")
        salt_bytes = secrets.token_bytes(16)
        derived_key = deriveKey(key, salt_bytes)
        data = salt_bytes + aes256_encrypt(data, derived_key)
    elif encrypt == 'none':
        pass
    else:
        raise ValueError(f"Unsupported encryption type: {encrypt}")

    if final_base64:
        data = base64.b64encode(data)

    if compress_after_b64:
        data = gzip.compress(data)

    return data

def to_c_array(data: bytes, array_name: str) -> str:
    """
    Convert bytes to comma-separated integers in a C++ array, plus size variable.
    Example:
        const uint8_t CONFIG_B64[123] PROGMEM = { ... };
        const size_t CONFIG_B64_SIZE = 123;
    """
    bytes_as_int = ", ".join(str(b) for b in data)
    length = len(data)
    return (f"const uint8_t {array_name}[{length}] PROGMEM = {{{bytes_as_int}}};\n"
            f"const size_t {array_name}_SIZE = {length};")

def to_int_list_string(data: bytes) -> str:
    return ", ".join(str(b) for b in data)

def from_int_list_string(data_str: str) -> bytes:
    """
    Converts a comma-and-space-separated string of integers into a bytes object.
    
    Example:
        "65, 66, 67" → b'ABC'
    """
    return bytes(int(x) for x in data_str.split(','))