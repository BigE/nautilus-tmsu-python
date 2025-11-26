import gi
import re
import sys

try:
	gi.require_version("Adw", "1")
	from gi.repository import Adw, Gio, Gtk, Nautilus
except ValueError as e:
	print(f"Error loading Adw 1: {e}")
	sys.exit(1)

from typing import List

from nautilus_tmsu_utils import add_tmsu_tags, delete_tmsu_tag, get_tmsu_tags


class NautilusTMSUDialog(Gtk.ApplicationWindow):
	_files: List[Nautilus.FileInfo]

	def __init__(self, title, parent_window: Gtk.Window, application: Gtk.Application | None, files: List[Nautilus.FileInfo]):
		super().__init__(application=application, title=title)
		self._files = files

		self.set_modal(True)
		self.set_transient_for(parent_window)


class NautilusTMSUAddDialog(NautilusTMSUDialog):
	def __init__(self, parent_window: Gtk.Window, application: Gtk.Application | None, files: List[Nautilus.FileInfo]):
		super().__init__("TMSU Add Tags", parent_window, application, files)

		self.set_default_size(400, 150)

		vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12)
		vbox.append(Gtk.Label(label=f"Add (space-separated) tags to {len(files)} file{"" if len(files) == 1 else "s"}"))
		entry = Gtk.Entry(activates_default=True)
		vbox.append(entry)
		completion = Gtk.EntryCompletion()
		entry.set_completion(completion)
		completion_model = Gtk.ListStore(str)
		cwd = None
		location = files[0].get_location()
		if not isinstance(location, Gio.File):
			raise ValueError
		if files[0].is_directory() and isinstance(location, Gio.File):
			cwd = str(location.get_path())
		else:
			parent = location.get_parent()
			if isinstance(parent, Gio.File):
				cwd = str(parent.get_path())
		for item in get_tmsu_tags(cwd=cwd):
			completion_model.append([item, ])
		completion.set_model(completion_model)
		completion.set_text_column(0)

		button_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10, halign=Gtk.Align.CENTER, hexpand=True)
		vbox.append(button_box)

		save_button = Gtk.Button(label="Save")
		button_box.append(save_button)
		save_button.connect("clicked", self._on_clicked_add_tags, entry)

		cancel_button = Gtk.Button(label="Canecl")
		button_box.append(cancel_button)
		cancel_button.connect("clicked", lambda btn: self.destroy())

		self.set_child(vbox)
		self.set_default_widget(save_button)

	def _on_clicked_add_tags(self, button: Gtk.Button, entry: Gtk.Entry):
		text = str(entry.get_text())
		tags = re.findall(r"((?:\\ |[^ ])+)", text)
		files = []
		for file in self._files:
			location = file.get_location()
			if not isinstance(location, Gio.File):
				continue
			path = location.get_path()
			if path:
				files.append(path)
		add_tmsu_tags(files, tags)
		self.destroy()

class NautilusTMSUEditDialog(NautilusTMSUDialog):
	def __init__(self, parent_window: Gtk.Window, application: Gtk.Application | None, file: Nautilus.FileInfo):
		super().__init__("TMSU Edit Tags", parent_window, application, [file, ])

		self.set_default_size(400, 500)

		vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
		vbox.set_margin_bottom(20)
		vbox.set_margin_end(20)
		vbox.set_margin_start(20)
		vbox.set_margin_top(20)
		tag_listbox = Gtk.ListBox(selection_mode=Gtk.SelectionMode.NONE)
		vbox.append(tag_listbox)
		tag_listbox.add_css_class("boxed-list")

		for tag in self.get_existing_tags():
			row = Adw.ActionRow(title=tag)
			tag_listbox.append(row)
			delete_button = Gtk.Button(icon_name="user-trash-symbolic")
			delete_button.add_css_class("destructive-action")
			delete_button.add_css_class("flat")
			row.add_suffix(delete_button)
			delete_button.connect("clicked", lambda btn: self.delete_existing_tag(file, tag, row, tag_listbox))

		self.set_child(vbox)

	def delete_existing_tag(self, file_info: Nautilus.FileInfo, tag: str, row: Gtk.ListBoxRow, tag_listbox: Gtk.ListBox):
		file = file_info.get_location()
		if not isinstance(file, Gio.File):
			return
		path = file.get_path()
		if path:
			try:
				delete_tmsu_tag(str(path), tag)
				tag_listbox.remove(row)
			except:
				pass

	def get_existing_tags(self):
		tags = []
		for file in self._files:
			tags += get_tmsu_tags(file_info=file)
		return set(tags)
