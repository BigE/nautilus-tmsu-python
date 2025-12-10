import gi
import sys

try:
	gi.require_version("Gtk", "4.0")
	from gi.repository import Nautilus, Gio, GObject, Gtk # type: ignore
except ValueError as e:
	print(f"Failed to import Gtk 4.0: {str(e)}")
	sys.exit(1)
from typing import List, Literal

from nautilus_tmsu_commands import NautilusTMSUCommandInit
from nautilus_tmsu_dialog import NautilusTMSUAddDialog, NautilusTMSUEditDialog, NautilusTMSUManageDialog, NautilusTMSURepairDialog
from nautilus_tmsu_object import NautilusTMSUObject
from nautilus_tmsu_runner import is_tmsu_db

MENU_ITEM_NAME = "NautilusTMSUMenu"


class NautilusTMSUMenu(NautilusTMSUObject, GObject.Object, Nautilus.MenuProvider):
	def __init__(self) -> None:
		super().__init__()
		self._current_background_folder: Nautilus.FileInfo | None = None
		self._current_is_in_tmsu_db: bool = False

	@property
	def current_background_folder(self):
		return self._current_background_folder

	@property
	def current_is_in_tmsu_db(self):
		return self._current_is_in_tmsu_db

	def get_file_items(
		self,
		files: List[Nautilus.FileInfo],
	) -> List[Nautilus.MenuItem]:
		if len(files) == 0:
			return []

		if not is_tmsu_db(files[0]):
			return []

		menuitem = self._build_tmsu_menu(f'{MENU_ITEM_NAME}::Tags', 'TMSU Tags', files)

		return [
			menuitem,
		]

	def get_background_items(
		self,
		current_folder: Nautilus.FileInfo,
	) -> List[Nautilus.MenuItem]:
		bypass = True if current_folder == self.current_background_folder else False
		self._current_background_folder = current_folder

		if not bypass:
			self._current_is_in_tmsu_db = is_tmsu_db(current_folder)

		if not self.current_is_in_tmsu_db:
			return [
				self._build_tmsu_init(current_folder)
			]

		name = f'{MENU_ITEM_NAME}::Background'
		files = [current_folder, ]

		tags_menuitem = self._build_tmsu_menu(f'{name}::Tags', 'TMSU Tags', files)
		[database_menuitem, database_submenu] = self._build_submenu_item(f'{name}::Database', 'TMSU Database')
		self._build_menu_item(f'{name}::Database::Manage', 'Manage Tags', action='manage', files=files, menu=database_submenu)
		self._build_repair_menuitem(name, files, database_submenu, True)

		return [
			tags_menuitem,
			database_menuitem,
		]

	def on_alert_dialog_chosen(self, source: Gtk.AlertDialog, result: Gio.AsyncResult, directory: Nautilus.FileInfo):
		response = source.choose_finish(result)
		if response != 1 or not directory.is_directory():
			return

		NautilusTMSUCommandInit(directory).execute()

	def on_menu_init_activated(self, menu_item: Nautilus.MenuItem, directory: Nautilus.FileInfo):
		application = Gtk.Application.get_default()
		assert isinstance(application, Gtk.Application)
		window = application.get_active_window()
		dialog = Gtk.AlertDialog(modal=True)
		dialog.set_message("Initialize TMSU?")
		dialog.set_detail(f"Are you sure you want to create a TMSU database at \"{directory.get_uri()}\"?")
		dialog.set_buttons(["Cancel", "OK"])
		dialog.choose(window, None, self.on_alert_dialog_chosen, directory)

	def on_menu_item_activated(self, menu_item: Nautilus.MenuItem, action: Literal["add", "edit", "manage", 'repair'], files: List[Nautilus.FileInfo], repair_database: bool = False):
		if action == "add":
			dialog = NautilusTMSUAddDialog(files)
		elif action == "edit":
			if len(files) != 1:
				raise TypeError(f"Edit can only work with 1 file, got {len(files)} files")
			dialog = NautilusTMSUEditDialog(files[0])
		elif action == "manage":
			dialog = NautilusTMSUManageDialog(files[0])
		elif action == 'repair':
			dialog = NautilusTMSURepairDialog(files[0], repair_database)
		else:
			raise ValueError(f"Unknown action: {action}")

		dialog.present()

	def _build_menu_item(self, name: str, label: str, *args, action: Literal["add", "edit", "manage", 'repair'] | None = None, files: List[Nautilus.FileInfo] = [], menu: Nautilus.Menu | None = None) -> Nautilus.MenuItem:
		menuitem = Nautilus.MenuItem(name=name, label=label)
		if action and len(files):
			menuitem.connect("activate", self.on_menu_item_activated, action, files, *args)
		if menu:
			menu.append_item(menuitem)
		return menuitem

	def _build_repair_menuitem(self, name: str, files: list[Nautilus.FileInfo] = [], menu: Nautilus.Menu | None = None, repair_database: bool = False):
		self._build_menu_item(f'{name}::Repair', 'Repair Tags', action='repair', files=files, menu=menu, *[repair_database, ])

	def _build_submenu_item(self, name: str, label: str, menu: Nautilus.Menu | None = None) -> tuple[Nautilus.MenuItem, Nautilus.Menu]:
		menuitem = self._build_menu_item(name, label)
		submenu = Nautilus.Menu()
		menuitem.set_submenu(submenu)
		if menu:
			menu.append_item(menuitem)
		return (menuitem, submenu)

	def _build_tmsu_init(self, directory: Nautilus.FileInfo):
		if not directory.is_directory():
			raise TypeError("Cannot build Init menu on non-directory")

		menuitem = self._build_menu_item("Init", "TMSU Initialize", files=[directory, ])
		menuitem.connect("activate", self.on_menu_init_activated, directory)
		return menuitem

	def _build_tmsu_menu(self, name: str, label: str, files: List[Nautilus.FileInfo] = []) -> Nautilus.MenuItem:
		[menuitem, submenu] = self._build_submenu_item(name, label)
		self._build_menu_item(f"{name}::Add", "Add Tags", action="add", files=files, menu=submenu)

		if len(files) == 1:
			self._build_menu_item(f"{name}::Edit", "Edit Tags", action="edit", files=files, menu=submenu)
			if files[0].is_directory():
				self._build_repair_menuitem(name, files, submenu)

		return menuitem
