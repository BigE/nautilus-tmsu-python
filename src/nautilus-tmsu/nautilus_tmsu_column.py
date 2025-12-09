import logging
import queue
import threading

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
		self._runner = NautilusTMSURunner()

	def cancel_update(self, provider: Nautilus.InfoProvider, handle: Nautilus.OperationHandle | None = None) -> None:
		logger.debug(f"cancelling handle: {handle}")
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
		logger.debug(f"update_file_info_full: {file.get_uri()}")

		if file.get_uri_scheme() != "file" or not is_tmsu_db(file):
			logger.debug(f"skipping non tmsu file: {file.get_uri()}")
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
		logger.debug(f"_update_ui: {file.get_uri()} {result}")

		if handle not in self._active_handlers:
			logger.debug(f"handler missing, skipping _update_ui")
			return False

		if result:
			file.add_string_attribute('tmsu_tags', ', '.join([tag.replace('\\', '') for tag in result]))
			file.invalidate_extension_info()
		logger.debug(f"_update_ui completed")
		Nautilus.info_provider_update_complete_invoke(closure, provider, handle, Nautilus.OperationResult.COMPLETE)
		return False
