import os

from gi.repository import Nautilus, Gio, GObject # type: ignore
from typing import Any, List

from nautilus_tmsu_commands import NautilusTMSUCommandTags
from nautilus_tmsu_runner import is_tmsu_db
from nautilus_tmsu_object import NautilusTMSUObject


class NautilusTMSUProperties(NautilusTMSUObject, GObject.Object, Nautilus.PropertiesModelProvider):
	def get_models(
		self,
		files: List[Nautilus.FileInfo],
	) -> List[Nautilus.PropertiesModel]:
		if len(files) != 1:
			return []

		if not is_tmsu_db(files[0]):
			return []

		tags_model = Gio.ListStore(item_type=Nautilus.PropertiesItem)
		tags = NautilusTMSUCommandTags(files[0]).execute()

		for tag in tags:
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