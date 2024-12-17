from modbuilder import mods
from modbuilder.adf_profile import create_u8, read_u32
from modbuilder.widgets import AMMO_CLASS_BUTTONS_STATE
from deca.ff_rtpc import rtpc_from_binary, RtpcNode
from deca.file import ArchiveFile
from deca.ff_adf import Adf
from pathlib import Path
import FreeSimpleGUI as sg
import re, os

DEBUG = False
NAME = "Modify Ammo"
DESCRIPTION = "Modify ammo attributes. It is easy to over-adjust these settings and create unrealistic ammo. Class changes do not show in the UI but will affect harvest integrity."
EQUIPMENT_FILE = "settings/hp_settings/equipment_data.bin"

class Ammo:
  __slots__ = (
    'file', "name", "display_name", "type", 'offsets', 'classes'
  )

  file: str
  name: str
  display_name: str
  type: str
  offsets: dict
  classes: list[int]

  def __init__(self, filepath: Path) -> None:
    self.file = mods.get_relative_path(filepath)
    self._parse_name_and_type(filepath)
    adf = Adf()
    with ArchiveFile(open(filepath, 'rb')) as f:
      adf.deserialize(f)
    ammo_data = adf.table_instance_full_values[0].value
    self.offsets = self._get_offsets(ammo_data)
    self.classes = self._get_classes(ammo_data)

  def _parse_name_and_type(self, filepath: Path) -> None:
    # split_path = self.file.split("/")
    self.type = filepath.parts[-2]
    self.name = filepath.stem  #filename without extension
    self.display_name = mods.map_equipment_name(self.name, "ammo")

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

def format_name(name: str) -> str:
  return " ".join([x.capitalize() for x in name.split("_")])

def load_ammo(root_path: Path, ammo_type: str, name_pattern: re.Pattern) -> list[Ammo]:
  ammo_list = []
  count = 0
  for file in (root_path / ammo_type).glob("*.ammotunec"):
    count += 1
    name_match = name_pattern.match(file.name)
    if name_match:
      ammo = Ammo(file)
      if ammo.classes:  # skip "placeholder" ammos that do not have Class data
        ammo_list.append(ammo)
  ammo_list.sort(key=lambda x: x.display_name)
  return ammo_list

def get_ammo() -> dict:
  root_path = mods.APP_DIR_PATH / "org/editor/entities/hp_weapons/ammunition"
  name_pattern = re.compile(r'^equipment_ammo_(\w+)_\d+\.ammotunec$')

  bow_ammo = load_ammo(root_path, "bows", name_pattern)
  handgun_ammo = load_ammo(root_path, "handguns", name_pattern)
  rifle_ammo = load_ammo(root_path, "rifles", name_pattern)
  shotgun_ammo = load_ammo(root_path, "shotguns", name_pattern)

  return {
    "bow": bow_ammo,
    "handgun": handgun_ammo,
    "rifle": rifle_ammo,
    "shotgun": shotgun_ammo,
  }

def build_tab(ammo_type: str, ammo_list: list[Ammo]) -> sg.Tab:
  return sg.Tab(ammo_type.capitalize(), [
    [sg.Combo([ammo.display_name for ammo in ammo_list], size=30, key=f"ammo_list_{ammo_type}", enable_events=True)]
  ], key=f"ammo_tab_{ammo_type}")

def get_option_elements() -> sg.Column:
  ammo = get_ammo()
  buttons_row = [sg.Button(str(i), k=f"modify_ammo_class_button_{i}", enable_events=True,) for i in range(1, 10)]

  layout = [[
      sg.TabGroup([[
          build_tab("bow", ammo["bow"]),
          build_tab("handgun", ammo["handgun"]),
          build_tab("rifle", ammo["rifle"]),
          build_tab("shotgun", ammo["shotgun"])
        ]], key="ammo_tab_group", enable_events=True),
      sg.Column([[
          sg.Text("Classes", justification="left"),
          sg.Checkbox("Auto-select ammo defaults", font="_12", default=True, k="auto_select_ammo_defaults", enable_events=True, p=((25,0),(0,0)))
        ],
        buttons_row,
      ], p=((30,0),(0,0)), vertical_alignment='top', expand_x=True),
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

def handle_event(event: str, window: sg.Window, values: dict) -> None:
  # select an ammo, swap tabs, or check the box = update displayed data
  if event.startswith("ammo_list_") or event == "ammo_tab_group" or event == "auto_select_ammo_defaults":
    active_tab = window["ammo_tab_group"].find_currently_active_tab_key().lower()
    ammo_type = active_tab.removeprefix("ammo_tab_")
    ammo_name = values.get(f"ammo_list_{ammo_type}")
    if values["auto_select_ammo_defaults"]:  # is the box checked?
      if not ammo_name:  # no ammo selected = reset class buttons
        reset_ammo_class_buttons()
      else:  # ammo selected = update class buttons to match ammo's default
        ammo = get_ammo()
        selected_ammo = next((a for a in ammo[ammo_type] if a.display_name == ammo_name))
        for i in range(1,10):  # class buttons match ammo's default classes
          if i in selected_ammo.classes:
            AMMO_CLASS_BUTTONS_STATE[i - 1] = True
          else:
            AMMO_CLASS_BUTTONS_STATE[i - 1] = False
    # show projectiles options if shotgun ammo is selected, hide if non-shotgun ammo is selected
    window["ammo_projectiles_label"].update(visible=(ammo_type == "shotgun"))
    window["ammo_projectiles"].update(visible=(ammo_type == "shotgun"))
    window["options"].contents_changed()
  # press a class button = toggle that button
  if event.startswith("modify_ammo_class_button_"):
    selected_class = int(event[-1])
    AMMO_CLASS_BUTTONS_STATE[selected_class - 1] = not AMMO_CLASS_BUTTONS_STATE[selected_class - 1]
    #print(AMMO_CLASS_BUTTONS_STATE)
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
  active_tab = window["ammo_tab_group"].find_currently_active_tab_key().lower()
  ammo_type = active_tab.removeprefix("ammo_tab_")
  ammo_name = values.get(f"ammo_list_{ammo_type}")
  if not ammo_name:
    return {
      "invalid": "Please select an ammo first"
    }

  ammo = get_ammo()
  selected_ammo = next((a for a in ammo[ammo_type] if a.display_name == ammo_name))
  file = selected_ammo.file
  ammo_name = selected_ammo.display_name
  kinetic_energy = values["ammo_kinetic_energy"]
  penetration = values["ammo_penetration"]
  expansion = values["ammo_expansion"]
  damage = values["ammo_damage"]
  mass = values["ammo_mass"]
  projectiles = values["ammo_projectiles"] if selected_ammo.type == "shotgun" else 0
  classes = format_class_selection()

  return {
    "key": f"modify_ammo_{file}",
    "invalid": None,
    "options": {
      "name": ammo_name,
      "kinetic_energy": kinetic_energy,
      "penetration": penetration,
      "expansion": expansion,
      "damage": damage,
      "mass": mass,
      "projectiles": projectiles,
      "classes": classes,
      "file": file
    }
  }

def format(options: dict) -> str:
  # editor/entities/hp_weapons/ammunition/bows/equipment_ammo_jp_crossbow_arrow_300gr_01.ammotunec
  # splt file from path and then split filename from extension
  # easier to just ingest the file into an Ammo object?
  name = options["file"].split("/")[-1].split(".")[0]
  ammo_name = mods.map_equipment_name(name, "ammo")
  kinetic_energy = int(options["kinetic_energy"])
  penetration = int(options["penetration"])
  expansion = int(options["expansion"])
  damage = int(options["damage"])
  classes = options["classes"]
  return f"Modify Ammo: {ammo_name} ({kinetic_energy}% energy, {penetration}% penetrate, {expansion}% expand, {damage}% damage) {classes}"

def handle_key(mod_key: str) -> bool:
  return mod_key.startswith("modify_ammo")

def get_files(options: dict) -> list[str]:
  return [options["file"]]

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
  file = options["file"]
  # editor/entities/hp_weapons/ammunition/bows/equipment_ammo_jp_crossbow_arrow_300gr_01.ammotunec
  # parse type from the path and remove "s"
  # easier to just ingest the file into an Ammo object?
  ammo_type = file.split("/")[-2][:-1]
  ammo = get_ammo()
  selected_ammo = next((a for a in ammo[ammo_type] if a.file == file))
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

  mods.update_file_at_offset(file, selected_ammo.offsets["kinetic_energy"], kinetic_energy, "multiply")
  mods.update_file_at_offset(file, selected_ammo.offsets["mass"], mass, "multiply")
  mods.update_file_at_offset(file, selected_ammo.offsets["penetration"], penetration, "multiply")
  mods.update_file_at_offset(file, selected_ammo.offsets["damage"], damage, "multiply")
  mods.update_file_at_offset(file, selected_ammo.offsets["expansion"], expansion_rate, "multiply")
  mods.update_file_at_offset(file, selected_ammo.offsets["contraction"], expansion_rate, "multiply")
  mods.update_file_at_offset(file, selected_ammo.offsets["max_expansion"], max_expansion, "multiply")
  mods.update_file_at_offset(file, selected_ammo.offsets["projectiles"], projectiles, "add")

  if len(classes) > 0:
    header_offset = selected_ammo.offsets["classes_info"]
    data_offset = selected_ammo.offsets["classes"]
    file_data = mods.get_modded_file(file).read_bytes()
    old_array_length = read_u32(file_data[header_offset+8:header_offset+12])
    new_array_length = len(classes)
    mods.insert_array_data(file, create_classes(classes), header_offset, data_offset, array_length=new_array_length, old_array_length=old_array_length)
