import logging
import queue
import threading

from gi.repository import GObject, Nautilus
from urllib.parse import unquote

from nautilus_tmsu_utils import is_in_tmsu_db, tmsu_get_tags

GObject.threads_init()

COLUMN_NAME = "NautilusTMSUColumn"
logger = logging.getLogger("nautilus-tmsu")


class NautilusTMSUTask(object):
	closure: GObject.Closure
	file: Nautilus.FileInfo
	handle: Nautilus.OperationHandle
	provider: Nautilus.InfoProvider

	def __init__(self, file: Nautilus.FileInfo, provider: Nautilus.InfoProvider, handle: Nautilus.OperationHandle, closure: GObject.Closure) -> None:
		self.closure = closure
		self.file = file
		self.handle = handle
		self.provider = provider


class NautilusTMSUColumn(GObject.GObject, Nautilus.ColumnProvider, Nautilus.InfoProvider):
	def __init__(self, **kwargs) -> None:
		super().__init__(**kwargs)
		self._active_handles = set()
		self._lock = threading.Lock()
		self._worker_queue = queue.Queue()
		self._worker_running = False
		self._start_worker_thread()
		# make sure our thread runs
		GObject.timeout_add(50, self._keep_alive)

	def cancel_update(self, provider: Nautilus.InfoProvider, handle: Nautilus.OperationHandle | None = None) -> None:
		with self._lock:
			if handle and handle in self._active_handles:
				self._active_handles.remove(handle)

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
		path = unquote(file.get_uri() if file.is_directory() else file.get_parent_uri())[7:]

		if file.get_uri_scheme() != "file" or not is_in_tmsu_db(path):
			logger.debug(f"skipping non tmsu file: {file.get_uri()}")
			return Nautilus.OperationResult.COMPLETE

		with self._lock:
			self._active_handles.add(handle)

		task = NautilusTMSUTask(file=file, provider=provider, handle=handle, closure=closure)
		self._worker_queue.put(task)
		logger.debug(f"added to queue: {file.get_uri()}")

		return Nautilus.OperationResult.IN_PROGRESS

	def _is_active_handle(self, handle: Nautilus.OperationHandle):
		with self._lock:
			if handle in self._active_handles:
				return True
		return False

	def _keep_alive(self):
		return True

	def _process_queue(self):
		while True:
			task: NautilusTMSUTask = self._worker_queue.get()

			if not self._is_active_handle(task.handle):
				self._worker_queue.task_done()
				continue

			tags = tmsu_get_tags(task.file)

			if not self._is_active_handle(task.handle):
				self._worker_queue.task_done()
				continue

			GObject.idle_add(self._update_ui, task, tags)
			self._worker_queue.task_done()

	def _start_worker_thread(self):
		if self._worker_running:
			logger.debug("worker thread already running, skipping")
			return

		thread = threading.Thread(target=self._process_queue, daemon=True)
		self._worker_running = True
		thread.start()
		logger.info("started column worker thread")

	def _update_ui(self, task: NautilusTMSUTask, tags: list[str]):
		logger.debug(f"_update_ui: {task.file.get_uri()}")
		if not self._is_active_handle(task.handle):
			logger.debug("handle cancelled")
			return False

		task.file.add_string_attribute("tmsu_tags", ", ".join(tags))
		task.file.invalidate_extension_info()
		Nautilus.info_provider_update_complete_invoke(task.closure, task.provider, task.handle, Nautilus.OperationResult.COMPLETE)
		logger.debug("_update_ui completed")
		return False
