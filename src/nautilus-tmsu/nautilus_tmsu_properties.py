from gi.repository import Nautilus, GObject, Gio
from typing import List

from nautilus_tmsu_utils import get_tmsu_tags, which_tmsu


class NautilusTMSUProperties(GObject.Object, Nautilus.PropertiesModelProvider):
	def get_models(
		self,
		files: List[Nautilus.FileInfo],
	) -> List[Nautilus.PropertiesModel]:
		if len(files) != 1:
			return []

		tags_model = Gio.ListStore(item_type=Nautilus.PropertiesItem)

		for tag in get_tmsu_tags(files[0]):
			tags_model.append(
				Nautilus.PropertiesItem(
					name="Tag",
					value=tag
				)
			)

		return [
			Nautilus.PropertiesModel(
				title="TMSU Tags",
				model=tags_model,
			),
		]