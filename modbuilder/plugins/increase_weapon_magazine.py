from modbuilder import mods, PySimpleGUI_License
from pathlib import Path
from deca.ff_rtpc import rtpc_from_binary, RtpcNode
import PySimpleGUI as sg

DEBUG = False
NAME = "Increase Weapon Magazine"
DESCRIPTION = "Increase the magazine size of weapons. All variants of a selected weapon will be updated."
FILE = "settings/hp_settings/equipment_data.bin"

class Weapon:
  __slots__ = (
    'name', 'type', 'magazine_size', 'magazine_data_offsets'
  )

  def __init__(self, weapon_data: RtpcNode) -> None:
    weapon_name = parse_weapon_name(weapon_data)
    self.name, self.type = map_weapon(weapon_name)
    magazine = weapon_data.child_table[1].prop_table[2]
    self.magazine_size = magazine.data
    self.magazine_data_offsets = [magazine.data_pos]

def parse_weapon_name(weapon_data: RtpcNode) -> dict:
  name = ""
  for i in [4,5,6]:
    raw_name = weapon_data.prop_table[i].data
    if type(raw_name) is bytes:
      name = raw_name.decode("utf-8")
      if name == "store_featured":
        name = ""
        continue
      break
  if not name:
    raise ValueError("Unable to parse weapon name", weapon_data)
  return name

def map_weapon(name: str) -> tuple[str, str]:
  if name.startswith("10 GA O/U Shotgun"):
    return ("Gopi 10G Grand", "Shotgun")
  if name.startswith(".223 Bolt-Action Rifle (223 DOCENT)"):
    return (".223 Docent", "Rifle")
  if name.startswith(".22LR Semi-Auto Rifle"):
    return ("Viriant .22LR", "Rifle")
  if name.startswith(".22h BA"):
    return ("Kullman .22H", "Rifle")
  if name.startswith(".243 Bolt-Action Rifle (RANGER .243)"):
    return ("Ranger .243", "Rifle")
  if name.startswith(".270 Bolt-Action Rifle"):
    return (".270 Huntsman", "Rifle")
  if name.startswith(".30-06 Bolt-Action Rifle"):
    return ("Eckers .30-06", "Rifle")
  if name.startswith(".30-30 Lever Action Rifle (WHITLOCK MODEL 86)"):
    return ("Whitlock Model 86", "Rifle")
  if name == ".300 Bolt-Action Rifle":  # only 1 variant and shares beginning of name with .300 Canning Magnum
    return ("Fors Elite .300", "Rifle")
  if name.startswith(".300 Bolt-Action Rifle wby"):
    return (".300 Canning Magnum", "Rifle")
  if name.startswith(".338 Bolt Action Rifle 01 (SAKO TRG 42/TSURUGI LRR)"):
    return ("Tsurugi LLR .338", "Rifle")
  if name.startswith(".338 Mag. Single Shot Rifle"):
    return ("Rangemaster 338", "Rifle")
  if name.startswith(".357 Mag. Revolver (FOCOSO 357)"):
    return ("Focoso 357","Handgun")
  if name.startswith(".375 Bolt Action Rifle"):
    return ("Vallgarda .375", "Rifle")
  if name.startswith(".410 Mag. Revolver"):
    return ("Mangiafico 410/45 Colt", "Handgun")
  if name.startswith(".44 Mag. Revolver"):
    return (".44 Magnum", "Handgun")
  if name.startswith(".44 Magnum Lever Action Rifle"):
    return ("Moradi Model 1894", "Rifle")
  if name.startswith(".450 Bolt-Action Rifle"):
    return ("Johansson .450", "Rifle")
  if name.startswith(".454 Revolver (RHINO 454)"):
    return ("Rhino/Sundberg 454", "Handgun")
  if name.startswith(".470 NE Double-barreled Rifle"):
    return ("King 470DB", "Rifle")
  if name.startswith(".50 Caplock Muzzleloader"):
    return ("Hudzik .50 Caplock", "Rifle")
  if name.startswith(".45-70 Lever Action Rifle.(COACHMATE LEVER .45-70)"):
    return ("Coachmate Lever .45-70", "Rifle")
  if name.startswith("10 GA Semi-Automatic Shotgun"):
    return ("Strandberg 10SA", "Shotgun")
  if name.startswith("12 GA O/U Shotgun"):
    return ("Caversham Steward 12G", "Shotgun")
  if name.startswith("12 GA Pump-Action Shotgun"):
    return ("Cacciatore 12G", "Shotgun")
  if name.startswith("16 GA PA Winchester 1897"):
    return ("Couso Model 1897", "Shotgun")
  if name.startswith("165 lbs.Crossbow (CROSSPOINT CB-165"):
    return ("Crosspoint CB-165", "Bow")
  if name.startswith("1887 Lever Action Shotgun"):
    return ("Miller Model 1891", "Shotgun")
  if name.startswith("20 GA SXS"):
    return ("Strecker SxS 20G", "Shotgun")
  if name.startswith("20 GA Semi-Automatic Shotgun"):
    return ("Nordin 20SA", "Shotgun")
  if name.startswith("22 Semi Auto Pistol Var"):
    return ("Andersson .22LR", "Handgun")
  if name.startswith("22-250 Bolt-Action Rifle"):
    return ("Zagan Varminter .22-250", "Rifle")
  if name.startswith("308 Bolt Action Rifle 01 (Model 21/OLSSON MODEL 23)"):
    return ("Olsson Model 23 .308", "Rifle")
  if name.startswith("45 Air Rifle Synthetic 01"):
    return ("Vasquez Cyclone .45", "Rifle")
  if name.startswith("4570 Pistol Thompson Single-Shot"):
    return (".45-70 Jernberg Superior", "Handgun")
  if name.startswith("6.5mm Bolt-Action B14 Rifle"):
    return ("Martensson 6.5mm", "Rifle")
  if name.startswith("60 lbs.Compound Bow"):
    return ("Bearclaw/Razorback Lite CB-60", "Bow")
  if name.startswith("70 lbs.Compound Bow (HAWK EDGE CB-70)"):
    return ("Hawk Edge CB-70", "Bow")
  if name.startswith("7mm Bolt Action Rifle 01 (700 SPS/MALMER)"):
    return ("Malmer 7mm Magnum", "Rifle")
  if name.startswith("7mm Mag. Single Shot Rifle"):
    return ("7mm Empress/Regent Magnum", "Rifle")
  if name.startswith("AR10 308 20GA Skin"):
    return ("ZARZA-10 .308", "Rifle")
  if name.startswith("AR15 223 20GA Skin"):
    return ("ZARZA-15 .223", "Rifle")
  if name.startswith("AR15 22lr 16GA Skin"):
    return ("ZARZA-15 .22LR", "Rifle")
  if name.startswith("AR15 300 Skin"):
    return ("Arzyna .300 Mag Tactical", "Rifle")
  if name.startswith("Compound Bow Orpheus"):
    return ("Koter CB-65", "Bow")
  if name.startswith("Drilling Combination Gun Var"):
    return ("Grelck Drilling Rifle", "Shotgun")
  if name.startswith("Glock 10mm Var"):
    return ("10mm Davani", "Handgun")
  if name.startswith("HOUYI Longbow"):
    return ("Houyi Recurve Bow", "Bow")
  if name.startswith("M1 Garand 3006 Semi Automatic"):
    return ("M1 Iwaniec", "Rifle")
  if name.startswith("Modern Muzzleloader .50 cal"):
    return ("Curman .50 Inline", "Rifle")
  if name.startswith("Modern takedown recurve bow"):
    return ("Stenberg Takedown Recurve Bow", "Bow")
  if name.startswith("Mosin Nagant MN1890"):
    return ("Solokhin MN1890", "Rifle")
  if name.startswith("Nepal 577 450 Rifle"):
    return ("Gandhare Rifle", "Rifle")
  if name.startswith("Peacemaker Revolver 45"):
    return (".45 Rolleston", "Handgun")
  if name.startswith("Pistol Thompson"):
    return (".243 R. Cuomo", "Handgun")
  if name.startswith("Traditional Longbow"):
    return ("Alexander Longbow", "Bow")
  if name.startswith("equipment_weapon_ba_rifle_303"):
    return ("F.L. Sporter .303", "Rifle")
  return (name, "")

def open_rtpc(filename: Path) -> RtpcNode:
  with filename.open("rb") as f:
    data = rtpc_from_binary(f)
  root = data.root_node
  return root

def load_weapons() -> list[Weapon]:
  equipment = open_rtpc(mods.APP_DIR_PATH / "org" / FILE)
  weapons_table = equipment.child_table[6].child_table
  weapons = []
  for weapon_data in weapons_table:
    weapon = Weapon(weapon_data)
    existing = next((w for w in weapons if w.name == weapon.name), None)
    if existing:
      existing.magazine_data_offsets.extend(weapon.magazine_data_offsets)
    else:
      weapons.append(weapon)
  weapons.sort(key=lambda weapon: (weapon.type, weapon.name))
  return weapons

def get_option_elements() -> sg.Column:
  weapons = load_weapons()
  weapon_names = [f"{weapon.type}: {weapon.name}" for weapon in weapons]
  ct = sg.T("Weapon:", p=((10,10),(10,10)))
  #ctt = sg.T("(default magazine size shown in parenthesis)", font="_ 12", p=(0,0))
  c = sg.Combo(weapon_names, k="weapon_mag_name", p=(10,10), enable_events=True)
  st = sg.T("Magazine Size:", p=((10,0), (10,0)))
  n = sg.T("This weapon will still reload after each shot. Magazine change is only cosmetic.", k="weapon_mag_note", font="_ 12 italic", text_color="orange", p=((10,10),(10,0)), visible=False)
  s = sg.Slider((1, 99), 1, 1, orientation = "h", k="weapon_mag_size", p=(50,0))
  return sg.Column([[ct, c], [st, n], [s]])

def handle_event(event: str, window: sg.Window, values: dict) -> None:
  if event == "weapon_mag_name":
    weapons = load_weapons()
    selected_weapon = next(w for w in weapons if values["weapon_mag_name"] == f"{w.type}: {w.name}")
    if selected_weapon.magazine_size == 1:
      window["weapon_mag_note"].update(visible=True)
    else:
      window["weapon_mag_note"].update(visible=False)
    window["weapon_mag_size"].update(selected_weapon.magazine_size)

def add_mod(window: sg.Window, values: dict) -> dict:
  weapon_name = values["weapon_mag_name"]
  if not weapon_name:
    return {
      "invalid": "Please select weapon first"
    }
  weapon_mag_size = values["weapon_mag_size"]
  weapons = load_weapons()
  weapon = next(w for w in weapons if values["weapon_mag_name"] == f"{w.type}: {w.name}")
  return {
    "key": f"weapon_magazine_{weapon_name}",
    "invalid": None,
    "options": {
      "weapon_name": weapon.name,
      "weapon_mag_size": int(weapon_mag_size),
      "weapon_mag_offsets": weapon.magazine_data_offsets
    }
  }

def format(options: dict) -> str:
  return f"Increase Magazine: {options['weapon_name']} ({options['weapon_mag_size']})"

def handle_key(mod_key: str) -> bool:
  return mod_key.startswith("weapon_magazine")

def process(options: dict) -> None:
  weapon_mag_size = options["weapon_mag_size"]
  weapon_mag_offsets = options["weapon_mag_offsets"]

  mods.update_file_at_offsets(Path(FILE), weapon_mag_offsets, weapon_mag_size)
