from gi.repository import Nautilus, Gtk
from typing import List


def show_edit_tags_dialog(files: List[Nautilus.FileInfo]):
	window = Gtk.Window()
	window.set_title("TMSU")
	window.set_default_size(450, 500)
	window.set_modal(True)
	window.set_hide_on_close(True)