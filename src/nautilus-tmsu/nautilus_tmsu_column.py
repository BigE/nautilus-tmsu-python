import logging

from gi.repository import GObject, Nautilus # type: ignore
from urllib.parse import unquote

from nautilus_tmsu_commands import NautilusTMSUCommandTags
from nautilus_tmsu_runner import is_tmsu_db, NautilusTMSUCommand, NautilusTMSURunner

GObject.threads_init()

COLUMN_NAME = "NautilusTMSUColumn"
logger = logging.getLogger("nautilus-tmsu")


class NautilusTMSUTask(object):
	closure: GObject.Closure
	file: Nautilus.FileInfo
	handle: Nautilus.OperationHandle
	provider: Nautilus.InfoProvider

	def __init__(self, file: Nautilus.FileInfo, provider: Nautilus.InfoProvider, handle: Nautilus.OperationHandle, closure: GObject.Closure, command: NautilusTMSUCommandTags) -> None:
		self.closure = closure
		self.command = command
		self.file = file
		self.handle = handle
		self.provider = provider


class NautilusTMSUColumn(GObject.GObject, Nautilus.ColumnProvider, Nautilus.InfoProvider):
	def __init__(self, **kwargs) -> None:
		super().__init__(**kwargs)
		self._active_handlers = dict[Nautilus.OperationHandle, NautilusTMSUCommand]()
		self._current_parent: Nautilus.FileInfo | None = None
		self._is_parent_in_tmsu_db = False
		self._runner = NautilusTMSURunner()

	def cancel_update(self, provider: Nautilus.InfoProvider, handle: Nautilus.OperationHandle | None = None) -> None:
		logger.log(9, f"cancelling handle: {handle}")
		with NautilusTMSURunner.lock:
			if handle in self._active_handlers:
				self._active_handlers[handle].can_run = False
				del self._active_handlers[handle]

	def get_columns(self) -> list[Nautilus.Column]:
		return [
			Nautilus.Column(
				name=f"{COLUMN_NAME}::tmsu_tags_column",
				attribute="tmsu_tags",
				label="TMSU tags",
				description="List of TMSU tags"
			)
		]

	def update_file_info_full(self, provider: Nautilus.InfoProvider, handle: Nautilus.OperationHandle, closure: GObject.Closure, file: Nautilus.FileInfo):
		logger.log(9, f"update_file_info_full: {file.get_uri()}")

		if self._current_parent is None or file != self._current_parent:
			self._current_parent = file.get_parent_info()
			if self._current_parent:
				self._is_parent_in_tmsu_db = is_tmsu_db(self._current_parent)

		if self._current_parent and self._is_parent_in_tmsu_db is False:
			logger.debug(f'skipping file: parent directory is not in tmsu db {file.get_uri()}')
			return Nautilus.OperationResult.COMPLETE

		command = NautilusTMSUCommandTags(file)
		with NautilusTMSURunner.lock:
			self._active_handlers[handle] = command

		self._runner.add(command, self._update_ui, provider, handle, closure, file)
		logger.debug(f"added to queue: {file.get_uri()}")
		return Nautilus.OperationResult.IN_PROGRESS

	def _update_ui(self, command: NautilusTMSUCommand, result: str | None, *args):
		file: Nautilus.FileInfo
		[provider, handle, closure, file] = args
		logger.log(9, f"_update_ui: {file.get_uri()} {result}")

		if handle not in self._active_handlers:
			logger.debug(f"handler missing, skipping _update_ui")
			return False

		if result:
			file.add_string_attribute('tmsu_tags', ', '.join([tag.replace('\\', '') for tag in result]))
			file.invalidate_extension_info()
		Nautilus.info_provider_update_complete_invoke(closure, provider, handle, Nautilus.OperationResult.COMPLETE)
		logger.log(9, f"_update_ui completed")
		return False
