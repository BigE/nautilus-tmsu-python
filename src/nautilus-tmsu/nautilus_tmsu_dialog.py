import gi
import re
import sys

try:
	gi.require_version("Adw", "1")
	from gi.repository import Adw, Gio, Gtk, Nautilus
except ValueError as e:
	print(f"Error loading Adw 1: {e}")
	sys.exit(1)

from typing import Callable, List, TypeAlias

from nautilus_tmsu_utils import get_path_from_file_info, tmsu_add_tags, tmsu_delete_tag, tmsu_get_tags, tmsu_info, tmsu_untag_file


TMSUCallback: TypeAlias = Callable[[str, str], None]


class NautilusTMSUDialog(Gtk.ApplicationWindow):
	_files: List[Nautilus.FileInfo]

	def __init__(self, title, files: List[Nautilus.FileInfo]):
		application = Gtk.Application.get_default()
		if not isinstance(application, Gtk.Application) or application.get_application_id() != "org.gnome.Nautilus":
			raise TypeError("Unable to find Gtk.Application with application_id of \"org.gnome.Nautilus\"")
		window = application.get_active_window()
		super().__init__(application=application, modal=True, title=title, transient_for=window)
		self._files = files
		vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10, hexpand=True, vexpand=True)
		vbox.set_margin_bottom(20)
		vbox.set_margin_end(20)
		vbox.set_margin_start(20)
		vbox.set_margin_top(20)
		self.set_child(vbox)

	def is_single_directory(self):
		return self.is_single_item() and self._files[0].is_directory()

	def is_single_item(self):
		return len(self._files) == 1


class NautilusTMSUAddDialog(NautilusTMSUDialog):
	def __init__(self, files: List[Nautilus.FileInfo]):
		super().__init__("TMSU Add Tags", files)

		self.set_default_size(400, 150)

		vbox = self.get_child()
		assert isinstance(vbox, Gtk.Box)
		vbox.append(Gtk.Label(label=f"Add (space-separated) tags to {len(files)} file{"" if len(files) == 1 else "s"}"))
		entry = Gtk.Entry(activates_default=True)
		vbox.append(entry)
		completion = Gtk.EntryCompletion()
		entry.set_completion(completion)
		completion_model = Gtk.ListStore(str)
		cwd = get_path_from_file_info(files[0], not files[0].is_directory())
		switch = None
		for item in tmsu_get_tags(cwd=cwd):
			completion_model.append([item, ])
		completion.set_model(completion_model)
		completion.set_text_column(0)

		# completion logic
		completion.set_match_func(self._completion_match, entry)
		completion.connect("match-selected", self.on_match_selected, entry)

		if self.is_single_directory():
			switch_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10, hexpand=True)
			vbox.append(switch_box)
			switch_box.append(Gtk.Label(label="Apply tags recursively", hexpand=True))
			switch = Gtk.Switch()
			switch_box.append(switch)

		button_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10, halign=Gtk.Align.CENTER, hexpand=True)
		vbox.append(button_box)

		save_button = Gtk.Button(label="Save")
		button_box.append(save_button)
		save_button.connect("clicked", self._on_clicked_add_tags, entry, switch)

		cancel_button = Gtk.Button(label="Canecl")
		button_box.append(cancel_button)
		cancel_button.connect("clicked", lambda btn: self.destroy())

		self.set_child(vbox)
		self.set_default_widget(save_button)

	def get_current_word_info(self, entry: Gtk.Entry):
		"""
		Helper to find the word under the cursor.
		Returns: (word_text, start_index, end_index)
		"""
		text = entry.get_text()
		cursor_pos = entry.get_position()

		# Find the start of the word (move left until space or start)
		start = cursor_pos
		while start > 0 and text[start - 1] != ' ':
			start -= 1

		# Find the end of the word (move right until space or end)
		end = cursor_pos
		while end < len(text) and text[end] != ' ':
			end += 1

		return text[start:end], start, end

	def on_match_selected(self, completion, model, iter, entry: Gtk.Entry):
		"""
		Custom insertion: Replaces only the current word, not the whole line.
		"""
		selected_word = model[iter][0]
		current_word, start, end = self.get_current_word_info(entry)

		# Get the current full text
		full_text = entry.get_text()

		# Construct the new text:
		# (Text before word) + (Selected completion) + (Text after word)
		new_text = full_text[:start] + selected_word + full_text[end:]

		entry.set_text(new_text)

		# Move cursor to the end of the inserted word
		entry.set_position(start + len(selected_word))

		# Return True to stop the default handler (which would replace the whole line)
		return True

	def _completion_match(self, completion, key, iter, entry: Gtk.Entry):
		"""
		Custom matcher: checks if the model row matches the current word fragment.
		"""
		# Get the word currently being typed
		current_word, _, _ = self.get_current_word_info(entry)

		# If the word is empty, don't show completion
		if not current_word:
			return False

		# Get the potential match from the model
		model = completion.get_model()
		if not model:
			return False
		row_value = model[iter][0]

		# Check if the model value starts with our partial word (case insensitive)
		return row_value.lower().startswith(current_word.lower())

	def _on_clicked_add_tags(self, button: Gtk.Button, entry: Gtk.Entry, switch: Gtk.Switch | None):
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
		tmsu_add_tags(files, tags, recursive=switch.get_active() if switch else False)
		self.destroy()


class NautilusTMSUEditTagListDialog(NautilusTMSUDialog):
	def __init__(self, title, file_info: Nautilus.FileInfo, tmsu_callback: TMSUCallback):
		super().__init__(title, [file_info, ])

		self.set_default_size(400, 500)

		vbox = self.get_child()
		assert isinstance(vbox, Gtk.Box)
		scroll_window = Gtk.ScrolledWindow(vexpand=True)
		vbox.append(scroll_window)
		tag_listbox = Gtk.ListBox(selection_mode=Gtk.SelectionMode.NONE)
		scroll_window.set_child(tag_listbox)
		tag_listbox.add_css_class("boxed-list")

		for tag in self.get_existing_tags():
			row = Adw.ActionRow(title=tag.replace('\\ ', ' '))
			tag_listbox.append(row)
			delete_button = Gtk.Button(icon_name="user-trash-symbolic")
			delete_button.add_css_class("destructive-action")
			delete_button.add_css_class("flat")
			row.add_suffix(delete_button)
			delete_button.connect("clicked", self.on_delete_button_clicked, file_info, tag, row, tag_listbox, tmsu_callback)

		self.set_child(vbox)

	@property
	def delete_dialog_detail(self) -> str:
		raise NotImplementedError()

	def delete_existing_tag(self, file_info: Nautilus.FileInfo, tag: str, row: Adw.ActionRow, tag_listbox: Gtk.ListBox, tmsu_callback: TMSUCallback):
		path = get_path_from_file_info(file_info, not file_info.is_directory())
		if path:
			try:
				tmsu_callback(path, tag)
				tag_listbox.remove(row)
			except:
				pass

	def get_existing_tags(self):
		raise NotImplementedError()

	def on_delete_button_clicked(self, button: Gtk.Button, file_info: Nautilus.FileInfo, tag: str, row: Adw.ActionRow, tag_listbox: Gtk.ListBox, tmsu_callback: TMSUCallback):
		dialog = Gtk.AlertDialog()
		dialog.set_buttons(["OK", "Cancel"])
		dialog.set_cancel_button(1)
		dialog.set_default_button(0)
		dialog.set_detail(self.delete_dialog_detail.format(tag=tag, file=file_info.get_uri()))
		dialog.set_message("Confirm Tag Deletion")
		dialog.choose(self, None, self.on_delete_dialog_choose_finish, file_info, tag, row, tag_listbox, tmsu_callback)

	def on_delete_dialog_choose_finish(self, dialog: Gtk.AlertDialog, result: Gio.AsyncResult, file_info: Nautilus.FileInfo, tag: str, row: Adw.ActionRow, tag_listbox: Gtk.ListBox, tmsu_callback: TMSUCallback):
		response = dialog.choose_finish(result)
		if response == 0:
			self.delete_existing_tag(file_info, tag, row, tag_listbox, tmsu_callback)


class NautilusTMSUEditDialog(NautilusTMSUEditTagListDialog):
	def __init__(self, file: Nautilus.FileInfo):
		super().__init__("TMSU Edit Tags", file, tmsu_untag_file)

	@property
	def delete_dialog_detail(self):
		return "Are you sure you want to remove the tag \"{tag}\" from the file {file}"

	def get_existing_tags(self):
		tags = []
		for file in self._files:
			tags += tmsu_get_tags(file_info=file)
		return set(tags)


class NautilusTMSUManageDialog(NautilusTMSUEditTagListDialog):
	def __init__(self, file: Nautilus.FileInfo):
		super().__init__("TMSU Manage Tags", file, tmsu_delete_tag)

	@property
	def delete_dialog_detail(self):
		return "Are you sure you want to remove the tag \"{tag}\" from the database at {file}?"

	def get_existing_tags(self):
		file_info = self._files[0]
		result = tmsu_info(file_info)
		if not result:
			return []
		matches = re.findall(r"Root path: ([^\n]+)", result, re.RegexFlag.MULTILINE)
		if len(matches) == 0:
			return []
		return tmsu_get_tags(None, cwd=matches[0])
