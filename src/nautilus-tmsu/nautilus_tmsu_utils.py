import os
import subprocess

def is_tmsu_db(path, tmsu="tmsu"):
	tmsu = which_tmsu(tmsu)
	return False if subprocess.run([tmsu, "info"], capture_output=True, cwd=path).returncode == 1 else True


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