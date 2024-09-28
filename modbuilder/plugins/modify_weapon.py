from modbuilder import mods, PySimpleGUI_License
from pathlib import Path
from deca.file import ArchiveFile
from deca.ff_adf import Adf
import PySimpleGUI as sg
import re, os

DEBUG = False
NAME = "Modify Weapon"
DESCRIPTION = 'Modify weapon recoil, zeroing settings, and scope settings. Magazine sizes can be changed separately with the "Increase Magazine Size" mod.'
WARNING = 'Changing zeroing distances does not automatically calculate the correct angle to compensate for bullet drop. Use the in-game firing range to test for the proper zeroing angles for each distance. Consider changing ammo kinetic energy with the "Modify Ammo" mod to maintain accuracy at long distances.'
DEFAULT_ZERO_OFFSET = 448
DEFAULT_ANGLE_OFFSET = 452
SHORT_ZERO_OFFSET = 400
SHORT_ANGLE_OFFSET = 404
LONG_ZERO_OFFSET = 496
LONG_ANGLE_OFFSET = 500
# recoil_yaw and recoil_pitch
RECOIL_OFFSETS = [280, 284, 288, 292]

def format_name(name: str) -> str:
  return " ".join([x.capitalize() for x in name.split("_")])

def get_relative_path(path: str) -> str:
  return os.path.relpath(path, mods.APP_DIR_PATH / "org").replace("\\", "/")

def load_weapon_type(root: Path) -> list[dict]:
  name_pattern = re.compile(r'^(equipment_)?weapon_([\w\d\-]+).wtunec$')
  weapons = []
  for file in root.glob("*.wtunec"):
    if file.name.startswith("weapon_sway"):
        continue
    name_match = name_pattern.match(file.name)
    if name_match:
      matched_name = name_match[2]
      matched_name = map_weapon(matched_name)
      file = get_relative_path(file)
      weapons.append({ "name": matched_name, "file": file })
  weapons.sort(key=lambda weapon: weapon["name"])
  return weapons

def load_weapons() -> dict[list[dict]]:
  base_path = mods.APP_DIR_PATH / "org/editor/entities/hp_weapons"

  bows = load_weapon_type(base_path / "weapon_bows_01/tuning")
  handguns = load_weapon_type(base_path / "weapon_handguns_01/tuning")
  rifles = load_weapon_type(base_path / "weapon_rifles_01/tuning")
  shotguns = load_weapon_type(base_path / "weapon_shotguns_01/tuning")

  return {
    "bow": bows,
    "handgun": handguns,
    "rifle": rifles,
    "shotgun": shotguns
  }

def map_weapon(name: str) -> str:
  # Bows
  if name == "compound_bow_01":
    return "Razorback Lite CB-60"
  if name == "compound_bow_01b":
    return "Bearclaw Lite CB-60"
  if name == "compound_bow_02":
    return "Hawk Edge CB-70"
  if name == "compound_bow_orpheus":
    return "Koter CB-65"
  if name == "crossbow_01":
    return "Crosspoint CB-165"
  if name == "longbow_01":
    return "Houyi Recurve Bow"
  if name == "recurve_bow_01":
    return "Stenberg Takedown Recurve Bow"
  if name == "traditional_longbow_01":
    return "Alexander Longbow"
  # Handguns
  if name == "handgun_357":
    return "Focoso 357"
  if name == "handgun_410":
    return "Mangiafico 410/45 Colt (.410 Birdshot)"
  if name == "handgun_44":
    return ".44 Magnum"
  if name == "handgun_454":
    return "Rhino/Sundberg 454"
  if name == "handgun_45c":
    return "Mangiafico 410/45 Colt (.45 Colt)"
  if name == "handgun_sa_22":
    return "Andersson .22LR"
  if name == "pistol_10mm":
    return "10mm Davani"
  if name == "pistol_ss_243":
    return ".243 R. Cuomo"
  if name == "pistol_ss_4570":
    return ".45-70 Jernberg Superior"
  if name == "revolver_45":
    return ".45 Rolleston"
  # Rifles
  if name == "30_30_lever_action":
    return "Whitlock Model 86"
  if name == "45-70_lever_action":
    return "Coachmate Lever .45-70"
  if name == "airrifle_45":
    return "Vasquez Cyclone .45"
  if name == "ba_rifle_22h":
    return "Kullman .22H"
  if name == "ba_rifle_308_01":
    return "Olsson Model 23 .308"
  if name == "ba_rifle_338_01":
    return "Tsurugi LLR .338"
  if name == "ba_rifle_7mm_01":
    return "Malmer 7mm Magnum"
  if name == "caplock_muzzleloader":
    return "Hudzik .50 Caplock (Round Ball)"
  if name == "caplock_muzzleloader_minie":
    return "Hudzik .50 Caplock (Minié Ball)"
  if name == "la_rifle_44_lever_action":
    return "Moradi Model 1894"
  if name == "rifle_drilling":
    return "Grelck Drilling Rifle (9.3X74R)"
  if name == "rifle_muzzleloader_50_01":
    return "Curman .50 Inline"
  if name == "rifles_223":
    return ".223 Docent"
  if name == "rifles_22_250":
    return "Zagan Varminter .22-250"
  if name == "rifles_243":
    return "Ranger .243"
  if name == "rifles_270":
    return ".270 Huntsman"
  if name == "rifles_3006":
    return "Eckers .30-06"
  if name == "rifles_300_wby":
    return ".300 Canning Magnum"
  if name == "rifles_303":
    return "F.L. Sporter .303"
  if name == "rifles_577_450":
    return "Gandhare Rifle"
  if name == "rifles_6_5mm_b14":
    return "Martensson 6.5mm"
  if name == "rifles_m1_garand_3006":
    return "M1 Iwaniec"
  if name == "rifles_mosin_1890":
    return "Solokhin MN1890"
  if name == "sa_rifle_22lr":
    return "Viriant .22LR"
  if name == "sa_rifle_ar10_308":
    return "ZARZA-10 .308"
  if name == "sa_rifle_ar15_223":
    return "ZARZA-15 .223"
  if name == "sa_rifle_ar15_22lr":
    return "ZARZA-15 .22LR"
  if name == "sa_rifle_ar15_300":
    return "Arzyna .300 Mag Tactical"
  if name == "ss_rifle_338_01":
    return "Rangemaster 338"
  if name == "ss_rifle_7mm_01":
    return "7mm Empress/Regent Magnum"
  if name == "sxs_rifle_470ne":
    return "King 470DB"
  # Shotguns
  if name == "shotgun_1887_la":
    return "Miller Model 1891 (Bird/Buckshot)"
  if name == "shotgun_1887_la_slugs":
    return "Miller Model 1891 (Slug)"
  if name == "shotgun_1897_pa":
    return"Couso Model 1897 (Bird/Buckshot)"
  if name == "shotgun_1897_pa_slugs":
    return "Couso Model 1897 (Slug)"
  if name == "shotgun_drilling":
    return "Grelck Drilling Rifle (Bird/Buckshot)"
  if name == "shotgun_drilling_slugs":
    return "Grelck Drilling Rifle (Slug)"
  if name == "shotgun_ou":
    return "Caversham Steward 12G (Bird/Buckshot)"
  if name == "shotgun_ou_slugs":
    return "Caversham Steward 12G (Slug)"
  if name == "shotgun_pa":
    return "Cacciatore 12G (Bird/Buckshot)"
  if name == "shotgun_pa_slugs":
    return "Cacciatore 12G (Slug)"
  if name == "shotgun_sa":
    return "Nordin 20SA (Bird/Buckshot)"
  if name == "shotgun_sa_slugs":
    return "Nordin 20SA (Slug)"
  if name == "shotgun_sa_10ga":
    return "Strandberg 10SA (Bird/Buckshot)"
  if name == "shotgun_sa_10ga_slugs":
    return "Strandberg 10SA (Slug)"
  if name == "shotgun_sbs":
    return "Strecker SxS 20G (Bird/Buckshot)"
  if name == "shotgun_sbs_slugs":
    return "Strecker SxS 20G (Slug)"
  # Placeholders (future DLC?)
  if name == "sa_rifle_30-60":
    return "_PLACEHOLDER Single-Action 30-60 Rifle"
  if name == "sa_rifle_308":
    return "_PLACEHOLDER Single-Action 308 Rifle"
  if name == "sa_rifle_7_62":
    return "_PLACEHOLDER Single-Action 7.62 Rifle"
  # NO MATCH
  return name

def build_weapon_tab(weapon_type: str, weapons: list[dict]) -> sg.Tab:
  type_key = weapon_type.lower()
  weapon_names = [x["name"] for x in weapons]
  return sg.Tab(weapon_type, [
    [sg.Combo(weapon_names, p=((10,0),(20,10)), k=f"{type_key}_weapon", enable_events=True)],
    [sg.T("Decrease Recoil Percentage:")],
    [sg.Slider((0,100), 0, 2, orientation="h", p=((50,0),(0,20)), k=f"{type_key}_recoil_percent")],
    [sg.T("Zeroing Settings:"), sg.T('(distance, angle) Level 1 is default. Levels 2 and 3 require the "Zeroing" perk', font="_ 12")],
    [sg.T("Level 1: ", p=((20,0),(10,10))), sg.Input("", size=4, p=((10,0),(0,0)), k=f"{type_key}_level_1_distance"), sg.Input("", p=((10,10),(0,0)), k=f"{type_key}_level_1_angle")],
    [sg.T("Level 2: ", p=((20,0),(10,10))), sg.Input("", size=4, p=((10,0),(0,0)), k=f"{type_key}_level_2_distance"), sg.Input("", p=((10,10),(0,0)), k=f"{type_key}_level_2_angle")],
    [sg.T("Level 3: ", p=((20,0),(10,10))), sg.Input("", size=4, p=((10,0),(0,0)), k=f"{type_key}_level_3_distance"), sg.Input("", p=((10,10),(0,0)), k=f"{type_key}_level_3_angle")],
    [sg.T("Scope Settings:", p=((10, 0), (15, 0)))],
    [sg.Column([
      [sg.T("Scope: ", p=((0,0),(0,10))), sg.Combo([], k=f"{type_key}_weapon_scopes", p=((10,0),(0,0)), enable_events=True, expand_x=True)],
      [sg.T("Horizontal Offset: ", p=((0,0),(10,10))), sg.Input("", k=f"{type_key}_weapon_scope_horizontal_offset", p=((10,0),(0,0)), expand_x=True)],
      [sg.T("Vertical Offset: ", p=((0,0),(10,0))), sg.Input("", k=f"{type_key}_weapon_scope_vertical_offset", p=((10,0),(0,0)), expand_x=True)],
    ], p=((20,10),(10,0)))],
    [sg.T("")]
  ], k=f"{weapon_type}_recoil_tab")

def get_option_elements() -> sg.Column:
  weapons = load_weapons()

  layout = [[
    sg.TabGroup([[
      build_weapon_tab("Bow", weapons["bow"]),
      build_weapon_tab("Handgun", weapons["handgun"]),
      build_weapon_tab("Rifle", weapons["rifle"]),
      build_weapon_tab("Shotgun", weapons["shotgun"])
    ]], k="weapon_recoil_group")
  ]]

  return sg.Column(layout)

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
    if "illum_iron" in scope:
      return "Iron Sights"
    if "red_dot" in scope:
      return "Red Dot"
    if "reflex" in scope:
      return "Reflex"
    if scope.startswith("compound_bow_1pin_illum"):
      return "Brightsight Single-Pin"
    if scope.startswith("compound_bow_3pin"):
      return "Swift-Mark 3-pin"
    if scope.startswith("compound_bow_5pin"):
      return "Swift-Mark 5-pin"
    if scope.startswith("compound_bow_rangefinder"):
      return "Brightsignt Rangefinder"
    if scope.startswith("crossbow_scope_1-5x_30mm"):
      return "Hawken 1-5x30"
    if scope.startswith("equipment_scope_3-7x_33mm"):
      return "Hermes 3-7x33"
    if scope.startswith("equipment_scope_muzzleloader_4-8x32"):
      return "Galileo 4-8x32"
    if scope.startswith("handgun_scope_2-4x_20mm"):
      return "Goshawk Redeye 2-4x20"
    if scope.startswith("rifle_scope_1-4x_24mm"):
      return "Ascent 1-4x24"
    if scope.startswith("rifle_scope_3_9x44mm"):
      return "Falcon 3-9x44 Drilling"
    if scope.startswith("rifle_scope_4-8x_32mm"):
      return "Helios 4-8x32"
    if scope.startswith("rifle_scope_4-8x_42mm"):
      return "Hyperion 4-8x42"
    if scope.startswith("rifle_scope_4-12x_33mm"):
      return "Odin 4-12x33"
    if scope.startswith("rifle_scope_8-16x_50mm"):
      return "Argus 8-16x50"
    if scope.startswith("rifle_scope_night_vision_1-4x_24mm"):
      return "GenZero 1-4x24 Night Vision"
    if scope.startswith("rifle_scope_night_vision_4-8x_100mm"):
      return "Angler 4-8x100 Night Vision"
    if scope.startswith("shotgun_scope_1-4x_20mm"):
      return "Meridian 1-4x20"
    # Placeholder (future DLC?)
    if scope.startswith("la_rifle_scope_6-10x_20mm"):
      return "_PLACEHOLDER Lever-Action 6-10x20"
    # NO MATCH
    return scope

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
        scope_name = f"unknown scope [{scope_i}]"
      else:
        scope_name = f"{scope_name.replace('equipment_sight_', '')} [{scope_i}]"
      scope_horizontal_offset = scope.value["HorizontalOffset"].value
      scope_horizontal_offset_pos = int(scope.value["HorizontalOffset"].data_offset)
      scope_vertical_offset = scope.value["VerticalOffset"].value
      scope_vertical_offset_pos = int(scope.value["VerticalOffset"].data_offset)
      scopes.append(WeaponScopeSettings(scope_i, scope_name, scope_horizontal_offset, scope_vertical_offset, scope_horizontal_offset_pos, scope_vertical_offset_pos))
  scopes.sort(key=lambda x: x.scope)
  return scopes

def zeroing_disabled(disable: bool, type_key: str, window: sg.Window) -> None:
  window[f"{type_key}_level_1_distance"].update("0", disabled=disable)
  window[f"{type_key}_level_1_angle"].update("0", disabled=disable)
  window[f"{type_key}_level_2_distance"].update("0", disabled=disable)
  window[f"{type_key}_level_2_angle"].update("0", disabled=disable)
  window[f"{type_key}_level_3_distance"].update("0", disabled=disable)
  window[f"{type_key}_level_3_angle"].update("0", disabled=disable)

def scope_settings_disabled(disable: bool, type_key: str, window: sg.Window) -> None:
  window[f"{type_key}_weapon_scopes"].update(values=[], disabled=disable)
  window[f"{type_key}_weapon_scope_horizontal_offset"].update("", disabled=disable)
  window[f"{type_key}_weapon_scope_vertical_offset"].update("", disabled=disable)

def handle_event(event: str, window: sg.Window, values: dict) -> None:
  if event.endswith("_weapon"):
    type_key = event.split("_")[0]
    weapons = load_weapons()[type_key]
    weapon_name = values[event]
    weapon = next(w for w in weapons if w["name"] == weapon_name)
    weapon_zeroing = load_weapon_zeroing(weapon["file"])
    weapon_scopes = load_weapon_scopes(weapon["file"])
    if weapon_zeroing:
      zeroing_disabled(False, type_key, window)
      window[f"{type_key}_level_1_distance"].update(int(weapon_zeroing.one_distance))
      window[f"{type_key}_level_1_angle"].update(weapon_zeroing.one_angle)
      window[f"{type_key}_level_2_distance"].update(int(weapon_zeroing.two_distance))
      window[f"{type_key}_level_2_angle"].update(weapon_zeroing.two_angle)
      window[f"{type_key}_level_3_distance"].update(int(weapon_zeroing.three_distance))
      window[f"{type_key}_level_3_angle"].update(weapon_zeroing.three_angle)
    else:
      zeroing_disabled(True, type_key, window)
    if weapon_scopes:
      scope_settings_disabled(False, type_key, window)
      window[f"{type_key}_weapon_scopes"].update(values=[s.scope for s in weapon_scopes])
      window[f"{type_key}_weapon_scopes"].metadata = weapon_scopes
    else:
      scope_settings_disabled(True, type_key, window)
  if event.endswith("_weapon_scopes"):
    type_key = event.split("_")[0]
    weapons = load_weapons()[type_key]
    weapon_name = values[f"{type_key}_weapon"]
    weapon = next(w for w in weapons if w["name"] == weapon_name)
    weapon_scopes = load_weapon_scopes(weapon["file"])
    selected_scope = values[event]
    if selected_scope:
      scope_index = window[event].Values.index(selected_scope)
    else:
      scope_index = 0
    scope_settings = weapon_scopes[scope_index]
    window[f"{type_key}_weapon_scope_horizontal_offset"].update(f"{scope_settings.horizontal_offset:.6f}")
    window[f"{type_key}_weapon_scope_vertical_offset"].update(f"{scope_settings.vertical_offset:.6f}")

def add_mod(window: sg.Window, values: dict) -> dict:
  active_tab = window["weapon_recoil_group"].find_currently_active_tab_key().lower()
  active_tab = active_tab.split("_")[0]
  weapon_name = values[f"{active_tab}_weapon"]
  if not weapon_name:
    return {
      "invalid": "Please select weapon first"
    }

  weapons = load_weapons()[active_tab]
  recoil_percent = values[f"{active_tab}_recoil_percent"]
  one_distance = float(values[f"{active_tab}_level_1_distance"])
  one_angle = float(values[f"{active_tab}_level_1_angle"])
  two_distance = float(values[f"{active_tab}_level_2_distance"])
  two_angle = float(values[f"{active_tab}_level_2_angle"])
  three_distance = float(values[f"{active_tab}_level_3_distance"])
  three_angle = float(values[f"{active_tab}_level_3_angle"])
  weapon = next(w for w in weapons if w["name"] == weapon_name)
  weapon_file = weapon["file"]

  weapon_scope = values[f"{active_tab}_weapon_scopes"]
  if weapon_scope:
    weapon_index = window[f"{active_tab}_weapon_scopes"].Values.index(weapon_scope)
    weapon_details = window[f"{active_tab}_weapon_scopes"].metadata[weapon_index]
    weapon_scope_horizontal = float(values[f"{active_tab}_weapon_scope_horizontal_offset"])
    weapon_scope_vertical = float(values[f"{active_tab}_weapon_scope_vertical_offset"])

    return {
      "key": f"weapon_scope_{weapon_name}_{weapon_details.scope_index}",
      "invalid": None,
      "options": {
        "name": weapon_details.scope,
        "weapon_name": weapon_name,
        "file": weapon_file,
        "horizontal_offset": weapon_scope_horizontal,
        "vertical_offset": weapon_scope_vertical,
        "horizontal_pos": weapon_details.horizontal_pos,
        "vertical_pos": weapon_details.vertical_pos
      }
    }
  else:
    return {
      "key": f"weapon_recoil_{weapon_name}", # TODO: remove old key eventually
      "invalid": None,
      "options": {
        "name": weapon_name,
        "file": weapon_file,
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
  return mod_key.startswith("weapon_recoil") or mod_key.startswith("weapon_scope")

def get_files(options: dict) -> list[str]:
  return [options["file"]]

def load_archive_files(base_path: Path):
  archives = {}
  for file in base_path.glob("*.ee"):
    archive_files = list(mods.get_sarc_file_info(file).keys())
    archives[str(file)] = archive_files
  return archives

def find_archive_files(archive_files: dict, file: str) -> str:
  found_archives = []
  for archive, files in archive_files.items():
    if file in files:
      found_archives.append(os.path.relpath(archive, mods.APP_DIR_PATH / "org"))
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
