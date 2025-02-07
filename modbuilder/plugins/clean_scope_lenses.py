from modbuilder import mods
import os

DEBUG = False
NAME = "Clean Scope Lenses"
DESCRIPTION = "Replace the dirty, tinted scope lenses with clean, clear glass."
WARNING = "Does not modify Reflex and Red Dot sights. Those adjustments are available in-game under Settings > Interface > Sights."
OPTIONS = [
  {
    "name": "Remove Night Vision Tint",
    "style": "boolean",
    "default": False,
    "initial": False,
    "note": "Remove green tint from the GenZero Night Vision scope",
  }
]
NIGHT_VISION_FILE = "environment/weather/night_vision.environc"

def format(options: dict) -> str:
  text = "Clean Scope Lenses"
  night_vision = options.get("remove_night_vision_tint")
  if night_vision:
    text += " and Remove Night Vision Tint"
  return text

def get_files(options: dict) -> list[str]:
  night_vision = options.get("remove_night_vision_tint")
  if night_vision:
    return [NIGHT_VISION_FILE]
  return []

def merge_files(files: list[str], options: dict) -> None:
  base_path = "models/hp_sights/lenses/textures"
  modded_path = "modded/scope_lenses"
  for file in os.listdir(mods.APP_DIR_PATH / "org" / modded_path):
    src = mods.APP_DIR_PATH / "org" / modded_path / file
    dest = mods.APP_DIR_PATH / "mod/dropzone" / base_path / file
    mods.copy_file(src, dest)

def process(options: dict) -> None:
  night_vision = options.get("remove_night_vision_tint")
  if night_vision:
    mods.update_file_at_offsets_with_values(
      NIGHT_VISION_FILE,
      [
        (944, 0.22018349170684814),
        (952, 25.22058868408203),
      ]
    )
