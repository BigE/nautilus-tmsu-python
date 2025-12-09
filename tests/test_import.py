import pytest

def test_nautilus_tmsu_import():
	try:
		import nautilus_tmsu
	except ImportError as e:
		pytest.fail(f"Import failed: {e}")