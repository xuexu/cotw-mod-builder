from modbuilder import mods, mods2
from pathlib import Path
import FreeSimpleGUI as sg
import re, os
from modbuilder.logging_config import get_logger

logger = get_logger(__name__)

DEBUG = False
NAME = "Modify Scope Zoom"
DESCRIPTION = "Modify the magnification for all five zoom levels of each scope. Use advanced controls to customize the sensitivity and maximum horizontal/vertical angular speed while zoomed in."

class Scope:
  def __init__(self, file: Path, bundle_file: Path) -> None:
    self.file = mods.get_relative_path(file)
    self.bundle_file = mods.get_relative_path(bundle_file)
    self._map_name()
    tuning_file = mods2.deserialize_adf(self.file, modded=False)
    tuning_values = tuning_file.table_instance_full_values[0].value
    self.scope_level_1 = tuning_values["zoom_multiplier_level_0"].value
    self.scope_level_2 = tuning_values["zoom_multiplier_level_1"].value
    self.scope_level_3 = tuning_values["zoom_multiplier_level_2"].value
    self.scope_level_4 = tuning_values["zoom_multiplier_level_3"].value
    self.scope_level_5 = tuning_values["zoom_multiplier_level_4"].value
    self.scope_level_1_sensitivity = round(tuning_values["sensitivity_modifier_zoom_0"].value, 2)
    self.scope_level_2_sensitivity = round(tuning_values["sensitivity_modifier_zoom_1"].value, 2)
    self.scope_level_3_sensitivity = round(tuning_values["sensitivity_modifier_zoom_2"].value, 2)
    self.scope_level_4_sensitivity = round(tuning_values["sensitivity_modifier_zoom_3"].value, 2)
    self.scope_level_5_sensitivity = round(tuning_values["sensitivity_modifier_zoom_4"].value, 2)
    self.scope_level_1_h_speed = tuning_values["max_h_angular_speed_zoom_0"].value
    self.scope_level_1_v_speed = tuning_values["max_v_angular_speed_zoom_0"].value
    self.scope_level_2_h_speed = tuning_values["max_h_angular_speed_zoom_1"].value
    self.scope_level_2_v_speed = tuning_values["max_v_angular_speed_zoom_1"].value
    self.scope_level_3_h_speed = tuning_values["max_h_angular_speed_zoom_2"].value
    self.scope_level_3_v_speed = tuning_values["max_v_angular_speed_zoom_2"].value
    self.scope_level_4_h_speed = tuning_values["max_h_angular_speed_zoom_3"].value
    self.scope_level_4_v_speed = tuning_values["max_v_angular_speed_zoom_3"].value
    self.scope_level_5_h_speed = tuning_values["max_h_angular_speed_zoom_4"].value
    self.scope_level_5_v_speed = tuning_values["max_v_angular_speed_zoom_4"].value

  def __repr__(self) -> str:
    return f"{self.name}, {self.file}, {self.bundle_file}"

  def _map_name(self) -> None:
    split_file = self.file.split("/")
    filename = split_file[-1].removesuffix(".sighttunec")  # filename without "".sighttunec" extension
    self.name = mods.clean_equipment_name(filename, "sight")
    if (mapped_eqipment := mods.map_equipment(self.name, "sight")):
      self.display_name = mapped_eqipment["name"]
    else:
      self.display_name = self.name

def load_scopes() -> list[Scope]:
  scopes = []
  zoomable_scope = re.compile(r'^\w+[\-_]\d+x\w+$')
  extra_scopes = ["rifle_red_dot_01"]
  base_path = mods.APP_DIR_PATH / "org/editor/entities/hp_weapons/sights"
  for folder in os.listdir(base_path):
    if zoomable_scope.match(folder) or folder in extra_scopes:
      sight_file = list((base_path / folder).glob("*.sighttunec"))[0]
      ee_file = list((base_path / folder).glob("*.ee"))[0]
      scopes.append(Scope(sight_file, ee_file))
  logger.debug("Loaded scopes")
  return sorted(scopes, key=lambda x: x.display_name)

def get_option_elements() -> sg.Column:
  layout = []
  advanced_layout = []
  layout.append([sg.T("Scope: "), sg.Combo([x.display_name for x in ALL_SCOPES], metadata=ALL_SCOPES, k="scope_name", enable_events=True)])
  for i in range(1,6):
    layout.append([
      sg.T(f"Level {i}: "),
      sg.Slider((1, 50), 1.0, 0.1, orientation="h", k=f"scope_level_{i}", s=(50,20), p=((10,0),(0,5)))
    ])
    advanced_layout.append([
      sg.T(i, s=5, justification="center"),
      sg.Slider((0.002, 0.05), 0.002, 0.002, orientation="h", k=f"scope_level_{i}_sensitivity", s=(25,20), p=((25,25),(0,5))),
      sg.Slider((10, 100), 10, 10, orientation="h", k=f"scope_level_{i}_h_speed", s=(10,20), p=((25,25),(0,5))),
      sg.Slider((10, 100), 10, 10, orientation="h", k=f"scope_level_{i}_v_speed", s=(10,20), p=((25,25),(0,5)))
    ])
  layout.append([sg.Checkbox(" Enable advanced sensitivity control", False, k="scope_advanced_sensitivity", enable_events=True), sg.T("(scroll down)", font="_ 12 italic", text_color="orange", k="scope_advanced_sensitivity_note", visible=False)])
  layout.append([sg.pin(sg.Column([
      [sg.T("Level", s=5, justification="center"), sg.T("Sensitivity", s=33, justification="center"), sg.T("Max H-Speed", s=15, justification="center"), sg.T("Max V-Speed", s=15, justification="center")],
      *advanced_layout
    ], k="scope_advanced_sensitivity_settings", visible=False))])
  return sg.Column(layout)

def get_selected_scope(window: sg.Window, values: dict) -> Scope:
  scope_list = window["scope_name"].metadata
  scope_name = values.get("scope_name")
  if scope_name:
    try:
      scope_index = window["scope_name"].Values.index(scope_name)
      return scope_list[scope_index]
    except ValueError as _e:  # user typed/edited data in box and we cannot match
      pass
  return None

def handle_event(event: str, window: sg.Window, values: dict) -> None:
  if event == "scope_name":
    selected_scope = get_selected_scope(window, values)
    for i in range(1,6):
      window[f"scope_level_{i}"].update(getattr(selected_scope, f"scope_level_{i}"))
      window[f"scope_level_{i}_sensitivity"].update(getattr(selected_scope, f"scope_level_{i}_sensitivity"))
      window[f"scope_level_{i}_h_speed"].update(getattr(selected_scope, f"scope_level_{i}_h_speed"))
      window[f"scope_level_{i}_v_speed"].update(getattr(selected_scope, f"scope_level_{i}_v_speed"))
  if event == "scope_advanced_sensitivity":
    window["scope_advanced_sensitivity_note"].update(visible=values["scope_advanced_sensitivity"])
    window["scope_advanced_sensitivity_settings"].update(visible=values["scope_advanced_sensitivity"])
    window.refresh()
    window["options"].contents_changed()

def add_mod(window: sg.Window, values: dict) -> dict:
  selected_scope = get_selected_scope(window, values)
  if not selected_scope:
    return {
      "invalid": "Please select a scope first"
    }

  mod_settings = {
    "key": f"modify_scope_{selected_scope.name}",
    "invalid": None,
    "options": {
      "name": selected_scope.name,
      "display_name": selected_scope.display_name,
      "file": selected_scope.file,
      "bundle_file": selected_scope.bundle_file,
    }
  }
  advanced_settings = {"advanced_sensitivity": values["scope_advanced_sensitivity"]}
  for i in range(1,6):
    mod_settings["options"][f"level_{i}"] = values[f"scope_level_{i}"]
    advanced_settings[f"level_{i}_sensitivity"] = values[f"scope_level_{i}_sensitivity"]
    advanced_settings[f"level_{i}_h_speed"] = values[f"scope_level_{i}_h_speed"]
    advanced_settings[f"level_{i}_v_speed"] = values[f"scope_level_{i}_v_speed"]

  if values["scope_advanced_sensitivity"]:
    mod_settings["options"].update(advanced_settings)
  return mod_settings

def format_options(options: dict) -> str:
  # safely handle old save files without display_name
  display_name = options.get("display_name", options.get("name"))
  return f"Modify Scope Zoom: {display_name} ({options['level_1']}, {options['level_2']}, {options['level_3']}, {options['level_4']}, {options['level_5']}, Advanced Settings: {options.get('advanced_sensitivity')})"

def handle_key(mod_key: str) -> bool:
  return mod_key.startswith("modify_scope")

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
  if options.get("advanced_sensitivity"):
    updates.extend([
      {"offset": tuning_values["sensitivity_modifier_zoom_0"].data_offset, "value": options["level_1_sensitivity"]},
      {"offset": tuning_values["sensitivity_modifier_zoom_1"].data_offset, "value": options["level_2_sensitivity"]},
      {"offset": tuning_values["sensitivity_modifier_zoom_2"].data_offset, "value": options["level_3_sensitivity"]},
      {"offset": tuning_values["sensitivity_modifier_zoom_3"].data_offset, "value": options["level_4_sensitivity"]},
      {"offset": tuning_values["sensitivity_modifier_zoom_4"].data_offset, "value": options["level_5_sensitivity"]},
      {"offset": tuning_values["max_h_angular_speed_zoom_0"].data_offset, "value": options["level_1_h_speed"]},
      {"offset": tuning_values["max_v_angular_speed_zoom_0"].data_offset, "value": options["level_1_v_speed"]},
      {"offset": tuning_values["max_h_angular_speed_zoom_1"].data_offset, "value": options["level_2_h_speed"]},
      {"offset": tuning_values["max_v_angular_speed_zoom_1"].data_offset, "value": options["level_2_v_speed"]},
      {"offset": tuning_values["max_h_angular_speed_zoom_2"].data_offset, "value": options["level_3_h_speed"]},
      {"offset": tuning_values["max_v_angular_speed_zoom_2"].data_offset, "value": options["level_3_v_speed"]},
      {"offset": tuning_values["max_h_angular_speed_zoom_3"].data_offset, "value": options["level_4_h_speed"]},
      {"offset": tuning_values["max_v_angular_speed_zoom_3"].data_offset, "value": options["level_4_v_speed"]},
      {"offset": tuning_values["max_h_angular_speed_zoom_4"].data_offset, "value": options["level_5_h_speed"]},
      {"offset": tuning_values["max_v_angular_speed_zoom_4"].data_offset, "value": options["level_5_v_speed"]},
    ])
  mods.apply_updates_to_file(file, updates)

def handle_update(mod_key: str, mod_options: dict, version: str) -> tuple[str, dict]:
  """
  2.2.2
  - Replace full filepath with just scope name in mod_key
  2.2.0
  - Use formatted name from 'name_map.yaml' as display_name
  - Fix formatting of file path
  """
  # 2.1.9 and prior had double backslashes in file paths
  selected_scope = next((
    x for x in ALL_SCOPES if (
      x.file == mod_options["file"] or  # properly formatted path with single forward slash (/)
      x.file == mod_options["file"].replace("\\", "/")  # old path with double backslash (\\)
    )), None
  )
  if not selected_scope:
    raise ValueError(f"Unable to match scope {mod_options.get("display_name", mod_options.get("name"))}")

  updated_mod_key = f"modify_scope_{selected_scope.name}"
  updated_mod_options = mod_options
  updated_mod_options["name"] = selected_scope.name
  updated_mod_options["display_name"] = selected_scope.display_name
  updated_mod_options["file"] = selected_scope.file
  updated_mod_options["bundle_file"] = selected_scope.bundle_file
  return updated_mod_key, updated_mod_options

ALL_SCOPES = load_scopes()
