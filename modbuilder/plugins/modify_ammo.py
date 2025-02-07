from modbuilder import mods
from modbuilder.adf_profile import create_u8, read_u32
from deca.file import ArchiveFile
from deca.ff_adf import Adf
from pathlib import Path
import FreeSimpleGUI as sg
import re

DEBUG = False
NAME = "Modify Ammo"
DESCRIPTION = "Modify ammo attributes. It is easy to over-adjust these settings and create unrealistic ammo. Class changes do not show in the UI but will affect harvest integrity. Changes to a category stack with individual ammo changes."
EQUIPMENT_FILE = "settings/hp_settings/equipment_data.bin"

class Ammo:
  __slots__ = (
    'file',
    "name",
    "display_name",
    "type",
    'offsets',
    'classes'
  )

  file: str
  name: str
  display_name: str
  type: str
  offsets: dict
  classes: list[int]

  def __init__(self, file: str) -> None:
    self.file = file
    self._parse_name_and_type()
    adf = Adf()
    with ArchiveFile(open(mods.APP_DIR_PATH / "org" / file, 'rb')) as f:
      adf.deserialize(f)
    ammo_data = adf.table_instance_full_values[0].value
    self.offsets = self._get_offsets(ammo_data)
    self.classes = self._get_classes(ammo_data)

  def __repr__(self) -> str:
    return f"Name: {self.name}   Display Name: {self.display_name}   Type: {self.type}   Classes: {self.classes}   Offsets: {self.offsets}   File: {self.file}"

  def _parse_name_and_type(self) -> None:
    # example file: editor/entities/hp_weapons/ammunition/bows/equipment_ammo_jp_crossbow_arrow_300gr_01.ammotunec
    split_file = self.file.split("/")
    self.type = split_file[-2].removesuffix("s")  # "bow" instead of "bows"
    filename = split_file[-1].removesuffix(".ammotunec")  # filename without "".ammotunec" extension
    self.name, _v = mods.clean_equipment_name(filename, "ammo")
    mapped_eqipment = mods.map_equipment(self.name, "ammo")
    if mapped_eqipment:
      self.display_name = mapped_eqipment["name"]
    else:
      self.display_name = self.name

  def _get_offsets(self, ammo_data) -> dict:
    offsets = {}
    offsets["classes"] = ammo_data["ammunition_class"].data_offset
    offsets["classes_info"] = ammo_data["ammunition_class"].info_offset
    offsets["kinetic_energy"] = ammo_data["kinetic_energy"].data_offset
    offsets["mass"] = ammo_data["mass"].data_offset
    offsets["penetration"] = ammo_data["projectile_penetration"].data_offset
    offsets["damage"] = ammo_data["projectile_damage"].data_offset
    offsets["expansion"] = ammo_data["projectile_expansion_rate"].data_offset
    offsets["contraction"] = ammo_data["projectile_contraction_rate"].data_offset
    offsets["max_expansion"] = ammo_data["projectile_max_expansion"].data_offset
    offsets["projectiles"] = ammo_data["projectiles_per_shot"].data_offset
    return offsets

  def _get_classes(self, ammo_data) -> list[int]:
    # There are "placeholder" ammos in the game files that are not available in game and do not have Class data, such as:
    #  - .410 Slug for the Mangiafico 410/45 Colt handgun
    #  - 28 Gauge bird and buckshot for an unreleased shotgun
    #  - 7.62x54R Full Metal Jacket for the Solokhin MN1890
    # This will return a blank list for "placeholder" ammos. We will skip them in load_ammo()
    return [ammo_class.value["level"].value for ammo_class in ammo_data["ammunition_class"].value]

def load_ammo_type(ammo_type: str) -> list[Ammo]:
  root_path = mods.APP_DIR_PATH / "org/editor/entities/hp_weapons/ammunition"
  name_pattern = re.compile(r'^equipment_ammo_(\w+)_\d+\.ammotunec$')
  ammo_list = []
  count = 0
  for file in (root_path / ammo_type).glob("*.ammotunec"):
    count += 1
    name_match = name_pattern.match(file.name)
    if name_match:
      relative_file = mods.get_relative_path(file)
      ammo = Ammo(relative_file)
      if ammo.classes:  # skip "placeholder" ammos that do not have Class data
        ammo_list.append(ammo)
  ammo_list.sort(key=lambda x: x.display_name)
  return ammo_list

def load_all_ammo() -> dict[str, list[Ammo]]:
  all_ammo = {
      "bow": load_ammo_type("bows"),
      "handgun": load_ammo_type("handguns"),
      "rifle": load_ammo_type("rifles"),
      "shotgun": load_ammo_type("shotguns"),
    }
  # print("Loaded ammo")
  return all_ammo

def build_tab(ammo_type: str) -> sg.Tab:
  ammo_list = ALL_AMMO[ammo_type]
  return sg.Tab(ammo_type.capitalize(), [
    [sg.Combo([ammo.display_name for ammo in ammo_list], metadata=ammo_list, size=30, key=f"ammo_list_{ammo_type}", enable_events=True)]
  ], key=f"ammo_tab_{ammo_type}")

def get_option_elements() -> sg.Column:
  buttons_row = [sg.Button(str(i), k=f"modify_ammo_class_button_{i}", enable_events=True,) for i in range(1, 10)]

  layout = [[
      sg.TabGroup([[
        build_tab(key) for key in ALL_AMMO
        ]], key="ammo_tab_group", enable_events=True),
      sg.Column([[
          sg.Text("Classes", justification="left"),
          sg.Checkbox("Auto-select ammo defaults", font="_12", default=True, k="ammo_update_default_classes", enable_events=True, p=((25,0),(0,0)))
        ],
        buttons_row,
      ], p=((30,0),(0,0)), vertical_alignment='top'),
      sg.Button("Add Category Modification", k="add_mod_group_ammo", button_color=f"{sg.theme_element_text_color()} on brown", p=((30,0),(30,0))),
    ],
    [sg.Column([
        [sg.Text("Increase Kinetic Energy Percent:", p=((0,10),(18,4)))],
        [sg.Text("Increase Penetration Percent:", p=((0,10),(18,4)))],
        [sg.Text("Increase Expansion Percent:", p=((0,10),(18,4)))],
        [sg.Text("Increase Damage Percent:", p=((0,10),(18,4)))],
        [sg.Text("Increase Mass Percent:", p=((0,10),(18,4)))],
        [sg.Text("Increase Projectile Number:", key="ammo_projectiles_label", p=((0,10),(18,4)), visible=False)]
      ], p=(10,0), element_justification='left', vertical_alignment='top'),
      sg.Column([
        [sg.Slider((0, 200), 0, 2, orientation="h", key="ammo_kinetic_energy", s=(50,15))],
        [sg.Slider((0, 100), 0, 2, orientation="h", key="ammo_penetration", s=(50,15))],
        [sg.Slider((0, 200), 0, 2, orientation="h", key="ammo_expansion", s=(50,15))],
        [sg.Slider((0, 200), 0, 2, orientation="h", key="ammo_damage", s=(50,15))],
        [sg.Slider((0, 200), 0, 2, orientation="h", key="ammo_mass", s=(50,15))],
        [sg.Slider((0, 100), 0, 2, orientation="h", key="ammo_projectiles", s=(50,15), visible=False)]
      ], p=(0,10), element_justification='left', vertical_alignment='top')
    ]
  ]

  return sg.Column(layout)

def get_selected_ammo(window: sg.Window, values: dict) -> Ammo:
  active_tab = str(window["ammo_tab_group"].find_currently_active_tab_key()).lower()
  ammo_type = active_tab.removeprefix("ammo_tab_")
  ammo_list = f"ammo_list_{ammo_type}"
  ammo_name = values.get(ammo_list)
  if ammo_name:
    try:
      ammo_index = window[ammo_list].Values.index(ammo_name)
      return window[ammo_list].metadata[ammo_index]
    except ValueError as _e:  # user typed/edited data in box and we cannot match
      pass
  return None

def handle_event(event: str, window: sg.Window, values: dict) -> None:
  # select an ammo, swap tabs, or check the box = update displayed data
  if event.startswith("ammo_list_") or event == "ammo_tab_group" or event == "ammo_update_default_classes":
    active_tab = str(window["ammo_tab_group"].find_currently_active_tab_key()).lower()
    selected_ammo = get_selected_ammo(window, values)
    if values["ammo_update_default_classes"]:  # is the box checked?
      if selected_ammo is None:  # no ammo selected = reset class buttons
        reset_ammo_class_buttons()
      else:  # ammo selected = update class buttons to match ammo's default
        for i in range(1,10):
          if i in selected_ammo.classes:
            AMMO_CLASS_BUTTONS_STATE[i - 1] = True
          else:
            AMMO_CLASS_BUTTONS_STATE[i - 1] = False
    # show projectiles options if shotgun tab is selected, hide if non-shotgun tab is selected
    window["ammo_projectiles_label"].update(visible=(active_tab == "ammo_tab_shotgun"))
    window["ammo_projectiles"].update(visible=(active_tab == "ammo_tab_shotgun"))
    window["options"].contents_changed()
  # press a class button = toggle that button
  if event.startswith("modify_ammo_class_button_"):
    selected_class = int(event[-1])
    AMMO_CLASS_BUTTONS_STATE[selected_class - 1] = not AMMO_CLASS_BUTTONS_STATE[selected_class - 1]
  update_ammo_class_buttons(window)

def reset_ammo_class_buttons() -> None:
  for i in range(9):
    AMMO_CLASS_BUTTONS_STATE[i] = True

def update_ammo_class_buttons(window: sg.Window) -> None:
  for i in range(1,10):
    if AMMO_CLASS_BUTTONS_STATE[i - 1]:
      window[f"modify_ammo_class_button_{i}"].update(button_color=sg.theme_button_color())
    else:
      window[f"modify_ammo_class_button_{i}"].update(button_color=("orange", "black"))

def format_class_selection() -> list[int]:
  # convert the list of True/False values from the buttons into a list of class numbers
  return [index + 1 for index, value in enumerate(AMMO_CLASS_BUTTONS_STATE) if value]

def add_mod(window: sg.Window, values: dict) -> dict:
  selected_ammo = get_selected_ammo(window, values)
  if selected_ammo is None:
    return {
      "invalid": "Please select an ammo first"
    }
  classes = format_class_selection()

  return {
    "key": f"modify_ammo_{selected_ammo.file}",
    "invalid": None,
    "options": {
      "name": selected_ammo.display_name,
      "type": selected_ammo.type,
      "file": selected_ammo.file,
      "kinetic_energy": values["ammo_kinetic_energy"],
      "penetration": values["ammo_penetration"],
      "expansion": values["ammo_expansion"],
      "damage": values["ammo_damage"],
      "mass": values["ammo_mass"],
      "projectiles": values["ammo_projectiles"] if selected_ammo.type == "shotgun" else 0,
      "classes": classes,
    }
  }

def add_mod_group(window: sg.Window, values: dict) -> dict:
  active_tab = window["ammo_tab_group"].find_currently_active_tab_key().lower()
  ammo_type = active_tab.removeprefix("ammo_tab_")
  if not ammo_type:
    return {
      "invalid": "Please select an ammo type first"
    }
  classes = format_class_selection()

  return {
    "key": f"modify_ammo_{ammo_type}",
    "invalid": None,
    "options": {
      "type": ammo_type,
      "kinetic_energy": values["ammo_kinetic_energy"],
      "penetration": values["ammo_penetration"],
      "expansion": values["ammo_expansion"],
      "damage": values["ammo_damage"],
      "mass": values["ammo_mass"],
      "projectiles": values["ammo_projectiles"] if ammo_type == "shotgun" else 0,
      "classes": classes,
    }
  }

def format(options: dict) -> str:
  kinetic_energy = int(options["kinetic_energy"])
  penetration = int(options["penetration"])
  expansion = int(options["expansion"])
  damage = int(options["damage"])
  classes = options["classes"]
  details_text = f"({kinetic_energy}% energy, {penetration}% penetration, {expansion}% expansion, {damage}% damage) {classes}"
  if "name" in options:
    ammo_name = options["name"]
    return f"Modify Ammo: {ammo_name} {details_text}"
  else:
    ammo_type = options["type"]
    return f"Modify Ammo Type: {ammo_type.capitalize()} {details_text}"

def handle_key(mod_key: str) -> bool:
  return mod_key.startswith("modify_ammo")

def get_files(options: dict) -> list[str]:
  if "file" in options:
    return [options["file"]]
  else:
    selected_ammo_files = [ammo.file for ammo in ALL_AMMO[options["type"]]]
    return selected_ammo_files

def get_bundle_file(file: str) -> Path:
  return Path(file).parent / f"{Path(file).name.split('.')[0]}.ee"

def merge_files(files: list[str], options: dict) -> None:
  for file in files:
    bundle_file = get_bundle_file(file)
    mods.expand_into_archive(file, str(bundle_file))

def create_classes(classes: list[int]) -> bytearray:
  result = bytearray()
  for c in classes:
    result += create_u8(c)
  return result

def process(options: dict) -> None:
  kinetic_energy = 1 + options["kinetic_energy"] / 100
  penetration = 1 - options["penetration"] / 100
  if penetration == 0:
    penetration = 0.0000001
  damage = 1 + options["damage"] / 100
  expansion_rate = 1 + options["expansion"] / 100
  max_expansion = 1 + options["expansion"] / 100
  mass = 1 + options["mass"] / 100 if "mass" in options else 0
  projectiles = int(options["projectiles"]) if "projectiles" in options else 0
  classes = options["classes"] if "classes" in options else []

  file = options.get("file")
  if file:  # edit a single ammo
    selected_ammos = [Ammo(file)]
  else:  # edit a whole category
    selected_ammos = ALL_AMMO[options["type"]]

  for ammo in selected_ammos:
    mods.update_file_at_offset(ammo.file, ammo.offsets["kinetic_energy"], kinetic_energy, "multiply")
    mods.update_file_at_offset(ammo.file, ammo.offsets["mass"], mass, "multiply")
    mods.update_file_at_offset(ammo.file, ammo.offsets["penetration"], penetration, "multiply")
    mods.update_file_at_offset(ammo.file, ammo.offsets["damage"], damage, "multiply")
    mods.update_file_at_offset(ammo.file, ammo.offsets["expansion"], expansion_rate, "multiply")
    mods.update_file_at_offset(ammo.file, ammo.offsets["contraction"], expansion_rate, "multiply")
    mods.update_file_at_offset(ammo.file, ammo.offsets["max_expansion"], max_expansion, "multiply")
    mods.update_file_at_offset(ammo.file, ammo.offsets["projectiles"], projectiles, "add")

    if len(classes) > 0:
      header_offset = ammo.offsets["classes_info"]
      data_offset = ammo.offsets["classes"]
      file_data = mods.get_modded_file(ammo.file).read_bytes()
      old_array_length = read_u32(file_data[header_offset+8:header_offset+12])
      new_array_length = len(classes)
      mods.insert_array_data(ammo.file, create_classes(classes), header_offset, data_offset, array_length=new_array_length, old_array_length=old_array_length)

def handle_update(mod_key: str, mod_options: dict) -> dict:
  """
  2.2.2
  - Replace full filepath with just ammo name in mod_key
  2.2.1
  - Use formatted name from 'name_map.yaml' as "display_name"
  """
  # 2.2.0 and prior saved the name with an old format (not from `name_map.yaml`)
  # 2.2.1 saved the full filename in the key
  # Update the config to use the display name and add ammo type
  ammo = Ammo(mod_options["file"])
  updated_mod_key = f"modify_ammo_{ammo.name}"
  updated_mod_options = {
    "name": ammo.display_name,
    "type": ammo.type,
    "file": ammo.file,
    "classes": mod_options["classes"],
    "kinetic_energy": mod_options["kinetic_energy"],
    "penetration": mod_options["penetration"],
    "expansion": mod_options["expansion"],
    "damage": mod_options["damage"],
    "mass": mod_options["mass"],
    "projectiles": mod_options["projectiles"],
  }
  return updated_mod_key, updated_mod_options

ALL_AMMO = load_all_ammo()
AMMO_CLASS_BUTTONS_STATE = [True for i in range(9)]
