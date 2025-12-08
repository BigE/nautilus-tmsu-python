import logging
import os
import sys

__VERSION__ = "0.0.1"

DEBUG_VERBOSE_LEVEL = 9
logging.addLevelName(DEBUG_VERBOSE_LEVEL, "DEBUG_VERBOSE")

logger = logging.getLogger("nautilus-tmsu")
logger.setLevel(os.getenv("NAUTILUS_TMSU_DEBUG", "INFO"))
handler = logging.StreamHandler(sys.stdout)
handler.setFormatter(logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s"))
logger.addHandler(handler)

logger.info(f"Initializing nautilus-tmsu: {__VERSION__}")

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'nautilus-tmsu'))
from nautilus_tmsu_column import NautilusTMSUColumn
from nautilus_tmsu_menu import NautilusTMSUMenu
from nautilus_tmsu_properties import NautilusTMSUProperties