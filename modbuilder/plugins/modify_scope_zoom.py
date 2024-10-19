from modbuilder import mods, PySimpleGUI_License
from pathlib import Path
import PySimpleGUI as sg
import re, os

DEBUG = False
NAME = "Modify Scope Zoom"
DESCRIPTION = "Modify the magnification for all five zoom levels of each scope. Use advanced controls to customize the sensitivity and maximum horizontal/vertical angular speed while zoomed in."

class Scope:
  def __init__(self, file: Path, bundle_file: Path, name: str) -> None:
    self.file = file
    self.bundle_file = bundle_file
    self.name = name
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

def map_scope_name(folder: str) -> str:
  if folder == "rifle_scope_night_vision_4-8x_100mm_01":
    return "Angler 4-8x100 Night Vision Rifle"
  if folder == "rifle_scope_8-16x_50mm_01":
    return "Argus 8-16x50 Rifle"
  if folder == "rifle_scope_1-4x_24mm_01":
    return "Ascent 1-4x24 Rifle"
  if folder == "scope_muzzleloader_4-8x32_01":
    return "Galileo 4-8x32 Muzzleloader"
  if folder == "rifle_scope_night_vision_1-4x_24mm_01":
    return "GenZero 1-4x24 Night Vision Rifle"
  if folder == "crossbow_scope_1-4x_24mm_01":
    return "Hawken 1-4x24 Crossbow"
  if folder == "rifle_scope_4-8x_32mm_01":
    return "Helios 4-8x32 Rifle"
  if folder == "scope_3-7x_33mm_01":
    return "Hermes 3-7x33 Handgun-Shotgun"
  if folder == "rifle_scope_4-8x_42mm_01":
    return "Hyperion 4-8x42 Rifle"
  if folder == "handgun_scope_2-4x_20mm_01":
    return "Goshawk Redeye 2-4x20 Handgun"
  if folder == "rifle_scope_3_9x44mm_01":
    return "Falcon 3-9x44 Drilling Shotgun"
  if folder == "shotgun_scope_1-4x_20mm_01":
    return "Meridian 1-4x20 Shotgun"
  if folder == "rifle_scope_4-12x_33mm_01":
    return "Odin 4-12x33 Rifle"
  if folder == "rifle_red_dot_01":
    return "Red Raptor Reflex"
  if folder == "rifle_scope_6-10x_20mm_01":
    return "_PLACEHOLDER 6-10x20 Rifle"
  return folder

def load_scopes() -> list[Scope]:
  scopes = []
  zoomable_scope = re.compile(r'^\w+[\-_]\d+x\w+$')
  extra_scopes = ["rifle_red_dot_01"]
  base_path = mods.APP_DIR_PATH / "org/editor/entities/hp_weapons/sights"
  for folder in os.listdir(base_path):
    if zoomable_scope.match(folder) or folder in extra_scopes:
      sight_file = list((base_path / folder).glob("*.sighttunec"))[0]
      ee_file = list((base_path / folder).glob("*.ee"))[0]
      scope_file = os.path.relpath(sight_file, mods.APP_DIR_PATH / "org")
      bundle_file = os.path.relpath(ee_file, mods.APP_DIR_PATH / "org")
      scopes.append(Scope(scope_file, bundle_file, map_scope_name(folder)))
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
    "key": f"modify_scope_{scope_name}",
    "invalid": None,
    "options": {
      "name": f"Modify Scope Zoom: {scope_name}",
      "file": str(selected_scope.file),
      "bundle_file": str(selected_scope.bundle_file),
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
  return f"{options['name']} ({options['level_1']}, {options['level_2']}, {options['level_3']}, {options['level_4']}, {options['level_5']}, Advanced Settings: {options.get('advanced_sensitivity')})"

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
