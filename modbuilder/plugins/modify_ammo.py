import re
from pathlib import Path

import FreeSimpleGUI as sg

from deca.ff_adf import Adf
from modbuilder import mods, mods2

DEBUG = False
NAME = "Modify Ammo"
DESCRIPTION = "Modify ammo attributes. It is easy to over-adjust these settings and create unrealistic ammo. Class changes do not show in the UI but will affect harvest integrity. Changes to a category may conflict with individual ammo changes."

class Ammo:
  __slots__ = (
    'file',
    "name",
    "display_name",
    "type",
    'offsets',
    'classes',
    'ui_data',
  )

  file: str
  name: str
  display_name: str
  type: str
  offsets: dict
  classes: list[int]
  ui_data: dict

  def __init__(self, file: str) -> None:
    self.file = file
    self._parse_name_and_type()
    extracted_adf = mods2.deserialize_adf(mods.get_org_file(file))
    self.offsets = self._get_offsets(extracted_adf)
    self.classes = self._get_classes(extracted_adf)
    self.ui_data = AMMO_UI_DATA.get(self.name)

  def __repr__(self) -> str:
    return f"Name: {self.name}   Display Name: {self.display_name}   Type: {self.type}   Classes: {self.classes}   Offsets: {self.offsets}   File: {self.file}"

  def _parse_name_and_type(self) -> None:
    # example file: editor/entities/hp_weapons/ammunition/bows/equipment_ammo_jp_crossbow_arrow_300gr_01.ammotunec
    split_file = self.file.split("/")
    self.type = split_file[-2].removesuffix("s")
    filename = split_file[-1].removesuffix(".ammotunec")
    if (mapped_eqipment := mods.map_equipment(filename, "ammo")):
      self.name = mapped_eqipment["map_name"]
      self.display_name = mapped_eqipment["name"]
    else:
      self.name = filename
      self.display_name = self.name

  def _get_offsets(self, extracted_adf: Adf) -> dict:
    ammo_data = extracted_adf.table_instance_full_values[0].value
    offsets = {}
    if ammo_data["ammunition_class"].data_offset == ammo_data["ammunition_class"].info_offset:
      # ammo has no classes array - set offsets to add data in the correct position
      offsets["classes"] = extracted_adf.table_instance[0].offset + extracted_adf.table_instance[0].size - 4
    else:
      offsets["classes"] = ammo_data["ammunition_class"].data_offset
    offsets["classes_info"] = ammo_data["ammunition_class"].info_offset
    offsets["classes_length"] = offsets["classes_info"] + 8
    offsets["kinetic_energy"] = ammo_data["kinetic_energy"].data_offset
    offsets["mass"] = ammo_data["mass"].data_offset
    offsets["penetration"] = ammo_data["projectile_penetration"].data_offset
    offsets["damage"] = ammo_data["projectile_damage"].data_offset
    offsets["expansion"] = ammo_data["projectile_expansion_rate"].data_offset
    offsets["contraction"] = ammo_data["projectile_contraction_rate"].data_offset
    offsets["max_expansion"] = ammo_data["projectile_max_expansion"].data_offset
    offsets["projectiles"] = ammo_data["projectiles_per_shot"].data_offset
    return offsets

  def _get_classes(self, extracted_adf: Adf) -> list[int]:
    # There are "placeholder" ammos in the game files that are not available in game and do not have Class data
    # This will return a blank classes list. Examples include:
    #  - .410 Slug for the Mangiafico 410/45 Colt handgun
    #  - 7.62x54R Full Metal Jacket for the Solokhin MN1890
    #  - 28 Gauge bird and buckshot for an unreleased shotgun
    ammo_data = extracted_adf.table_instance_full_values[0].value
    return [ammo_class.value["level"].value for ammo_class in ammo_data["ammunition_class"].value]

def load_ammo_type(ammo_type: str) -> list[Ammo]:
  root_path = mods.APP_DIR_PATH / "org/editor/entities/hp_weapons/ammunition"
  name_pattern = re.compile(r'^equipment_ammo_(\w+)_\d+\.ammotunec$')
  ammo_list = []
  for file in (root_path / ammo_type).glob("*.ammotunec"):
    name_match = name_pattern.match(file.name)
    if name_match:
      relative_file = mods.get_relative_path(file)
      ammo = Ammo(relative_file)
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

def load_ammo_ui_data() -> dict:
  ammo_sheet, _i = mods2.get_sheet(mods.EQUIPMENT_UI_DATA, "ammo")
  ammo_ui_data = {}
  for i in range(2,ammo_sheet["Rows"].value + 1): # skip header row
    name_cell = mods2.XlsxCell(mods.EQUIPMENT_UI_FILE, mods.EQUIPMENT_UI_DATA, {"sheet": "ammo", "coordinates": f"A{i}"})
    penetration_cell = mods2.XlsxCell(mods.EQUIPMENT_UI_FILE, mods.EQUIPMENT_UI_DATA, {"sheet": "ammo", "coordinates": f"C{i}"})
    expansion_cell = mods2.XlsxCell(mods.EQUIPMENT_UI_FILE, mods.EQUIPMENT_UI_DATA, {"sheet": "ammo", "coordinates": f"D{i}"})
    if name_cell.data_array_name == "StringData":  # file contains "blank" rows with True values as placeholders
      ammo_name = mods.clean_equipment_name(name_cell.value.decode("utf-8"), "ammo")
      ammo_ui_data[ammo_name] = {"row": i, "penetration": penetration_cell.value, "expansion": expansion_cell.value}
  return ammo_ui_data

def build_tab(ammo_type: str) -> sg.Tab:
  ammo_list = ALL_AMMO[ammo_type]
  return sg.Tab(ammo_type.capitalize(), [
    [sg.Combo([ammo.display_name for ammo in ammo_list], metadata=ammo_list, size=30, k=f"modify_ammo_list_{ammo_type}", enable_events=True)]
  ], k=f"modify_ammo_tab_{ammo_type}")

def get_option_elements() -> sg.Column:
  buttons_row = [sg.Button(str(i), k=f"modify_ammo_class_button_{i}", enable_events=True,) for i in range(1, 10)]

  layout = [[
      sg.TabGroup([[
        build_tab(key) for key in ALL_AMMO
        ]], k="modify_ammo_tab_group", enable_events=True),
      sg.Column([[
          sg.Text("Classes", justification="left"),
          sg.Checkbox("Auto-select ammo defaults", font="_ 12", default=True, k="modify_ammo_update_default_classes", enable_events=True, p=((25,0),(0,0)))
        ],
        buttons_row,
      ], p=((20,0),(0,0)), vertical_alignment='top'),
      sg.Column([
        [sg.Checkbox("Apply class selection to category", default=False, font="_ 12", k="modify_ammo_category_classes", p=((0,0),(0,0)))],
        [sg.Button("Add Category Modification", k="add_mod_group_ammo", button_color=f"{sg.theme_element_text_color()} on brown", p=((5,0),(5,0)))],
      ], p=((20,0),(0,0))),
      sg.Column([
            [sg.T( " No UI data for ammo ", text_color="firebrick1", background_color="black", k="modify_ammo_ui_error", visible=False, p=((0,0),(0,0)))],
        ], p=((20,0),(0,0))),
    ],
    [sg.Column([
        [sg.Text("Increase Penetration Percent:", p=((0,10),(18,4)))],
        [sg.Text("Increase Expansion Percent:", p=((0,10),(18,4)))],
        [sg.Text("Increase Damage Percent:", p=((0,10),(18,4)))],
        [sg.Text("Increase Kinetic Energy Percent:", p=((0,10),(18,4)))],
        [sg.Text("Increase Mass Percent:", p=((0,10),(18,4)))],
        [sg.Text("Increase Projectile Number:", k="modify_ammo_projectiles_label", p=((0,10),(18,4)), visible=False)]
      ], p=(10,0), element_justification='left', vertical_alignment='top'),
      sg.Column([
        [sg.Slider((0, 100), 0, 2, orientation="h", k="modify_ammo_penetration", s=(50,15))],
        [sg.Slider((0, 200), 0, 2, orientation="h", k="modify_ammo_expansion", s=(50,15))],
        [sg.Slider((0, 200), 0, 2, orientation="h", k="modify_ammo_damage", s=(50,15))],
        [sg.Slider((0, 200), 0, 2, orientation="h", k="modify_ammo_kinetic_energy", s=(50,15))],
        [sg.Slider((0, 200), 0, 2, orientation="h", k="modify_ammo_mass", s=(50,15))],
        [sg.Slider((0, 100), 0, 2, orientation="h", k="modify_ammo_projectiles", s=(50,15), visible=False)]
      ], p=(0,10), element_justification='left', vertical_alignment='top')
    ]
  ]

  return sg.Column(layout)

def get_selected_ammo(window: sg.Window, values: dict) -> Ammo:
  active_tab = str(window["modify_ammo_tab_group"].find_currently_active_tab_key()).lower()
  ammo_type = active_tab.removeprefix("modify_ammo_tab_")
  ammo_list = f"modify_ammo_list_{ammo_type}"
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
  if event.startswith("modify_ammo_list_") or event == "modify_ammo_tab_group" or event == "modify_ammo_update_default_classes":
    active_tab = str(window["modify_ammo_tab_group"].find_currently_active_tab_key()).lower()
    selected_ammo = get_selected_ammo(window, values)
    toggle_ui_error(selected_ammo, window)
    if values["modify_ammo_update_default_classes"]:  # is the box checked?
      if selected_ammo is None:  # no ammo selected = reset class buttons
        reset_ammo_class_buttons()
      else:  # ammo selected = update class buttons to match ammo's default
        for i in range(1,10):
          if i in selected_ammo.classes:
            AMMO_CLASS_BUTTONS_STATE[i - 1] = True
          else:
            AMMO_CLASS_BUTTONS_STATE[i - 1] = False
    # show projectiles options if shotgun tab is selected, hide if non-shotgun tab is selected
    window["modify_ammo_projectiles_label"].update(visible=(active_tab == "modify_ammo_tab_shotgun"))
    window["modify_ammo_projectiles"].update(visible=(active_tab == "modify_ammo_tab_shotgun"))
    window["options"].contents_changed()
  # press a class button = toggle that button
  if event.startswith("modify_ammo_class_button_"):
    selected_class = int(event[-1])
    AMMO_CLASS_BUTTONS_STATE[selected_class - 1] = not AMMO_CLASS_BUTTONS_STATE[selected_class - 1]
  if event.startswith("modify_ammo_"):
    update_ammo_class_buttons(window)

def toggle_ui_error(selected_ammo: Ammo, window: sg.Window) -> None:
  show_error = selected_ammo and not selected_ammo.ui_data
  window["modify_ammo_ui_error"].update(visible=show_error)

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
    "key": f"modify_ammo_{selected_ammo.name}",
    "invalid": None,
    "options": {
      "name": selected_ammo.display_name,
      "type": selected_ammo.type,
      "file": selected_ammo.file,
      "classes": classes,
      "penetration": values["modify_ammo_penetration"],
      "expansion": values["modify_ammo_expansion"],
      "damage": values["modify_ammo_damage"],
      "kinetic_energy": values["modify_ammo_kinetic_energy"],
      "mass": values["modify_ammo_mass"],
      "projectiles": values["modify_ammo_projectiles"] if selected_ammo.type == "shotgun" else 0,
    }
  }

def add_mod_group(window: sg.Window, values: dict) -> dict:
  active_tab = window["modify_ammo_tab_group"].find_currently_active_tab_key().lower()
  ammo_type = active_tab.removeprefix("modify_ammo_tab_")
  if not ammo_type:
    return {
      "invalid": "Please select an ammo type first"
    }
  if values["modify_ammo_category_classes"]:
    classes = format_class_selection()
  else:
    classes = []

  return {
    "key": f"modify_ammo_type_{ammo_type}",
    "invalid": None,
    "options": {
      "type": ammo_type,
      "classes": classes,
      "penetration": values["modify_ammo_penetration"],
      "expansion": values["modify_ammo_expansion"],
      "damage": values["modify_ammo_damage"],
      "kinetic_energy": values["modify_ammo_kinetic_energy"],
      "mass": values["modify_ammo_mass"],
      "projectiles": values["modify_ammo_projectiles"] if ammo_type == "shotgun" else 0,
    }
  }

def format(options: dict) -> str:
  penetration = int(options.get("penetration", 0))
  penetration_text = f'+{penetration}% pen.' if penetration else ""
  expansion = int(options.get("expansion", 0))
  expansion_text = f'+{expansion}% exp.' if expansion else ""
  damage = int(options.get("damage", 0))
  damage_text = f'+{damage}% damage' if damage else ""
  kinetic_energy = int(options.get("kinetic_energy", 0))
  kinetic_energy_text = f'+{kinetic_energy}% energy' if kinetic_energy else ""
  mass = int(options.get("mass", 0))
  mass_text = f'+{mass}% damage' if mass else ""
  projectiles = int(options.get("projectiles", 0))
  projectiles_text = f"+{projectiles} pellets" if options["type"] == "shotgun" and projectiles else ""
  classes = options.get("classes", [])

  stats = [penetration_text, expansion_text, damage_text, kinetic_energy_text, mass_text, projectiles_text]
  stats_text = ", ".join([s for s in stats if s and s.strip()])
  details_text = f'({stats_text if stats_text else "No Stat Changes"})  Classes: {classes if classes else "Default"}'
  if "file" in options:  # single ammo
    ammo_name = options["name"]
    return f"Modify Ammo: {ammo_name} {details_text}"
  else:  # category
    ammo_type = options["type"]
    return f"Modify Ammo Type: {ammo_type.capitalize()} {details_text}"

def handle_key(mod_key: str) -> bool:
  return mod_key.startswith("modify_ammo")

def get_files(options: dict) -> list[str]:
  if "file" in options:
    return [options["file"], mods.EQUIPMENT_UI_FILE]
  else:
    selected_ammo_files = [ammo.file for ammo in ALL_AMMO[options["type"]]]
    return [*selected_ammo_files, mods.EQUIPMENT_UI_FILE]

def get_bundle_file(file: str) -> Path:
  return Path(file).parent / f"{Path(file).name.split('.')[0]}.ee"

def merge_files(files: list[str], options: dict) -> None:
  for file in files:
    if file is not mods.EQUIPMENT_UI_FILE:
      bundle_file = get_bundle_file(file)
      mods.expand_into_archive(file, str(bundle_file))

def update_classes_array(ammo: Ammo, classes: list[int]) -> None:
  updates = []
  if classes:
    # Enforce info/data offsets. This lets us modify "_PLACEHOLDER" ammos that have no class data
    added_offset = ammo.offsets["classes"] - ammo.offsets["classes_info"]
    updates.append({"offset": ammo.offsets["classes_info"], "value": added_offset})
    updates.append({"offset": ammo.offsets["classes_length"], "value": len(classes)})
    # Add class data array
    data_offset = ammo.offsets["classes"]
    classes_array = mods.create_bytearray(classes, "uint08")
    updates.extend(mods.update_array_data(ammo.file, classes_array, data_offset, bytes_to_remove=len(ammo.classes)))
  return updates

def process(options: dict) -> None:
  kinetic_energy = 1 + options["kinetic_energy"] / 100
  penetration = 1 - options["penetration"] / 100
  if penetration == 0:
    penetration = 0.0000001
  damage = 1 + options["damage"] / 100
  expansion_rate = 1 + options["expansion"] / 100
  max_expansion = 1 + options["expansion"] / 100
  mass = 1 + options["mass"] / 100 if "mass" in options else 0
  projectiles = int(options.get("projectiles", 0))
  classes = options.get("classes", [])

  file = options.get("file")
  if file:  # single ammo
    selected_ammos = [Ammo(file)]
  else:  # category
    selected_ammos = ALL_AMMO[options["type"]]

  for ammo in selected_ammos:
    updates = []
    updates.append({"offset": ammo.offsets["kinetic_energy"], "value": kinetic_energy, "transform": "multiply"})
    updates.append({"offset": ammo.offsets["mass"], "value": mass, "transform": "multiply"})
    updates.append({"offset": ammo.offsets["penetration"], "value": penetration, "transform": "multiply"})
    updates.append({"offset": ammo.offsets["damage"], "value": damage, "transform": "multiply"})
    updates.append({"offset": ammo.offsets["expansion"], "value": expansion_rate, "transform": "multiply"})
    updates.append({"offset": ammo.offsets["contraction"], "value": expansion_rate, "transform": "multiply"})
    updates.append({"offset": ammo.offsets["max_expansion"], "value": max_expansion, "transform": "multiply"})
    if ammo.type == "shotgun":
      updates.append({"offset": ammo.offsets["projectiles"], "value": projectiles, "transform":  "add"})
    updates.extend(update_classes_array(ammo, classes))

    if ammo.ui_data:
      ui_penetration = max(min(int(ammo.ui_data["penetration"] * (1 + options["penetration"] / 100)), 100), 1)
      ui_expansion = max(min(int(ammo.ui_data["expansion"] * expansion_rate), 100), 1)
      ui_updates = [
        {
          "coordinates": f"F{ammo.ui_data["row"]}",
          "value": ";".join(map(str,classes))
        },
        {
          "coordinates": f"C{ammo.ui_data["row"]}",
          "value": ui_penetration
        },
        {
          "coordinates": f"D{ammo.ui_data["row"]}",
          "value": ui_expansion
        }
      ]
      for update in ui_updates:
        update["sheet"] = "ammo"
        update["allow_new_data"] = True
      mods2.apply_coordinate_updates_to_file(mods.EQUIPMENT_UI_FILE, ui_updates)
    mods.apply_updates_to_file(ammo.file, updates)

def handle_update(mod_key: str, mod_options: dict) -> tuple[str, dict]:
  """
  2.2.2
  - Replace full filepath with just ammo name in mod_key
  - Separate key for category mods
  2.2.1
  - Use formatted name from 'name_map.yaml' as "display_name"
  """
  # 2.2.0 and prior saved the name with an old format (not from `name_map.yaml`)
  # 2.2.1 saved the full filename in the key
  # Update the config to use the display name and add ammo type
  if "file" in mod_options:  # single ammo
    ammo = Ammo(mod_options["file"])
    updated_mod_key = f"modify_ammo_{ammo.name}"
    updated_mod_options = {
      "name": ammo.display_name,
      "type": ammo.type,
      "file": ammo.file,
      "classes": mod_options.get("classes", []),
    }
  else:  # category
    updated_mod_key = f"modify_ammo_type_{mod_options["type"]}"
    updated_mod_options = {
      "type": mod_options["type"],
      "classes": mod_options.get("classes", []),
    }

  keys_to_copy = ["damage", "penetration", "expansion",
                  "kinetic_energy", "mass", "projectiles"]
  for key in keys_to_copy:
    updated_mod_options[key] = mod_options.get(key, 0)

  return updated_mod_key, updated_mod_options

AMMO_UI_DATA = load_ammo_ui_data()
ALL_AMMO = load_all_ammo()
AMMO_CLASS_BUTTONS_STATE = [True] * 9
