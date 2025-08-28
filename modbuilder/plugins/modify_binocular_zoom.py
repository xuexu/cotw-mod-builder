from modbuilder import mods, mods2
from pathlib import Path
import FreeSimpleGUI as sg

DEBUG = False
NAME = "Modify Binocular Zoom"
DESCRIPTION = "Modify the zoom range for binoculars. Every zoomable binocular has five zoom levels. With this mod you get to control each level of the zoom."

class Optics:
  def __init__(self, file: Path, bundle_file: Path) -> None:
    self.file = mods.get_relative_path(file)
    self.bundle_file = mods.get_relative_path(bundle_file)
    self._map_name()
    tuning_file = mods2.deserialize_adf(self.file, modded=False)
    tuning_values = tuning_file.table_instance_full_values[0].value
    self.optics_level_1 = tuning_values["zoom_multiplier_level_0"].value
    self.optics_level_2 = tuning_values["zoom_multiplier_level_1"].value
    self.optics_level_3 = tuning_values["zoom_multiplier_level_2"].value
    self.optics_level_4 = tuning_values["zoom_multiplier_level_3"].value
    self.optics_level_5 = tuning_values["zoom_multiplier_level_4"].value

  def __repr__(self) -> str:
    return f"{self.name}, {self.file}, {self.bundle_file}"

  def _map_name(self) -> None:
    split_file = self.file.split("/")
    filename = split_file[-1].replace(".sighttunec","")  # filename without "".sighttunec" extension
    self.name = mods.clean_equipment_name(filename, "optic")
    if (mapped_eqipment := mods.map_equipment(self.name, "optic")):
      self.display_name = mapped_eqipment["name"]
    else:
      self.display_name = self.name

def load_optics() -> list[Optics]:
  base_file_path = mods.APP_DIR_PATH / "org/editor/entities/hp_equipment/optics/tuning"
  base_bundle_path = mods.APP_DIR_PATH / "org/editor/entities/hp_equipment/optics"
  binoculars = [
    Optics(base_file_path / "equipment_optics_binoculars_01.sighttunec", base_bundle_path / "equipment_optics_binoculars_01.ee"),
    Optics(base_file_path / "equipment_optics_rangefinder_01.sighttunec", base_bundle_path / "equipment_optics_rangefinder_01.ee"),
    Optics(base_file_path / "equipment_optics_rangefinder_binoculars_01.sighttunec", base_bundle_path / "equipment_optics_rangefinder_binoculars_01.ee"),
    Optics(base_file_path / "equipment_optics_night_vision_01.sighttunec", base_bundle_path / "equipment_optics_night_vision_01.ee"),
  ]
  return sorted(binoculars, key=lambda x: x.name)

def get_option_elements() -> sg.Column:
  return sg.Column([
    [sg.T("Binoculars:"), sg.Combo([x.display_name for x in ALL_OPTICS], metadata=ALL_OPTICS, k="optics_name", p=((10,0),(10,10)), enable_events=True)],
    [sg.T("Level 1:"), sg.Slider((1, 30), 1.0, 0.1, orientation="h", k="optics_level_1", s=(30,20), p=((10,0),(0,10)))],
    [sg.T("Level 2:"), sg.Slider((1, 30), 1.0, 0.1, orientation="h", k="optics_level_2", s=(30,20), p=((10,0),(0,10)))],
    [sg.T("Level 3:"), sg.Slider((1, 30), 1.0, 0.1, orientation="h", k="optics_level_3", s=(30,20), p=((10,0),(0,10)))],
    [sg.T("Level 4:"), sg.Slider((1, 30), 1.0, 0.1, orientation="h", k="optics_level_4", s=(30,20), p=((10,0),(0,10)))],
    [sg.T("Level 5:"), sg.Slider((1, 30), 1.0, 0.1, orientation="h", k="optics_level_5", s=(30,20), p=((10,0),(0,10)))]
  ])

def get_selected_optics(window: sg.Window, values: dict) -> Optics:
  optics_list = window["optics_name"].metadata
  optics_name = values.get("optics_name")
  if optics_name:
    try:
      optics_index = window["optics_name"].Values.index(optics_name)
      return optics_list[optics_index]
    except ValueError as _e:  # user typed/edited data in box and we cannot match
      pass
  return None

def handle_event(event: str, window: sg.Window, values: dict) -> None:
  if event == "optics_name":
    selected_optics = get_selected_optics(window, values)
    window["optics_level_1"].update(selected_optics.optics_level_1)
    window["optics_level_2"].update(selected_optics.optics_level_2)
    window["optics_level_3"].update(selected_optics.optics_level_3)
    window["optics_level_4"].update(selected_optics.optics_level_4)
    window["optics_level_5"].update(selected_optics.optics_level_5)

def add_mod(window: sg.Window, values: dict) -> dict:
  selected_optics = get_selected_optics(window, values)
  if not selected_optics:
    return {
      "invalid": "Please select a binocular first"
    }

  return {
    "key": f"modify_optics_{selected_optics.name}",
    "invalid": None,
    "options": {
      "name": selected_optics.name,
      "display_name": selected_optics.display_name,
      "file": selected_optics.file,
      "bundle_file": selected_optics.bundle_file,
      "level_1": values["optics_level_1"],
      "level_2": values["optics_level_2"],
      "level_3": values["optics_level_3"],
      "level_4": values["optics_level_4"],
      "level_5": values["optics_level_5"]
    }
  }

def format_options(options: dict) -> str:
  return f"Modify Optics: {options.get('display_name', options['name'])} ({options['level_1']}, {options['level_2']}, {options['level_3']}, {options['level_4']}, {options['level_5']})"

def handle_key(mod_key: str) -> bool:
  return mod_key.startswith("modify_optics")

def get_files(options: dict) -> list[str]:
  return [options["file"]]

def merge_files(files: list[str], options: dict) -> None:
  lookup = mods.get_sarc_file_info(mods.APP_DIR_PATH / "org" / options["bundle_file"])
  mods.merge_into_archive(options["file"].replace("\\", "/"), options["bundle_file"], lookup)

def process(options: dict) -> None:
  file = options["file"]
  tuning_file = mods2.deserialize_adf(file)
  tuning_values = tuning_file.table_instance_full_values[0].value
  updates = [
    {"offset": tuning_values["zoom_multiplier_level_0"].data_offset, "value": options["level_1"]},
    {"offset": tuning_values["zoom_multiplier_level_1"].data_offset, "value": options["level_2"]},
    {"offset": tuning_values["zoom_multiplier_level_2"].data_offset, "value": options["level_3"]},
    {"offset": tuning_values["zoom_multiplier_level_3"].data_offset, "value": options["level_4"]},
    {"offset": tuning_values["zoom_multiplier_level_4"].data_offset, "value": options["level_5"]},
  ]
  mods.apply_updates_to_file(file, updates)

def handle_update(mod_key: str, mod_options: dict, version: str) -> tuple[str, dict]:
  """
  2.2.2
  - Replace full filepath with just optics name in mod_key
  2.2.0
  - Use formatted name from 'name_map.yaml' as display_name
  - Fix formatting of file path
  """
  # 2.1.9 and prior had double backslashes in file paths
  selected_optics = next((
    x for x in ALL_OPTICS if (
      x.file == mod_options["file"] or  # properly formatted path with single forward slash (/)
      x.file == mod_options["file"].replace("\\", "/")  # old path with double backslash (\\)
    )), None
  )
  if not selected_optics:
    raise ValueError(f"Unable to match optics {mod_options['name']}")

  updated_mod_key = f"modify_optics_{selected_optics.name}"
  updated_mod_options = mod_options
  updated_mod_options["name"] = selected_optics.name
  updated_mod_options["display_name"] = selected_optics.display_name
  updated_mod_options["file"] = selected_optics.file
  updated_mod_options["bundle_file"] = selected_optics.bundle_file
  return updated_mod_key, updated_mod_options

ALL_OPTICS = load_optics()
