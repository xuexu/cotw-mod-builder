from modbuilder import mods
from pathlib import Path
from deca.file import ArchiveFile
from deca.ff_adf import Adf
import FreeSimpleGUI as sg
import re, os

DEBUG = False
NAME = "Modify Weapon"
DESCRIPTION = 'Modify weapon recoil, zeroing settings, and scope settings. Use the "Increase Magazine Size" mod to change mag sizes. Use the "Modify Ammo" mod to edit classes for harvest integrity.'
WARNING = 'Changing zeroing distances does not automatically compensate for bullet drop. Use the in-game firing range to test for each distance. Consider changing ammo kinetic energy with the "Modify Ammo" mod to maintain accuracy at long distances.'
DEFAULT_ZERO_OFFSET = 432
DEFAULT_ANGLE_OFFSET = 436
SHORT_ZERO_OFFSET = 384
SHORT_ANGLE_OFFSET = 388
LONG_ZERO_OFFSET = 480
LONG_ANGLE_OFFSET = 484
# recoil_yaw and recoil_pitch
RECOIL_OFFSETS = [264, 268, 272, 276]

def format_name(name: str) -> str:
  return " ".join([x.capitalize() for x in name.split("_")])

def load_weapon_type(type_key: str) -> list[dict]:
  base_path = mods.APP_DIR_PATH / "org/editor/entities/hp_weapons"
  root = base_path / f"weapon_{type_key}_01/tuning"
  name_pattern = re.compile(r'^(equipment_)?weapon_([\w\d\-]+).wtunec$')
  weapons = []
  for file in root.glob("*.wtunec"):
    if file.name.startswith("weapon_sway"):
        continue
    name_match = name_pattern.match(file.name)
    if name_match:
      matched_name = name_match[2]
      matched_name = patch_name(matched_name)
      if type_key == "shotguns":
        shotgun_suffix = " (Slugs)" if matched_name.endswith("_slugs") else " (Bird/Buckshot)"
      else:
        shotgun_suffix = ""
      clean_name, _v = mods.clean_equipment_name(matched_name.removesuffix("_slugs"), "weapon")
      mapped_weapon = mods.map_equipment(clean_name, "weapon")
      if mapped_weapon:
        name = mapped_weapon["name"] + shotgun_suffix
      else:
        name = matched_name
      file = mods.get_relative_path(file)
      weapons.append({ "name": name, "file": file })
  weapons.sort(key=lambda weapon: weapon["name"])
  return weapons

def load_weapons() -> dict[list[dict]]:
  bows = load_weapon_type("bows")
  handguns = load_weapon_type("handguns")
  rifles = load_weapon_type("rifles")
  shotguns = load_weapon_type("shotguns")

  return {
    "bow": bows,
    "handgun": handguns,
    "rifle": rifles,
    "shotgun": shotguns
  }

def patch_name(name: str) -> str:
  # horrible dirty way to handle edge cases
  # these names in tuning files don't match anything anywhere else and conflict with other names in name_map.yaml
  if name == "compound_bow_02":
    name = "compound_bow_70lb_01"
  if name == "caplock_muzzleloader":
    name = "Hudzik .50 Caplock (Round Ball)"
  if name == "caplock_muzzleloader_minie":
    name = "Hudzik .50 Caplock (Minié Ball)"
  return name

def build_tab(weapon_type: str) -> sg.Tab:
  weapon_list = ALL_WEAPONS[weapon_type]
  return sg.Tab(weapon_type.capitalize(), [
    [sg.Combo([weapon["name"] for weapon in weapon_list], metadata=weapon_list, p=((10,0),(20,10)), k=f"modify_weapon_list_{weapon_type}", enable_events=True, expand_x=True)],
  ], key= f"modify_weapon_tab_{weapon_type}")

def get_option_elements() -> sg.Column:
  layout = [[
      sg.TabGroup([[
        build_tab(key) for key in ALL_WEAPONS
      ]], k="modify_weapon_tab_group", enable_events=True),
    ],
    [sg.Column([
      [sg.T("Decrease Recoil Percentage:")],
      [sg.Slider((0,100), 0, 2, orientation="h", p=((50,0),(0,20)), k="modify_weapon_recoil_percent")],
      [sg.T("Zeroing Settings:"), sg.T('(distance, angle) Level 1 is default. Levels 2 and 3 require the "Zeroing" perk', font="_ 12")],
      [sg.T("Level 1: ", p=((20,0),(10,10))), sg.Input("", size=4, p=((10,0),(0,0)), k="modify_weapon_level_1_distance"), sg.Input("", p=((10,10),(0,0)), k="modify_weapon_level_1_angle")],
      [sg.T("Level 2: ", p=((20,0),(10,10))), sg.Input("", size=4, p=((10,0),(0,0)), k="modify_weapon_level_2_distance"), sg.Input("", p=((10,10),(0,0)), k="modify_weapon_level_2_angle")],
      [sg.T("Level 3: ", p=((20,0),(10,10))), sg.Input("", size=4, p=((10,0),(0,0)), k="modify_weapon_level_3_distance"), sg.Input("", p=((10,10),(0,0)), k="modify_weapon_level_3_angle")],
      [sg.T("Scope Settings:", p=((10, 0), (15, 0)))],
      [sg.Column([
        [sg.T("Scope: ", p=((0,0),(0,10))), sg.Combo([], k="modify_weapon_scopes", p=((10,0),(0,0)), enable_events=True, expand_x=True)],
        [sg.T("Horizontal Offset: ", p=((0,0),(10,10))), sg.Input("", k="modify_weapon_scope_horizontal_offset", p=((10,0),(0,0)), expand_x=True)],
        [sg.T("Vertical Offset: ", p=((0,0),(10,0))), sg.Input("", k="modify_weapon_scope_vertical_offset", p=((10,0),(0,0)), expand_x=True)],
      ], p=((20,10),(10,0)))],
      ]),
  ]]
  return sg.Column(layout)

def get_selected_category(window: sg.Window) -> str:
  active_tab = str(window["modify_weapon_tab_group"].find_currently_active_tab_key()).lower()
  return active_tab.removeprefix("modify_weapon_tab_")

def get_selected_weapon(window: sg.Window, values: dict) -> dict:
  item_type = get_selected_category(window)
  item_list = f"modify_weapon_list_{item_type}"
  item_name = values.get(item_list)
  if item_name:
    try:
      item_index = window[item_list].Values.index(item_name)
      return window[item_list].metadata[item_index]
    except ValueError as _e:  # user typed/edited data in box and we cannot match
      pass
  return None

class WeaponZeroing:
  def __init__(self, one_distance: float, one_angle: float, two_distance: float, two_angle: float, three_distance: float, three_angle: float) -> None:
    self.one_distance = one_distance
    self.one_angle = one_angle
    self.two_distance = two_distance
    self.two_angle = two_angle
    self.three_distance = three_distance
    self.three_angle = three_angle

class WeaponScopeSettings:
  def __init__(self, scope_index: int, scope: str, horizontal_offset: float, vertical_offset: float, horizontal_pos: int, vertical_pos: int) -> None:
    self.scope_index = scope_index
    self.scope = self.parse_name(scope)
    self.horizontal_offset = round(horizontal_offset, 5)
    self.vertical_offset = round(vertical_offset, 5)
    self.horizontal_pos = horizontal_pos
    self.vertical_pos = vertical_pos

  def parse_name(self, scope: str) -> str:
    clean_name, _v = mods.clean_equipment_name(scope, "sight")
    mapped_equipment = mods.map_equipment(clean_name, "sight")
    if mapped_equipment:
      return mapped_equipment["name"]
    return clean_name

  def __repr__(self) -> str:
    return f"{self.scope} [{self.scope_index}], {self.horizontal_pos}, {self.vertical_pos}"

def load_weapon_zeroing(file: str) -> WeaponZeroing:
  short_distance = mods.read_file_at_offset(file, SHORT_ZERO_OFFSET, "f32")
  if short_distance == 0:
    # Weapon does not support multiple zeroing ranges
    return None
  short_angle = round(mods.read_file_at_offset(file, SHORT_ANGLE_OFFSET, "f32"), 4)
  default_distance = mods.read_file_at_offset(file, DEFAULT_ZERO_OFFSET, "f32")
  default_angle = round(mods.read_file_at_offset(file, DEFAULT_ANGLE_OFFSET, "f32"), 4)
  long_distance = mods.read_file_at_offset(file, LONG_ZERO_OFFSET, "f32")
  long_angle = round(mods.read_file_at_offset(file, LONG_ANGLE_OFFSET, "f32"), 4)
  return WeaponZeroing(default_distance, default_angle, short_distance, short_angle, long_distance, long_angle)

def load_weapon_scopes(file: str) -> list[WeaponScopeSettings]:
  adf = Adf()
  with ArchiveFile(open(mods.APP_DIR_PATH / "org" / file, 'rb')) as f:
    adf.deserialize(f)
  scopes = []
  adf_instance = adf.table_instance_full_values[0].value
  if "ScopeOffsetSettings" in adf_instance:
    scope_settings = adf_instance["ScopeOffsetSettings"].value
    for scope_i, scope in enumerate(scope_settings):
      scope_hash = scope.value["ScopeNameHash"].hash_string
      if scope_hash == None:
        continue
      scope_name = scope_hash.decode("utf-8")
      if scope_name == "":
        scope_name = f"_PLACEHOLDER [{scope_i}]"
      scope_horizontal_offset = scope.value["HorizontalOffset"].value
      scope_horizontal_offset_pos = int(scope.value["HorizontalOffset"].data_offset)
      scope_vertical_offset = scope.value["VerticalOffset"].value
      scope_vertical_offset_pos = int(scope.value["VerticalOffset"].data_offset)
      scopes.append(WeaponScopeSettings(scope_i, scope_name, scope_horizontal_offset, scope_vertical_offset, scope_horizontal_offset_pos, scope_vertical_offset_pos))
  scopes.sort(key=lambda x: x.scope)
  return scopes

def zeroing_disabled(disable: bool, window: sg.Window) -> None:
  window[f"modify_weapon_level_1_distance"].update("0", disabled=disable)
  window[f"modify_weapon_level_1_angle"].update("0", disabled=disable)
  window[f"modify_weapon_level_2_distance"].update("0", disabled=disable)
  window[f"modify_weapon_level_2_angle"].update("0", disabled=disable)
  window[f"modify_weapon_level_3_distance"].update("0", disabled=disable)
  window[f"modify_weapon_level_3_angle"].update("0", disabled=disable)

def scope_settings_disabled(disable: bool, window: sg.Window) -> None:
  window[f"modify_weapon_scopes"].update(values=[], disabled=disable)
  window[f"modify_weapon_scope_horizontal_offset"].update("", disabled=disable)
  window[f"modify_weapon_scope_vertical_offset"].update("", disabled=disable)

def handle_event(event: str, window: sg.Window, values: dict) -> None:
  if event.startswith("modify_weapon_list_"):
    selected_weapon = get_selected_weapon(window, values)
    if selected_weapon:
      weapon_zeroing = load_weapon_zeroing(selected_weapon["file"])
      weapon_scopes = load_weapon_scopes(selected_weapon["file"])
      if weapon_zeroing:
        zeroing_disabled(False, window)
        window["modify_weapon_level_1_distance"].update(int(weapon_zeroing.one_distance))
        window["modify_weapon_level_1_angle"].update(weapon_zeroing.one_angle)
        window["modify_weapon_level_2_distance"].update(int(weapon_zeroing.two_distance))
        window["modify_weapon_level_2_angle"].update(weapon_zeroing.two_angle)
        window["modify_weapon_level_3_distance"].update(int(weapon_zeroing.three_distance))
        window["modify_weapon_level_3_angle"].update(weapon_zeroing.three_angle)
      else:
        zeroing_disabled(True, window)
      if weapon_scopes:
        scope_settings_disabled(False, window)
        window["modify_weapon_scopes"].update(values=[s.scope for s in weapon_scopes])
        window["modify_weapon_scopes"].metadata = weapon_scopes
      else:
        scope_settings_disabled(True, window)
  if event.endswith("_weapon_scopes"):
    weapon = get_selected_weapon(window, values)
    weapon_scopes = load_weapon_scopes(weapon["file"])
    selected_scope = values[event]
    if selected_scope:
      scope_index = window[event].Values.index(selected_scope)
    else:
      scope_index = 0
    scope_settings = weapon_scopes[scope_index]
    window["modify_weapon_scope_horizontal_offset"].update(f"{scope_settings.horizontal_offset:.6f}")
    window["modify_weapon_scope_vertical_offset"].update(f"{scope_settings.vertical_offset:.6f}")

def add_mod(window: sg.Window, values: dict) -> dict:
  selected_weapon = get_selected_weapon(window, values)
  if not selected_weapon:
    return {
      "invalid": "Please select weapon first"
    }

  recoil_percent = values["modify_weapon_recoil_percent"]
  one_distance = float(values["modify_weapon_level_1_distance"])
  one_angle = float(values["modify_weapon_level_1_angle"])
  two_distance = float(values["modify_weapon_level_2_distance"])
  two_angle = float(values["modify_weapon_level_2_angle"])
  three_distance = float(values["modify_weapon_level_3_distance"])
  three_angle = float(values["modify_weapon_level_3_angle"])

  weapon_scope = values["modify_weapon_scopes"]
  if weapon_scope:
    weapon_index = window["modify_weapon_scopes"].Values.index(weapon_scope)
    weapon_details = window["modify_weapon_scopes"].metadata[weapon_index]
    weapon_scope_horizontal = float(values["modify_weapon_scope_horizontal_offset"])
    weapon_scope_vertical = float(values["modify_weapon_scope_vertical_offset"])

    return {
      "key": f"weapon_scope_{selected_weapon["name"]}_{weapon_details.scope_index}",
      "invalid": None,
      "options": {
        "name": weapon_details.scope,
        "weapon_name": selected_weapon["name"],
        "file": selected_weapon["file"],
        "horizontal_offset": weapon_scope_horizontal,
        "vertical_offset": weapon_scope_vertical,
        "horizontal_pos": weapon_details.horizontal_pos,
        "vertical_pos": weapon_details.vertical_pos
      }
    }
  else:
    return {
      "key": f"weapon_recoil_{selected_weapon["name"]}", # TODO: remove old key eventually
      "invalid": None,
      "options": {
        "name": selected_weapon["name"],
        "file": selected_weapon["file"],
        "recoil_percent": int(recoil_percent),
        "one_distance": one_distance,
        "one_angle": one_angle,
        "two_distance": two_distance,
        "two_angle": two_angle,
        "three_distance": three_distance,
        "three_angle": three_angle
      }
    }

def format(options: dict) -> str:
  if "recoil_percent" in options:
    return f"Modify Weapon: {options['name']} (-{options['recoil_percent']}% recoil)"
  else:
    return f"Modify Weapon: {options['weapon_name']} Scope ({options['name']})"

def handle_key(mod_key: str) -> bool:
  return mod_key.startswith(("modify_weapon", "weapon_recoil", "weapon_scope"))

def get_files(options: dict) -> list[str]:
  return [options["file"]]

def load_archive_files(base_path: Path) -> list[str]:
  archives = {}
  for file in base_path.glob("*.ee"):
    archive_files = list(mods.get_sarc_file_info(file).keys())
    archives[str(file)] = archive_files
  return archives

def find_archive_files(archive_files: dict, file: str) -> str:
  found_archives = []
  for archive, files in archive_files.items():
    if file in files:
      found_archives.append(mods.get_relative_path(archive))
  return found_archives

def merge_files(files: list[str], options: dict) -> None:
  base_path = mods.APP_DIR_PATH / "org" / Path(files[0]).parent.parent
  archives = load_archive_files(base_path)
  for file in files:
    bundle_files = find_archive_files(archives, file)
    for bundle_file in bundle_files:
      bundle_lookup = mods.get_sarc_file_info(mods.APP_DIR_PATH / "org" / bundle_file)
      mods.merge_into_archive(file, bundle_file, bundle_lookup)

def process(options: dict) -> None:
  file = options["file"]

  if "recoil_percent" in options:
    recoil_multiplier = 1 - options["recoil_percent"] / 100
    mods.update_file_at_offsets(Path(file), RECOIL_OFFSETS, recoil_multiplier, "multiply")

    if "one_distance" in options:
      one_distance = options["one_distance"]
      one_angle = options["one_angle"]
      two_distance = options["two_distance"]
      two_angle = options["two_angle"]
      three_distance = options["three_distance"]
      three_angle = options["three_angle"]

      mods.update_file_at_offset(Path(file), DEFAULT_ZERO_OFFSET, one_distance)
      mods.update_file_at_offset(Path(file), DEFAULT_ANGLE_OFFSET, one_angle)
      mods.update_file_at_offset(Path(file), SHORT_ZERO_OFFSET, two_distance)
      mods.update_file_at_offset(Path(file), SHORT_ANGLE_OFFSET, two_angle)
      mods.update_file_at_offset(Path(file), LONG_ZERO_OFFSET, three_distance)
      mods.update_file_at_offset(Path(file), LONG_ANGLE_OFFSET, three_angle)
  else:
    horizontal_offset = options["horizontal_offset"]
    vertical_offset = options["vertical_offset"]
    mods.update_file_at_offset(Path(file), options["horizontal_pos"], horizontal_offset)
    mods.update_file_at_offset(Path(file), options["vertical_pos"], vertical_offset)

ALL_WEAPONS = load_weapons()
