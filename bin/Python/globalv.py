from types import SimpleNamespace as sn

from cryptography.hazmat.primitives import padding as aes_padding
from cryptography.hazmat.primitives.ciphers import modes #Cipher, algorithms, 
#from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import hashes
#from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

aes = sn(
	padder=sn(
		python=aes_padding.PKCS7,
		javascript="CryptoJS.pad.Pkcs7"
	),
	mode=sn(
		python=modes.CBC,
		javascript="CryptoJS.mode.CBC"
	),
	PBKDF2=sn(
		algorithm=sn(
			python=hashes.SHA256,
			javascript="CryptoJS.algo.SHA256"
		),
		iterations=sn(
			python=100_000,
			javascript="100000"
		),
		length=sn(
			python=32,
			javascript="32"
		)
	)
)