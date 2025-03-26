import gzip

class Compressor:

	def __init__(self, type: str):
		self.type = type
		if self.type == 'gzip':
			self.compress = gzip.compress
			self.decompress = gzip.decompress
		elif self.type == 'none':
			self.compress = self._none
			self.decompress = self._none

	def _none(self, data: bytes) -> bytes:
		return data