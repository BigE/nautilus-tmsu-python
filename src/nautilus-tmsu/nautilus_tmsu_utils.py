import os

from gi.repository import Nautilus
from urllib.parse import unquote


def get_path_from_file_info(file_info: Nautilus.FileInfo, force_dir: bool = False):
	if force_dir and not file_info.is_directory():
		return unquote(file_info.get_parent_uri())[7:]
	return unquote(file_info.get_uri())[7:]


def which_tmsu(tmsu="tmsu"):
	def is_exe(fpath):
		return os.path.isfile(fpath) and os.access(fpath, os.X_OK)

	fpath, fname = os.path.split(tmsu)
	if fpath and is_exe(tmsu):
		return tmsu
	else:
		for path in os.environ.get("PATH", "").split(os.pathsep):
			exe_file = os.path.join(path, tmsu)
			if is_exe(exe_file):
				return exe_file

	raise ValueError("Command `tmsu` is not available on $PATH")