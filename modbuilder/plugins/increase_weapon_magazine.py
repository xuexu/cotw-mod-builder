from modbuilder import mods
from pathlib import Path
from deca.ff_rtpc import RtpcNode
import FreeSimpleGUI as sg
import re

DEBUG = False
NAME = "Increase Weapon Magazine"
DESCRIPTION = "Increase the magazine size of weapons. All variants of a selected weapon will be updated."
FILE = "settings/hp_settings/equipment_data.bin"

class Weapon:
  __slots__ = (
    'name', 'internal_names', 'display_name', 'type', 'magazine_size', 'magazine_data_offsets'
  )

  name: str
  internal_names: list[str]  # list so we can merge variants
  display_name: str
  type: str
  magazine_size: int
  magazine_data_offsets: list[int]  # list so we can merge variants

  def __init__(self, weapon_data: RtpcNode) -> None:
    for prop in weapon_data.prop_table:
      if prop.name_hash == 3541743236:  # 0xd31ab684 - "name"
        self.name = prop.data.decode("utf-8")
      if prop.name_hash == 588564970:  # 0x2314c9ea - internal variant display name
        self.internal_names = [prop.data.decode("utf-8")]
    self._get_weapon_name_and_type()
    magazine = weapon_data.child_table[1].prop_table[2]
    self.magazine_size = magazine.data
    self.magazine_data_offsets = [magazine.data_pos]

  def __repr__(self) -> str:
    return f"{self.name}, {self.internal_names}, {self.display_name}, {self.type}, {self.magazine_size}, {self.magazine_data_offsets}"

  def _get_weapon_name_and_type(self) -> None:
    self.name, _variant_key = mods.clean_equipment_name(self.name, "weapon")
    mapped_equipment = mods.map_equipment(self.name, "weapon")
    if mapped_equipment:
      self.display_name = mapped_equipment["name"]
      self.type = mapped_equipment.get("type")
    else:
      self.display_name = self.name
      self.type = ""


def load_weapons() -> list[Weapon]:
  equipment = mods.open_rtpc(mods.APP_DIR_PATH / "org" / FILE)
  weapons_table = equipment.child_table[6].child_table
  weapons = []
  for weapon_data in weapons_table:
    weapon = Weapon(weapon_data)
    existing = next((w for w in weapons if w.display_name == weapon.display_name), None)
    if existing:
      existing.magazine_data_offsets.extend(weapon.magazine_data_offsets)
      existing.internal_names.extend(weapon.internal_names)
    elif weapon.type is not None:  # Skip non-player weapons like Salzwiesen Clay Pigeon Launcher
      weapons.append(weapon)
  weapons.sort(key=lambda weapon: (weapon.type, weapon.display_name))
  # print("Loaded weapons")
  return weapons

def get_option_elements() -> sg.Column:
  weapon_names = [f"{weapon.type}: {weapon.display_name}" for weapon in WEAPON_LIST]

  layout = [
    [
      sg.T("Weapon:", p=((10,10),(10,10))),
      sg.Combo(weapon_names, k="weapon_mag_name", metadata=WEAPON_LIST, p=(10,10), enable_events=True)
    ],
    [
      sg.T("Magazine Size:", p=((10,0), (10,0))),
      sg.Checkbox("Auto-select default magazine size", font="_12", default=True, k="auto_select_default_mag_size", enable_events=True, p=((25,0),(10,0)))
    ],
    [
      sg.Slider((1, 99), 1, 1, orientation = "h", k="weapon_mag_size", p=(50,0))
    ],
    [
      sg.T("This weapon will still reload after each shot. Magazine change is only cosmetic.", k="weapon_mag_note", font="_ 12 italic", text_color="orange", p=((0,10),(0,0)), visible=False)
    ]
  ]
  return sg.Column(layout)

def get_selected_weapon(window: sg.Window, values: dict) -> Weapon:
  weapon_list = window["weapon_mag_name"].metadata
  weapon_type_and_name = values.get("weapon_mag_name")
  if weapon_type_and_name:
    try:
      weapon_index = window["weapon_mag_name"].Values.index(weapon_type_and_name)
      return weapon_list[weapon_index]
    except ValueError as _e:  # user typed/edited data in box and we cannot match
      pass
  return None

def handle_event(event: str, window: sg.Window, values: dict) -> None:
  if event == "weapon_mag_name":
    selected_weapon = get_selected_weapon(window, values)
    if selected_weapon:
      window["weapon_mag_note"].update(visible=(selected_weapon.magazine_size == 1))
      if values["auto_select_default_mag_size"]:  # is the box checked?
        window["weapon_mag_size"].update(selected_weapon.magazine_size)

def add_mod(window: sg.Window, values: dict) -> dict:
  selected_weapon = get_selected_weapon(window, values)
  if not selected_weapon:
    return {
      "invalid": "Please select a weapon first"
    }
  weapon_mag_size = values["weapon_mag_size"]
  return {
    "key": f"weapon_magazine_{selected_weapon.name}",
    "invalid": None,
    "options": {
      "weapon_name": selected_weapon.name,
      "weapon_display_name": selected_weapon.display_name,
      "weapon_mag_size": int(weapon_mag_size),
    }
  }

def format(options: dict) -> str:
 # safely handle old save files without display_name
  display_name = options.get("weapon_display_name", options.get("weapon_name"))
  return f"Increase Magazine: {display_name} ({options["weapon_mag_size"]})"

def handle_key(mod_key: str) -> bool:
  return mod_key.startswith("weapon_magazine")

def process(options: dict) -> None:
  selected_weapon = next((w for w in WEAPON_LIST if w.name == options["weapon_name"]), None)
  if selected_weapon:
    mods.update_file_at_offsets(Path(FILE), selected_weapon.magazine_data_offsets, options["weapon_mag_size"])

def handle_update(mod_key: str, mod_options: dict) -> dict:
  """
  2.2.2
  - Remove variant suffix (_01, _02, etc) from mod_key
  2.2.0
  - Use formatted name from 'name_map.yaml' as "display_name"
  2.1.3
  - Use formatted name instead of parsed internal name
  """
  selected_weapon = None
  # 2.2.2 - match mod key to remove variant suffix
  clean_name, _v = mods.clean_equipment_name(mod_options["weapon_name"], "weapon")
  mapped_equipment = mods.map_equipment(clean_name, "weapon")
  if mapped_equipment:
    selected_weapon = next((w for w in WEAPON_LIST if w.display_name == mapped_equipment["name"]), None)

  # 2.1.3 to 2.1.9 used on a formatted display name which we now store in `name_map.yaml` to combine variants
  if not selected_weapon:
    weapon_name = mod_options.get("weapon_name")
    display_name = mod_options.get("weapon_display_name")
    # Fix a few naming errors
    if weapon_name == ".44 Magnum" or display_name == ".44 Magnum":
        display_name = ".44 Panther Magnum"
    if weapon_name == "7mm Empress/Regent Magnum" or display_name == "7mm Empress/Regent Magnum":
        display_name = "7mm Regent/Empress Magnum"
    if weapon_name == "Viriant .22LR" or display_name == "Viriant .22LR":
        display_name = "Virant .22LR"
    # Match the old name to the new display_name
    selected_weapon = next((w for w in WEAPON_LIST if w.display_name == weapon_name or w.display_name == display_name), None)

  # Pre-2.1.3 used an "internal" weapon name found in `equipment_data.bin` and did not combine variants
  if not selected_weapon:
    selected_weapon = next((w for w in WEAPON_LIST if weapon_name in w.internal_names), None)

  # If we still didn't find a match then return an update error
  if not selected_weapon:
    raise ValueError(f"Unable to match weapon {weapon_name}")

  updated_mod_key = f"weapon_magazine_{selected_weapon.name}"
  updated_mod_options = {}
  updated_mod_options["weapon_name"] = selected_weapon.name
  updated_mod_options["weapon_display_name"] = selected_weapon.display_name
  updated_mod_options["weapon_mag_size"] = mod_options["weapon_mag_size"]
  return updated_mod_key, updated_mod_options

WEAPON_LIST = load_weapons()
