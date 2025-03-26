# encryption.py

from cryptography.hazmat.primitives.ciphers import Cipher, algorithms
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
import secrets
import globalv

class Encryptor:

	def __init__(self, type: str, passphrase: str):
		valid_types = ('none', 'xor', 'aes256')
		if type not in valid_types:
			raise ValueError(f"Type must be one of {valid_types}")
		self.type = type
		self._encryptor = eval(f'self._{self.type}_encrypt')
		self._salt = secrets.token_bytes(16)
		self._key = self._derive_key(passphrase, self._salt)


	def _xor_encrypt(self, data: bytes, key: bytes) -> bytes:
		return bytes(d ^ key[i % len(key)] for i, d in enumerate(data))
	
	def _aes256_encrypt(self, data: bytes, key: bytes) -> bytes:
		"""
		AES-256 encryption (CBC) with a random IV prepended.
		This matches the snippet you mentioned, ensuring the key must be 16, 24, or 32 bytes.
		"""
		if len(key) not in (16, 24, 32):
			raise ValueError("AES key must be 16, 24, or 32 bytes long")
		iv = secrets.token_bytes(16)
		padder = globalv.aes.padder.python(128).padder()
		padded_data = padder.update(data) + padder.finalize()
		cipher = Cipher(algorithms.AES(key), globalv.aes.mode.python(iv), backend=default_backend())
		encryptor = cipher.encryptor()
		encrypted = encryptor.update(padded_data) + encryptor.finalize()
		return iv + encrypted

	def _none_encrypt(self, data: bytes, key: bytes) -> bytes:
		return data
	
	def _derive_key(self, passphrase: str, salt: bytes) -> bytes:
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

	def reset(self):
		del self._key
		del self._salt

	def set_passphrase(self, passphrase: str):
		self._salt = secrets.token_bytes(16)
		self._key = self._deriveKey(passphrase, self._salt)

	def set_type(self, type: str):
		valid_types = ('none', 'xor', 'aes256')
		if type not in valid_types:
			raise ValueError(f"Type must be one of {valid_types}")
		self.type = type
		self._encryptor = eval(f'self._{self.type}_encrypt')

	def encrypt(self, data: bytes) -> bytes:
		return self._salt + self._encryptor(data, self._key)
