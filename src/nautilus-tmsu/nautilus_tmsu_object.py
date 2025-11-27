import os

class NautilusTMSUObject(object):
	def __init__(self) -> None:
		self._debug = bool(os.getenv("NAUTILUS_TMSU_DEBUG"))

	@property
	def debug(self):
		return self._debug
