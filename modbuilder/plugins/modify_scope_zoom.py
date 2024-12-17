from modbuilder import mods
from pathlib import Path
import FreeSimpleGUI as sg
import re, os

DEBUG = False
NAME = "Modify Scope Zoom"
DESCRIPTION = "Modify the magnification for all five zoom levels of each scope. Use advanced controls to customize the sensitivity and maximum horizontal/vertical angular speed while zoomed in."

class Scope:
  def __init__(self, file: Path, bundle_file: Path) -> None:
    self.file = mods.get_relative_path(file)
    self.bundle_file = mods.get_relative_path(bundle_file)
    self._map_name()
    self.scope_level_1 = mods.read_file_at_offset(file, 100, "f32")
    self.scope_level_2 = mods.read_file_at_offset(file, 104, "f32")
    self.scope_level_3 = mods.read_file_at_offset(file, 108, "f32")
    self.scope_level_4 = mods.read_file_at_offset(file, 112, "f32")
    self.scope_level_5 = mods.read_file_at_offset(file, 116, "f32")
    self.scope_level_1_sensitivity = round(mods.read_file_at_offset(file, 120, "f32"), 2)
    self.scope_level_2_sensitivity = round(mods.read_file_at_offset(file, 124, "f32"), 2)
    self.scope_level_3_sensitivity = round(mods.read_file_at_offset(file, 128, "f32"), 2)
    self.scope_level_4_sensitivity = round(mods.read_file_at_offset(file, 132, "f32"), 2)
    self.scope_level_5_sensitivity = round(mods.read_file_at_offset(file, 136, "f32"), 2)
    self.scope_level_1_h_speed = mods.read_file_at_offset(file, 140, "f32")
    self.scope_level_1_v_speed = mods.read_file_at_offset(file, 144, "f32")
    self.scope_level_2_h_speed = mods.read_file_at_offset(file, 148, "f32")
    self.scope_level_2_v_speed = mods.read_file_at_offset(file, 152, "f32")
    self.scope_level_3_h_speed = mods.read_file_at_offset(file, 156, "f32")
    self.scope_level_3_v_speed = mods.read_file_at_offset(file, 160, "f32")
    self.scope_level_4_h_speed = mods.read_file_at_offset(file, 164, "f32")
    self.scope_level_4_v_speed = mods.read_file_at_offset(file, 168, "f32")
    self.scope_level_5_h_speed = mods.read_file_at_offset(file, 172, "f32")
    self.scope_level_5_v_speed = mods.read_file_at_offset(file, 176, "f32")

  def __repr__(self) -> str:
    return f"{self.name}, {self.file}, {self.bundle_file}"

  def _map_name(self) -> None:
    filename = self.file.split("/")[-1].replace(".sighttunec","")
    mapped_name = mods.map_equipment_name(filename, "sights")
    self.name = mapped_name

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
  return sorted(scopes, key=lambda x: x.name)

def get_option_elements() -> sg.Column:
  scopes = load_scopes()
  layout = []
  advanced_layout = []
  layout.append([sg.T("Scope: "), sg.Combo([x.name for x in scopes], k="scope_name", enable_events=True)])
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

def handle_event(event: str, window: sg.Window, values: dict) -> None:
  if event == "scope_name":
    scope_name = values["scope_name"]
    scopes = load_scopes()
    selected_scope = next(x for x in scopes if x.name == scope_name)
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
  scope_name = values["scope_name"]
  if not scope_name:
    return {
      "invalid": "Please select a scope first"
    }

  scopes = load_scopes()
  selected_scope = next(x for x in scopes if x.name == scope_name)

  mod_settings = {
    "key": f"modify_scope_{selected_scope.file}",
    "invalid": None,
    "options": {
      "name": scope_name,
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

def format(options: dict) -> str:
  return f"Modify Scope Zoom: {options['name']} ({options['level_1']}, {options['level_2']}, {options['level_3']}, {options['level_4']}, {options['level_5']}, Advanced Settings: {options.get('advanced_sensitivity')})"

def handle_key(mod_key: str) -> bool:
  return mod_key.startswith("modify_scope")

def get_files(options: dict) -> list[str]:
  return [options["file"]]

def merge_files(files: list[str], options: dict) -> None:
  lookup = mods.get_sarc_file_info(mods.APP_DIR_PATH / "org" / options["bundle_file"])
  mods.merge_into_archive(options["file"].replace("\\", "/"), options["bundle_file"], lookup)

def process(options: dict) -> None:
  file = options["file"]

  mods.update_file_at_offset(file, 100, options["level_1"])
  mods.update_file_at_offset(file, 104, options["level_2"])
  mods.update_file_at_offset(file, 108, options["level_3"])
  mods.update_file_at_offset(file, 112, options["level_4"])
  mods.update_file_at_offset(file, 116, options["level_5"])
  if options.get("advanced_sensitivity"):
    mods.update_file_at_offset(file, 120, options["level_1_sensitivity"])
    mods.update_file_at_offset(file, 124, options["level_2_sensitivity"])
    mods.update_file_at_offset(file, 128, options["level_3_sensitivity"])
    mods.update_file_at_offset(file, 132, options["level_4_sensitivity"])
    mods.update_file_at_offset(file, 136, options["level_5_sensitivity"])
    mods.update_file_at_offset(file, 140, options["level_1_h_speed"])
    mods.update_file_at_offset(file, 144, options["level_1_v_speed"])
    mods.update_file_at_offset(file, 148, options["level_2_h_speed"])
    mods.update_file_at_offset(file, 152, options["level_2_v_speed"])
    mods.update_file_at_offset(file, 156, options["level_3_h_speed"])
    mods.update_file_at_offset(file, 160, options["level_3_v_speed"])
    mods.update_file_at_offset(file, 164, options["level_4_h_speed"])
    mods.update_file_at_offset(file, 168, options["level_4_v_speed"])
    mods.update_file_at_offset(file, 172, options["level_5_h_speed"])
    mods.update_file_at_offset(file, 176, options["level_5_v_speed"])

UPDATE_VERSION = "2.2.0"
def handle_update(mod_key: str, mod_options: dict, _version: str) -> tuple[str, dict]:
  scopes = load_scopes()
  selected_scope = next(
    x for x in scopes if (
      x.file == mod_options["file"] or  # properly formatted path with single forward slash (/)
      x.file == mod_options["file"].replace("\\", "/")  # old path with double backslash (\\)
    )
  )
  if not selected_scope:
    raise ValueError(f"Unable to match scope {mod_options['name']}")
  updated_mod_key = f"modify_scope_{selected_scope.file}"
  updated_mod_options = mod_options
  updated_mod_options["name"] = selected_scope.name
  updated_mod_options["file"] = selected_scope.file
  updated_mod_options["bundle_file"] = selected_scope.bundle_file
  return updated_mod_key, updated_mod_options
