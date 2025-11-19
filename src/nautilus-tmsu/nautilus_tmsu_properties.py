import subprocess

from gi.repository import Nautilus, GObject, Gio
from typing import List

from nautilus_tmsu_utils import which_tmsu


class NautilusTMSUProperties(GObject.GObject, Nautilus.PropertiesModelProvider):
	def get_models(
		self,
		files: List[Nautilus.FileInfo],
	) -> List[Nautilus.PropertiesModel]:
		if len(files) != 1:
			return []

		tmsu = which_tmsu()
		file: Gio.File = files[0].get_location()

		if file is None:
			return []

		tags_model = Gio.ListStore.new(item_type=Nautilus.PropertiesItem)
		result = subprocess.run([tmsu, "tags", "-1", file.get_path()], capture_output=True, text=True, cwd=file.get_parent().get_path())

		if result.returncode != 0:
			return []

		for tag in result.stdout.strip("\n").split("\n")[1:]:
			tags_model.append(
				Nautilus.PropertiesItem(
					name="Tag",
					value=tag.replace('\\ ', ' ')
				)
			)

		return [
			Nautilus.PropertiesModel(
				title="TMSU Tags",
				model=tags_model,
			),
		]