from types import SimpleNamespace as sn

padder = 

aes = sn(
	padder=sn(
		python=aes_padding.PKCS7(128).padder(),
		javascript="CryptoJS.pad.Pkcs7"
	),
)