from types import SimpleNamespace as sn

from cryptography.hazmat.primitives import padding, hashes
from cryptography.hazmat.primitives.ciphers import modes


aes = sn(
	padder=sn(
		python=apadding.PKCS7,
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