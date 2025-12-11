from gi.repository import Gdk, Gtk # type: ignore


class NautilusTMSUTagEntryBox(Gtk.Box):
	"""
	A custom widget that looks like a Gtk.Entry for TMSU tag completion
	"""
	def __init__(self, tags: list[str] = [], *args, **kwargs):
		super().__init__(*args, **kwargs)
		self.add_css_class('linked')

		self.entry = Gtk.Entry(hexpand=True)
		self.entry.set_placeholder_text('Type tags separated by a space')
		self.append(self.entry)

		self.string_model = Gtk.StringList.new(tags)
		self.filter = Gtk.CustomFilter.new(self._on_filter_match)
		self.filter_model = Gtk.FilterListModel(
			model=self.string_model,
			filter=self.filter,
		)

		self.selection_model = Gtk.SingleSelection(
			model=self.filter_model,
			autoselect=False,
		)

		# --- 3. The Popup List UI ---
		# Factory to dictate how to render each row
		factory = Gtk.SignalListItemFactory()
		factory.connect("setup", self._on_setup_list_item)
		factory.connect("bind", self._on_bind_list_item)

		# The actual List View
		self.list_view = Gtk.ListView(model=self.selection_model, factory=factory)
		# Activate on single click
		self.list_view.connect("activate", self._on_list_item_activated)

		# Scroll window for the list
		scrolled_window = Gtk.ScrolledWindow()
		scrolled_window.set_child(self.list_view)
		scrolled_window.set_max_content_height(300) # Limit height
		scrolled_window.set_propagate_natural_width(True)

		# The Popover (The floating window)
		self.popover = Gtk.Popover(hexpand=True)
		self.popover.set_child(scrolled_window)
		self.popover.set_parent(self.entry)
		self.popover.set_autohide(False) # We control visibility manually
		self.popover.set_has_arrow(False)
		key_controller = Gtk.EventControllerKey()
		key_controller.connect('key-pressed', self._on_popover_key_pressed)
		self.popover.add_controller(key_controller)

		# --- 4. Event Wiring ---
		# When text changes, re-filter
		self.entry.connect("changed", self._on_text_changed)

		# Handle "Arrow Down" to move focus into the list
		key_controller = Gtk.EventControllerKey()
		key_controller.connect("key-pressed", self._on_entry_key_pressed)
		self.entry.add_controller(key_controller)

	# --- Logic ---

	def get_current_word(self) -> tuple[str, int, int]:
		text = self.entry.get_text()
		cursor_pos = self.entry.get_position()

		start = cursor_pos
		while start > 0 and text[start - 1] != ' ':
			start -= 1

		end = cursor_pos
		while end < len(text) and text[end] != ' ':
			end += 1

		return text[start:end], start, end

	def _on_filter_match(self, item, *args):
		"""Decides if a row should be visible."""
		search_text, start, end = self.get_current_word()
		item_text = item.get_string().lower()

		# Logic: Show if search text is inside the item text
		return search_text in item_text

	def _on_text_changed(self, entry):
		"""Called when user types."""
		text = entry.get_text()

		# 1. Update the filter
		self.filter.changed(Gtk.FilterChange.DIFFERENT)

		# 2. Get the last word only
		last_token = text.split(' ')[-1]

		# 3. Decide if we should show the popup
		n_items = self.filter_model.get_n_items()

		if n_items > 0 and len(last_token) > 0:
			self.popover.set_size_request(self.entry.get_allocated_width(), -1)
			# Position the popover manually if needed,
			# or just rely on default attachment
			self.popover.popup()
		else:
			self.popover.popdown()

	def _on_list_item_activated(self, list_view: Gtk.ListView, position: int):
		"""Called when user clicks a row in the popup."""
		item = self.filter_model.get_item(position)
		if not isinstance(item, Gtk.StringObject):
			return
		selected_word = item.get_string()
		current_word, start, end = self.get_current_word()

		# Update entry
		full_text = self.entry.get_text()
		new_text = full_text[:start] + selected_word + full_text[end:]
		self.entry.set_text(new_text)
		self.entry.set_position(-1) # Move cursor to end
		self.popover.popdown()

	def _on_entry_key_pressed(self, controller, keyval, keycode, state):
		"""Handle keyboard navigation from Entry -> List."""
		print(f'_on_entry_key_pressed: {keyval} -> {Gdk.keyval_name(keyval)}')
		if state == Gdk.ModifierType.NO_MODIFIER_MASK and self.popover.get_visible():
			if keyval == Gdk.KEY_Down:
				self.list_view.grab_focus()
				self.selection_model.set_selected(0) # Select first item
				return True
			elif keyval == Gdk.KEY_Escape:
				self.popover.popdown()
				return True
		return False

	def _on_popover_key_pressed(self, controlle, keyval, keycode, state):
		print(f'_on_popover_key_pressed: {keyval} -> {Gdk.keyval_name(keyval)}')
		if state == Gdk.ModifierType.NO_MODIFIER_MASK and self.popover.get_visible():
			if keyval in {Gdk.KEY_KP_Enter, Gdk.KEY_ISO_Enter, Gdk.KEY_Return}:
				pos = self.selection_model.get_selected()
				if pos != Gtk.INVALID_LIST_POSITION:
					self.list_view.emit('activate', pos)
					return True
		return False

	# --- UI Rendering for the List ---

	def _on_setup_list_item(self, factory, list_item):
		label = Gtk.Label(xalign=0.0)
		label.set_margin_start(10)
		label.set_margin_end(10)
		list_item.set_child(label)

	def _on_bind_list_item(self, factory, list_item):
		label = list_item.get_child()
		item = list_item.get_item() # This is a GtkStringObject
		label.set_label(item.get_string())
