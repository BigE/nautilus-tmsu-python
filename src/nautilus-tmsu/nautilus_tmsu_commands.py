import logging
import subprocess

from collections.abc import Callable
from gi.repository import Nautilus # type: ignore
from typing import Literal

from nautilus_tmsu_utils import get_path_from_file_info, which_tmsu

logger = logging.getLogger('nautilus-tmsu')
NautilusTMSUCommandCallback = Callable[["NautilusTMSUCommand", str | None], Literal[False]]


class NautilusTMSUCommand(object):
	_tmsu = which_tmsu()

	def __init__(self, *args, callback: NautilusTMSUCommandCallback | None = None, cwd: str | None = None, log_error: bool = True) -> None:
		self._args = args
		self._cwd = cwd
		self._callback = callback
		self._can_run = True
		self._log_error = log_error

	@property
	def callback(self):
		return self._callback

	@property
	def can_run(self):
		return self._can_run

	@can_run.setter
	def can_run(self, value: bool):
		self._can_run = bool(value)

	@property
	def tmsu(self):
		return self._tmsu

	@tmsu.setter
	def tmsu(self, value):
		self._tmsu = which_tmsu(value)

	def execute(self):
		args = (self.tmsu, ) + self._args

		try:
			logger.log(9, f'command: CWD={self._cwd} {" ".join(args)}')
			result = subprocess.run(args, capture_output=True, cwd=self._cwd)
		except Exception as e:
			logger.error(e)
			return None

		if result.returncode != 0:
			logger.log(9, result)
			if self._log_error:
				error_message = result.stderr.decode('UTF-8')
				logger.error(f'command failed: {error_message}')
			return None

		return result.stdout.decode('UTF-8')


class NautilusTMSUCommandMixin(NautilusTMSUCommand):
	def __init__(self, *args, **kwargs) -> None:
		super().__init__(*args, **kwargs)


class NautilusTMSUCommandFilesMixin(NautilusTMSUCommandMixin):
	def __init__(self, *args, files: list[Nautilus.FileInfo], **kwargs) -> None:
		kwargs.setdefault('cwd', get_path_from_file_info(files[0], True))
		for file in files:
			args += (get_path_from_file_info(file), )
		super().__init__(*args, **kwargs)


class NautilusTMSUCommandRecursiveMixin(NautilusTMSUCommandMixin):
	def __init__(self, *args, recursive: bool, **kwargs) -> None:
		if recursive:
			args += ('--recursive', )
		super().__init__(*args, **kwargs)


class NautilusTMSUCommandTagsMixin(NautilusTMSUCommandMixin):
	def __init__(self, *args, tags: list[str] | None, **kwargs) -> None:
		if tags is not None:
			args += (f'--tags={" ".join(tags)}', )
		super().__init__(*args, **kwargs)


class NautilusTMSUCommandDelete(NautilusTMSUCommand):
	def __init__(self, file_info: Nautilus.FileInfo, tags: list[str]) -> None:
		cwd = get_path_from_file_info(file_info, True)
		args = ['delete', ] + tags
		super().__init__(cwd=cwd, *args)


class NautilusTMSUCommandInit(NautilusTMSUCommand):
	def __init__(self, file_info: Nautilus.FileInfo) -> None:
		cwd = get_path_from_file_info(file_info, True)
		args = ('init', )
		super().__init__(cwd=cwd, *args)


class NautilusTMSUCommandTag(NautilusTMSUCommandRecursiveMixin, NautilusTMSUCommandTagsMixin, NautilusTMSUCommandFilesMixin):
	def __init__(self, files: list[Nautilus.FileInfo], tags: list[str], recursive: bool = False) -> None:
		args = ['tag', ]
		super().__init__(files=files, tags=tags, recursive=recursive, *args)


class NautilusTMSUCommandTags(NautilusTMSUCommand):
	def __init__(self, file: Nautilus.FileInfo, use_as_cwd: bool = False, cwd: str | None = None) -> None:
		args = ['tags', '-1']
		if not use_as_cwd:
			args.append(get_path_from_file_info(file))
		cwd = cwd if cwd and not use_as_cwd else get_path_from_file_info(file, True)
		super().__init__(cwd=cwd, *args)

	def execute(self) -> list[str]:
		tags = super().execute()
		if not tags:
			return []
		return tags.strip().split('\n')[1:]


class NautilusTMSUCommandUntag(NautilusTMSUCommandRecursiveMixin, NautilusTMSUCommandTagsMixin, NautilusTMSUCommandFilesMixin):
	def __init__(self, files: list[Nautilus.FileInfo], tags: list[str] | None = None, recursive: bool = False, force_all: bool = False, tmsu: str = "tmsu", cwd: str | None = None) -> None:
		args = ['untag', ]
		if force_all:
			args.append('--all')
		elif tags is None:
			raise ValueError('tags or force_all must be defined')
		super().__init__(files=files, tags=tags, recursive=recursive, tmsu=tmsu, cwd=tmsu, *args)