import os
import sys

__VERSION__ = "0.0.1"

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'nautilus-tmsu'))
from nautilus_tmsu_properties import NautilusTMSUProperties
from nautilus_tmsu_menu import NautilusTMSUMenu