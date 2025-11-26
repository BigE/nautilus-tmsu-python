from gi.repository import Nautilus, GObject, Gio
from typing import List, Literal

from nautilus_tmsu_dialog import NautilusTMSUAddDialog, NautilusTMSUEditDialog
from nautilus_tmsu_utils import is_tmsu_db, which_tmsu

MENU_ITEM_NAME = "NautilusTMSUMenu"


class NautilusTMSUMenu(GObject.Object, Nautilus.MenuProvider):

	def __init__(self):
		super()
		self.tmsu = which_tmsu()
		if self.tmsu is None:
			raise ValueError("Cannot find `tmsu` on $PATH")

	def get_file_items(
		self,
		files: List[Nautilus.FileInfo],
	) -> List[Nautilus.MenuItem]:
		if len(files) == 0:
			return []

		for file_info in files:
			file = file_info.get_location()
			if not isinstance(file, Gio.File):
				raise TypeError("Unknown type {file.__class__}")
			path = None
			if file_info.is_directory():
				path = file.get_path()
			else:
				parent = file.get_parent()
				if parent and isinstance(parent, Gio.File):
					path = parent.get_path()
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
		file = current_folder.get_location()
		if isinstance(file, Gio.File) and not is_tmsu_db(file.get_path()):
			return []

		menuitem = self._build_tmsu_menu("TagsBackground", "TMSU Tags", [current_folder, ])

		return [
			menuitem,
		]

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
