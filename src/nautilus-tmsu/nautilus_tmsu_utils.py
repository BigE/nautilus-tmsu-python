import gi
import os
import subprocess
import sys
import threading

from gi.repository import GLib
from typing import List

try:
	gi.require_version('Gtk', '4.0')
	from gi.repository import Gio, Nautilus
except ValueError as e:
	print(f"Error loading GTK 4.0: {e}")
	sys.exit(1)

__DEBUG__ = bool(os.getenv("NAUTILUS_TMSU_DEBUG"))


def tmsu_add_tags(files: List[str], tags: List[str], notification: bool=True, recursive: bool=False, tmsu="tmsu"):
	cwd = os.path.dirname(files[0]) if not os.path.isdir(files[0]) else files[0]
	args = ["tag"]
	if recursive:
		args.append("-r")
	args += [f"--tags={" ".join(tags)}"] + files
	thread = threading.Thread(
		target=tmsu_run_command,
		args=args,
		kwargs={"cwd": cwd, "notification": notification, "tmsu": tmsu},
		daemon=True
	)
	thread.start()


def tmsu_delete_tag(cwd: str, tag: str, notification: bool=False, tmsu="tmsu"):
	tmsu_run_command("delete", tag, cwd=cwd, notification=notification, tmsu=tmsu)


def tmsu_info(file_info: Nautilus.FileInfo, tmsu="tmsu"):
	path = get_path_from_file_info(file_info, not file_info.is_directory())
	if not path:
		return None
	return tmsu_run_command("info", cwd=path)


def tmsu_untag_file(file: str, tag: str, notification: bool=False, tmsu="tmsu"):
	cwd = os.path.dirname(file if os.path.isdir(file) else os.path.dirname(file))
	tmsu_run_command("untag", file, tag, cwd=cwd, notification=notification, tmsu=tmsu)


def tmsu_get_tags(file_info: Nautilus.FileInfo | None=None, cwd: str | None=None, tmsu="tmsu"):
	args = ["tags", "-1"]
	path = None

	if file_info:
		path = get_path_from_file_info(file_info)
		if path is None:
			raise ValueError(f"Cannot find file {file_info.get_uri()}")
		if cwd is None:
			if file_info.is_directory():
				cwd = path
			else:
				cwd = get_path_from_file_info(file_info, True)
		args.append(path)
	elif cwd is None:
		raise ValueError("You must specify file_info or cwd")

	output = tmsu_run_command(*args, cwd=cwd, tmsu=tmsu)

	if output is None:
		return []

	return output.strip("\n").split("\n")[1:]


def get_path_from_file_info(file_info: Nautilus.FileInfo, parent=False):
	file = file_info.get_location()
	if not isinstance(file, Gio.File):
		return None
	if parent:
		parent_obj = file.get_parent()
		if not isinstance(parent_obj, Gio.File):
			return None
		return parent_obj.get_path()
	return file.get_path()



def tmsu_init_db(path, tmsu="tmsu"):
	if is_in_tmsu_db(path):
		raise ValueError(f"Path {path} already has a TMSU database")
	tmsu_run_command("init", cwd=path, notification=True, tmsu=tmsu)


def is_in_tmsu_db(path: str, tmsu="tmsu"):
	return False if tmsu_run_command("info", cwd=path, tmsu=tmsu) is None else True


def tmsu_run_command(*args, cwd=None, notification=False, tmsu="tmsu"):
	tmsu = which_tmsu(tmsu)
	args = (tmsu, ) + args

	try:
		if __DEBUG__:
			print(args)
		result = subprocess.run(args, capture_output=True, cwd=cwd)
	except Exception as e:
		if notification:
			GLib.idle_add(send_notification, "TMSU Task Failed", str(e))
		return None

	if result.returncode != 0:
		if notification:
			GLib.idle_add(send_notification, "TMSU Task Failed", str(result.stderr))
		return None

	if notification:
		GLib.idle_add(send_notification, "TMSU Task Complete", " ".join(args))
	return result.stdout.decode('UTF-8')


def send_notification(title: str, body: str):
	notification = Gio.Notification()
	notification.set_title(title)
	notification.set_body(body)
	application = Gio.Application.get_default()
	if application:
		application.send_notification(None, notification)


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