import gi
import os
import subprocess
import sys

from typing import List

try:
	gi.require_version('Gtk', '4.0')
	from gi.repository import Gio, Gtk, Nautilus
except ValueError as e:
	print(f"Error loading GTK 4.0: {e}")
	sys.exit(1)


def add_tmsu_tags(files: List[str], tags: List[str], recursive: bool=False, tmsu="tmsu"):
	tmsu = which_tmsu(tmsu)
	cwd = os.path.dirname(files[0]) if not os.path.isdir(files[0]) else files[0]
	args = [tmsu, "tag"]
	if recursive:
		args.append("-r")
	args += [f"--tags=\"{" ".join(tags)}\"", " ".join(files)]
	result = subprocess.run(args, capture_output=True, text=True, cwd=cwd)

	if result.returncode != 0:
		raise ValueError(result.stderr)


def delete_tmsu_tag(file: str, tag: str, tmsu="tmsu"):
	tmsu = which_tmsu(tmsu)
	cwd = os.path.dirname(file if os.path.isdir(file) else os.path.dirname(file))
	result = subprocess.run([tmsu, "untag", file, tag], capture_output=True, text=True, cwd=cwd)

	if result.returncode != 0:
		raise ValueError(result.stderr)


def get_tmsu_tags(file_info: Nautilus.FileInfo | None=None, cwd: str | None=None, tmsu="tmsu"):
	tmsu = which_tmsu(tmsu)
	args = [tmsu, "tags", "-1"]

	if file_info:
		file = file_info.get_location()
		if not isinstance(file, Gio.File):
			raise ValueError()
		path = file.get_path()
		if path is None:
			raise ValueError(f"Cannot find file {file.get_uri()}")
		print(f"Getting tags for {path}")
		if cwd is None:
			if file_info.is_directory():
				cwd = str(file.get_path())
			else:
				parent = file.get_parent()
				if isinstance(parent, Gio.File):
					cwd = str(parent.get_path())
		args.append(str(path))
	elif cwd is None:
		raise ValueError("You must specify file_info or cwd")
	result = subprocess.run(args, capture_output=True, text=True, cwd=cwd)


	if result.returncode != 0:
		print(result.stderr)
		return []

	return [item.replace('\\ ', ' ') for item in result.stdout.strip("\n").split("\n")[1:]]


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