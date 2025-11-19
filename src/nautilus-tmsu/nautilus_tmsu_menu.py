from gi.repository import Nautilus, GObject, Gio
from typing import List

from nautilus_tmsu_utils import is_tmsu_db, which_tmsu

MENU_ITEM_NAME = "NautilusTMSUMenu"


class NautilusTMSUMenu(GObject.GObject, Nautilus.MenuProvider):

	def __init__(self):
		super()
		self.tmsu = which_tmsu()
		if self.tmsu is None:
			raise ValueError("Cannot find `tmsu` on $PATH")

	def get_file_items(
		self,
		files: List[Nautilus.FileInfo],
	) -> List[Nautilus.MenuItem]:
		for file_info in files:
			file: Gio.File = file_info.get_location()
			if not is_tmsu_db(file.get_path() if file_info.is_directory() else file.get_parent().get_path()):
				return []

		return [
			self._build_tmsu_menu(files),
		]

	def get_background_items(
		self,
		current_folder: Nautilus.FileInfo,
	) -> List[Nautilus.MenuItem]:
		file = current_folder.get_location()
		if not is_tmsu_db(file.get_path()):
			return []

		return [
			self._build_tmsu_menu([current_folder]),
		]

	def _build_tmsu_menu(self, files: List[Nautilus.FileInfo]):
		menuitem = self._build_menu_item("Tags", "TMSU Tags")
		submenu = Nautilus.Menu()
		menuitem.set_submenu(submenu)

		add_tags_menuitem = self._build_menu_item("Add_Tags", "Add Tags", files)
		submenu.append_item(add_tags_menuitem)

		if len(files) == 1:
			edit_tags_menuitem = self._build_menu_item("Edit_Tags", "Edit Tags", files)
			submenu.append_item(edit_tags_menuitem)

		return menuitem

	def _build_menu_item(self, action, label, files: List[Nautilus.FileInfo]=[], callback=None):
		menuitem = Nautilus.MenuItem(
			name=f"{MENU_ITEM_NAME}::{action}",
			label=label
		)

		if callback:
			menuitem.connect("activate", callback, files)
		return menuitem
