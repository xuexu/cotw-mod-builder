import shutil

from modbuilder import mods
from modbuilder.logging_config import get_logger

logger = get_logger(__name__)

DEBUG = False
NAME = "Hide Save Indicator"
DESCRIPTION = "Hide the flashing hexagon indicator shown in the lower-left corner of the screen when the game saves."
OPTIONS = [
  { "title": "There are no options. Just add the modification." }
]

# This Scaleform-generated texture name may change after a game update
# Keep it synchronized with the UI assets shipped in the matching org asset bundle.
SAVE_INDICATOR_FILE = "overlay_i5d.ddsc"
ASSETS_PATH = mods.APP_DIR_PATH / "org/modded/hide_save_indicator"
REPLACEMENT_FILE = ASSETS_PATH / "transparent.ddsc"


def format_options(options: dict) -> str:
  return NAME


def get_files(options: dict) -> list[str]:
  return []


def merge_files(files: list[str], options: dict) -> None:
  try:
    mods.copy_file(REPLACEMENT_FILE, mods.MOD_PATH / "ui" / SAVE_INDICATOR_FILE)
  except (OSError, shutil.Error):
      logger.exception("Error: Could not copy save indicator file")
      pass


def update_values_at_offset(options: dict) -> list[dict]:
  return []
