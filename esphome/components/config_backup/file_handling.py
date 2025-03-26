# file_handling.py

import base64
from . import encryption, compression

def embedFile(path: str, **kwargs) -> bytes:
    # File embedding implementation...

def to_c_array(data: bytes, array_name: str) -> str:
    # C array conversion implementation...

def to_int_list_string(data: bytes) -> str:
    return ", ".join(str(b) for b in data)