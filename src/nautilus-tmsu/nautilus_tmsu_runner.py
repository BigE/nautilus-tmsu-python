import logging
import re
import queue
import threading

from gi.repository import GObject, Nautilus # type: ignore
from typing import TypedDict

from nautilus_tmsu_commands import NautilusTMSUCommand, NautilusTMSUCommandCallback
from nautilus_tmsu_utils import get_path_from_file_info

logger = logging.getLogger('nautilus-tmsu')

class classproperty:
	def __init__(self, method) -> None:
		self.method = method

	def __get__(self, instance, owner):
		return self.method(owner)


class NautilusTMSURunnerQueue(TypedDict):
	command: NautilusTMSUCommand
	callback: NautilusTMSUCommandCallback | None
	callback_args: tuple | None


class NautilusTMSURunner(GObject.Object):
	_instance: 'NautilusTMSURunner'
	_lock = threading.Lock()

	def __new__(cls, *args, **kwargs) -> 'NautilusTMSURunner':
		if not hasattr(cls, '_instance') or not cls._instance:
			with cls._lock:
				if not hasattr(cls, '_instance') or not cls._instance:
					cls._instance = super().__new__(cls, *args, **kwargs)
		return cls._instance

	def __init__(self) -> None:
		if hasattr(self, '_running') and self._running:
			return

		super()
		self._queue = queue.Queue[NautilusTMSURunnerQueue]()
		self._start_worker_thread()
		GObject.timeout_add(5, self._keep_alive)
		self._running: bool = True

	@classproperty
	def lock(cls):
		return cls._lock

	def add(self, command: NautilusTMSUCommand, callback: NautilusTMSUCommandCallback | None = None, *callback_args) -> None:
		self._queue.put({
			'command': command,
			'callback': callback,
			'callback_args': callback_args,
		})

	def _keep_alive(self):
		"""
		Keep alive to get attention from Nautilus
		"""
		return True

	def _process_queue(self):
		while True:
			task = self._queue.get()
			# it's possible the command has been canceled
			if task['command'].can_run:
				result = task['command'].execute()
				if task['callback']:
					GObject.idle_add(task['callback'], task['command'], result, *task['callback_args'] or tuple())
			self._queue.task_done()

	def _start_worker_thread(self):
		thread = threading.Thread(target=self._process_queue, daemon=True)
		thread.start()
		logger.info('worker thread started')


def find_tmsu_root(file_info: Nautilus.FileInfo):
	result = NautilusTMSUCommand('info', cwd=get_path_from_file_info(file_info, True)).execute()
	if result:
		m = re.findall(r'Root path: ([^\n]+)', result)
		if m:
			return m[0]
	return None


def is_tmsu_db(file_info: Nautilus.FileInfo):
	cwd = get_path_from_file_info(file_info, True)
	return False if (NautilusTMSUCommand("info", cwd=cwd, log_error=False)).execute() is None else True
