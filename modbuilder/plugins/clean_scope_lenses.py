from modbuilder import mods, mods2
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
NIGHT_VISION_WHITE_FILE = "environment/weather/night_vision_white.environc"

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
    white_adf = mods2.deserialize_adf(NIGHT_VISION_WHITE_FILE, modded=False)
    tint_index = white_adf.table_instance_full_values[0].value["Hashes"].value.index(2219558163)
    tint_value_1 = white_adf.table_instance_full_values[0].value["Parameters"].value[tint_index].value["Keys"].value[0]
    tint_value_2 = white_adf.table_instance_full_values[0].value["Parameters"].value[tint_index].value["Values"].value[0]
    green_adf = mods2.deserialize_adf(NIGHT_VISION_FILE)
    tint_offset_1 = green_adf.table_instance_full_values[0].value["Parameters"].value[tint_index].value["Keys"].data_offset
    tint_offset_2 = green_adf.table_instance_full_values[0].value["Parameters"].value[tint_index].value["Values"].data_offset
    mods.update_file_at_offsets_with_values(
      NIGHT_VISION_FILE,
      [
        (tint_offset_1, tint_value_1),
        (tint_offset_2, tint_value_2),
      ]
    )
