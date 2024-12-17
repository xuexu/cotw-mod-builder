from modbuilder import mods
from pathlib import Path
from deca.ff_rtpc import rtpc_from_binary, RtpcNode
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
    self._get_name(weapon_data)
    self._get_internal_name(weapon_data)
    self._get_weapon_name_and_type()
    magazine = weapon_data.child_table[1].prop_table[2]
    self.magazine_size = magazine.data
    self.magazine_data_offsets = [magazine.data_pos]

  def __repr__(self) -> str:
    return f"{self.name}, {self.internal_names}, {self.display_name}, {self.type}, {self.magazine_size}, {self.magazine_data_offsets}"

  def _get_name(self, weapon_data: RtpcNode) -> None:
    name = None
    # name_pattern = r'^(equipment_weapon_\w+(_\d+)*_\d+)(_name)?(_description)?$'
    name_pattern = r'^equipment_weapon_\w+_\d+$'
    for prop in reversed(weapon_data.prop_table):  # "name" field is usually toward the bottom of the prop table
      if type(prop.data) == bytes:
        data = prop.data.decode("utf-8")
        match = re.match(name_pattern, data)
        if match:
          name = match.group(0)
          break
    self.name = name

  def _get_internal_name(self, weapon_data: RtpcNode) -> None:
    name = ""
    for i in [4,5,6]:
      raw_name = weapon_data.prop_table[i].data
      if type(raw_name) == bytes:
        name = raw_name.decode("utf-8")
        if name == "store_featured":
          name = ""
          continue
        break
    if not name:
      raise ValueError("Unable to parse internal name", weapon_data)
    self.internal_names = [name]

  def _get_weapon_name_and_type(self) -> None:
    display_name, type = mods.map_weapon_name_and_type(self.name)
    self.display_name = display_name
    self.type = type.capitalize()

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
    else:
      weapons.append(weapon)
  weapons.sort(key=lambda weapon: (weapon.type, weapon.display_name))
  return weapons

def get_option_elements() -> sg.Column:
  weapons = load_weapons()
  weapon_names = [f"{weapon.type}: {weapon.display_name}" for weapon in weapons]

  layout = [
    [
      sg.T("Weapon:", p=((10,10),(10,10))),
      sg.Combo(weapon_names, k="weapon_mag_name", p=(10,10), enable_events=True)
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

def handle_event(event: str, window: sg.Window, values: dict) -> None:
  if event == "weapon_mag_name":
    weapons = load_weapons()
    selected_weapon = next(w for w in weapons if values["weapon_mag_name"] == f"{w.type}: {w.display_name}")
    if selected_weapon.magazine_size == 1:
      window["weapon_mag_note"].update(visible=True)
    else:
      window["weapon_mag_note"].update(visible=False)
    if values["auto_select_default_mag_size"]:  # is the box checked?
      window["weapon_mag_size"].update(selected_weapon.magazine_size)

def add_mod(window: sg.Window, values: dict) -> dict:
  weapon_name = values["weapon_mag_name"]
  if not weapon_name:
    return {
      "invalid": "Please select weapon first"
    }
  weapon_mag_size = values["weapon_mag_size"]
  weapons = load_weapons()
  weapon = next(w for w in weapons if values["weapon_mag_name"] == f"{w.type}: {w.display_name}")
  return {
    "key": f"weapon_magazine_{weapon_name}",
    "invalid": None,
    "options": {
      "weapon_name": weapon.name,
      "weapon_display_name": weapon.display_name,
      "weapon_mag_size": int(weapon_mag_size),
    }
  }

def format(options: dict) -> str:
  if "weapon_display_name" in options:
    return f"Increase Magazine: {options['weapon_display_name']} ({options['weapon_mag_size']})"
  else:  # safely handle old save files without display name
    return f"Increase Magazine: {options['weapon_name']} ({options['weapon_mag_size']})"

def handle_key(mod_key: str) -> bool:
  return mod_key.startswith("weapon_magazine")

def process(options: dict) -> None:
  weapons = load_weapons()
  selected_weapon = next(w for w in weapons if w.name == options["name"])
  if selected_weapon:
    mods.update_file_at_offsets(Path(FILE), selected_weapon.magazine_data_offsets, options["weapon_mag_size"])

UPDATE_VERSION = "2.2.0"
def handle_update(mod_key: str, mod_options: dict, _version: str) -> dict:
  weapons = load_weapons()
  # 2.1.3 to 2.1.9 used on a formatted name which we now store in `name_map.yaml`
  # The .44 Panther Magnum was erroneously named just ".44 Magnum". Catch and fix that
  if mod_options["weapon_name"] == ".44 Magnum":
    mod_options["weapon_name"] = ".44 Panther Magnum"
  selected_weapon = next((w for w in weapons if w.display_name == mod_options["weapon_name"]), None)
  if selected_weapon is None:
    # pre-2.1.3 used an raw internal weapon name found in `equipment_data.bin`
    selected_weapon = next((w for w in weapons if mod_options["weapon_name"] in w.internal_names), None)
  if selected_weapon is None:  # if we didn't find a match yet then raise an error
    raise ValueError(f"Unable to match weapon \"{mod_options['weapon_name']}\"")
  updated_mod_key = f"weapon_magazine_{selected_weapon.name}"
  updated_mod_options = {}
  updated_mod_options["weapon_name"] = selected_weapon.name
  updated_mod_options["weapon_display_name"] = selected_weapon.display_name
  updated_mod_options["weapon_mag_size"] = mod_options["weapon_mag_size"]
  return updated_mod_key, updated_mod_options

