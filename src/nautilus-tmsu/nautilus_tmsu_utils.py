import gi
import os
import subprocess
import sys

try:
	gi.require_version('Gtk', '4.0')
	from gi.repository import Gtk, Nautilus
except ValueError as e:
	print(f"Error loading GTK 4.0: {e}")
	sys.exit(1)


def find_nautilus_window() -> Gtk.Window | None:
	"""
	The final fallback method: Finds an active Gtk.Window by listing all toplevels.

	This is often the most reliable method when Gdk surface/popup APIs are blocked
	or incorrect in PyGObject bindings on Wayland.
	"""

	# 1. Get a list of all Gtk.Window objects currently managed by the process.
	toplevels = Gtk.Window.list_toplevels()

	if not toplevels:
		print("Error: No Gtk.Window objects found in the process.")
		return None

	# 2. Iterate and return the first one found that is active/visible.
	# In a typical Nautilus extension process, one of these will be the main Nautilus window.
	window: Gtk.Window
	for window in toplevels:
		# We can apply heuristics, but often simply taking the first one works,
		# or checking if it's currently focused.
		if window.is_visible():
			application = window.get_application()
			if application and application.get_application_id() == 'org.gnome.Nautilus':
				# We don't want to assume the first visible top-level window
				# is the Nautilus instance. Instead we check the application_id
				# to ensure we're returning Nautilus
				return window

	print("Warning: Found windows, but none were visible/active.")
	return None


def get_tmsu_tags(file_info: Nautilus.FileInfo, tmsu="tmsu"):
	file = file_info.get_location()
	tmsu = which_tmsu(tmsu)
	print(f"Getting tags for {file.get_path()}")
	result = subprocess.run([tmsu, "tags", file.get_path(), "-1"], capture_output=True, text=True, cwd=file.get_path() if file_info.is_directory() else file.get_parent().get_path())

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