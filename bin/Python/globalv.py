from types import SimpleNamespace as sn
from cryptography.hazmat.primitives import padding as aes_padding
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

aes = sn(
	padder=sn(
		python=aes_padding.PKCS7(128).padder(),
		javascript="CryptoJS.pad.Pkcs7"
	),
)