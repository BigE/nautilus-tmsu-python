import gi
import sys

try:
	gi.require_version("Gtk", "4.0")
	from gi.repository import Nautilus, Gio, GObject, Gtk
except ValueError as e:
	print(f"Failed to import Gtk 4.0: {str(e)}")
	sys.exit(1)
from typing import List, Literal

from nautilus_tmsu_dialog import NautilusTMSUAddDialog, NautilusTMSUEditDialog
from nautilus_tmsu_object import NautilusTMSUObject
from nautilus_tmsu_utils import get_path_from_file_info, init_tmsu_db, is_tmsu_db, which_tmsu

MENU_ITEM_NAME = "NautilusTMSUMenu"


class NautilusTMSUMenu(NautilusTMSUObject, GObject.Object, Nautilus.MenuProvider):
	def get_file_items(
		self,
		files: List[Nautilus.FileInfo],
	) -> List[Nautilus.MenuItem]:
		if len(files) == 0:
			return []

		path = get_path_from_file_info(files[0], not files[0].is_directory())
		if path is None or not is_tmsu_db(path):
			return []

		menuitem = self._build_tmsu_menu("Tags", "TMSU Tags", files)

		return [
			menuitem,
		]

	def get_background_items(
		self,
		current_folder: Nautilus.FileInfo,
	) -> List[Nautilus.MenuItem]:
		path = get_path_from_file_info(current_folder)

		if path is None:
			return []
		elif not is_tmsu_db(path):
			return [
				self._build_tmsu_init(current_folder)
			]

		menuitem = self._build_tmsu_menu("TagsBackground", "TMSU Tags", [current_folder, ])

		return [
			menuitem,
		]

	def on_alert_dialog_chosen(self, source: Gtk.AlertDialog, result: Gio.AsyncResult, directory: Nautilus.FileInfo):
		response = source.choose_finish(result)
		if response != 1 or not directory.is_directory():
			return

		path = get_path_from_file_info(directory)
		if path:
			init_tmsu_db(path)

	def on_menu_init_activated(self, menu_item: Nautilus.MenuItem, directory: Nautilus.FileInfo):
		application = Gtk.Application.get_default()
		assert isinstance(application, Gtk.Application)
		window = application.get_active_window()
		dialog = Gtk.AlertDialog(modal=True)
		dialog.set_message("Initialize TMSU?")
		dialog.set_detail(f"Are you sure you want to create a TMSU database at \"{directory.get_uri()}\"?")
		dialog.set_buttons(["Cancel", "OK"])
		dialog.choose(window, None, self.on_alert_dialog_chosen, directory)

	def on_menu_item_activated(self, menu_item: Nautilus.MenuItem, action: Literal["add", "edit"], files: List[Nautilus.FileInfo]):
		if action == "add":
			dialog = NautilusTMSUAddDialog(files)
		elif action == "edit":
			if len(files) != 1:
				raise TypeError(f"Edit can only work with 1 file, got {len(files)} files")
			dialog = NautilusTMSUEditDialog(files[0])
		else:
			raise ValueError(f"Unknown action: {action}")

		dialog.present()

	def _build_menu_item(self, name: str, label: str, action: Literal["add", "edit"] | None = None, files: List[Nautilus.FileInfo] = []) -> Nautilus.MenuItem:
		menuitem = Nautilus.MenuItem(name=name, label=label)
		if action and len(files):
			menuitem.connect("activate", self.on_menu_item_activated, action, files)
		return menuitem

	def _build_tmsu_init(self, directory: Nautilus.FileInfo):
		if not directory.is_directory():
			raise TypeError("Cannot build Init menu on non-directory")

		menuitem = self._build_menu_item("Init", "TMSU Initialize", files=[directory, ])
		menuitem.connect("activate", self.on_menu_init_activated, directory)
		return menuitem

	def _build_tmsu_menu(self, name: str, label: str, files: List[Nautilus.FileInfo] = []) -> Nautilus.MenuItem:
		menuitem = self._build_menu_item(name, label)
		submenu = Nautilus.Menu()
		menuitem.set_submenu(submenu)

		add_tags_menuitem = self._build_menu_item(f"{name}::Add", "Add Tags", "add", files)
		submenu.append_item(add_tags_menuitem)

		if len(files) == 1:
			edit_tags_menuitem = self._build_menu_item(f"{name}::Edit", "Edit Tags", "edit", files)
			submenu.append_item(edit_tags_menuitem)

		return menuitem
