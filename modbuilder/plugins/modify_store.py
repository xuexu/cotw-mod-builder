from modbuilder import mods
from deca.ff_rtpc import RtpcNode
import FreeSimpleGUI as sg
import re

DEBUG = False
NAME = "Modify Store"
DESCRIPTION = "Modify prices and quantites of store items or apply bulk changes to an entire category. Individual and bulk changes in the same category can cause unintended results."
EQUIPMENT_FILE = mods.EQUIPMENT_DATA_FILE

class StoreItem:
  __slots__ = (
    'type',
    'name',
    'display_name',
    'detailed_type',
    'internal_name',
    'price',
    'price_offset',
    'quantity',
    'quantity_offset'
  )

  type: str                   # item type
  name: str                   # unique item name for specific item/variant
  display_name: str           # unique display name for specific item/variant
  detailed_type: str          # additional type data (weapon for ammo and Illuminated Iron Sights, category for Misc/Lures)
  internal_name: str          # used to match old naming schemes
  price: int
  price_offset: int
  quantity: int
  quantity_offset: int

  def __init__(self, equipment_node: RtpcNode, equipment_type: str) -> None:
    self.type = equipment_type
    self.internal_name = None
    self.detailed_type = None
    self._parse_prop_table(equipment_node)
    if self.type == "skin":
      self.display_name = self._parse_skin_name()
    if self.type != "skin":
      self._map_equipment_name()
    self._format_display_name()

  def __repr__(self) -> str:
    return f"{self.type}, {self.name} ({self.price}, {self.price_offset}, {self.quantity}, {self.quantity_offset})"

  def _parse_prop_table(self, equipment_node: RtpcNode) -> None:
    self.price = 0
    self.price_offset = None
    self.quantity = 0
    self.quantity_offset = -1  # some items do not have quantity
    for prop in equipment_node.prop_table:
      if (
        self.type == "skin"  # parse texture name to get skin names
        and prop.name_hash == 837395680  # 0x31e9a4e0
      ):
        self.name = prop.data.decode("utf-8")

      if (
        self.type != "skin"  # read "name" value for all other item types
        and prop.name_hash == 3541743236  # 0xd31ab684 - "name"
      ):
        self.name = prop.data.decode("utf-8")

      if prop.name_hash == 588564970:  # 0x2314c9ea - old name pre-2.2.2
        data = prop.data.decode("utf-8")
        if data:
          self.internal_name = data

      if prop.name_hash == 870267695:  # 0x33df3b2f
        self.price = prop.data
        self.price_offset = prop.data_pos

      if self.type in ["ammo", "misc", "lure"]:  # categories with quantity
        if (
          prop.name_hash == 2979948800  # 0xb19e6900
          and prop.data != 4294967295
        ):
          # some items in categories with quantity have no individual quantity (callers in "lures", backpacks in "misc")
          # those items will have a "quantity" of 4294967295 (max 32-bit integer) that we can ignore
          self.quantity = prop.data
          self.quantity_offset = prop.data_pos

  def _parse_skin_name(self) -> None:
    skin_types = {
      "t1": "Paint",
      "t2": "Spray",
      "t3": "Material",
      "t4": "Camo",
      "t5": "Wrap",
    }
    parts = self.name.split("\\")  # parse texture name into something readable
    category = " ".join([x.capitalize() for x in parts[-2].split("_")])
    name = parts[-1].removesuffix("_dif.ddsc")
    if category == "Crosshair Thumbnails":
      category = "Reticle"
      pattern = r'^thumbnail_crosshair_(.*)_(\d\d)$'  # thumbnail_crosshair_mill_dot_01
      matches = re.match(pattern, name)
      display_name = f"Reticle: {" ".join([x.capitalize() for x in matches.group(1).split("_")])} {matches.group(2)}"
    else:
      pattern = r'(t\d)_(\d\d)$'  # camo_h2_lunar_new_year_1_t3_01 >> "Material 01"
      matches = re.search(pattern, name)
      display_name = f"{category}: {skin_types[matches.group(1)]} {matches.group(2)}"
    return display_name

  def _map_equipment_name(self) -> None:
    if (mapped_equipment := mods.map_equipment(self.name, self.type)):
      self.detailed_type = mapped_equipment.get("type", "")
      self.display_name = mods.format_variant_name(mapped_equipment)
    else:
      self.detailed_type = ""
      self.display_name = self.name

  def _format_display_name(self) -> None:
    detailed_type = self.detailed_type if self.detailed_type else ""
    if self.type in ["ammo", "misc", "weapon"]:
      self.display_name = f"{detailed_type}: {self.display_name}"
    if self.type == "sight":
      if self.display_name == "Illuminated Iron Sights":
        self.display_name = f"{self.display_name}: {detailed_type}"
    if self.type == "lure":
      self.display_name = f"{detailed_type}: {self.display_name.replace(" Decoy","").replace(" Caller","").replace(" Scent","")}"

def load_equipment_data(
    equipment_nodes: list[RtpcNode],
    equipment_type: str,
  ) -> list[StoreItem]:
  loaded_items = []
  for equipment_node in equipment_nodes:
    loaded_item = StoreItem(equipment_node, equipment_type)
    if (  # skip some invalid items
      (equipment_type == "optic" and loaded_item.name == "equipment_optics_camera_01")  # in-game "camera" item
      or (equipment_type == "weapon" and loaded_item.name == "equipment_weapon_clay_pigeon_01")  # Salzwiesen shooting range launcher
      or (equipment_type == "ammo" and loaded_item.name == "equipment_ammo_clay_pigeon_01")  # Salzwiesen shooting range ammo
    ):
      continue
    loaded_items.append(loaded_item)
  return sorted(loaded_items, key=lambda x: x.display_name)

def load_store_items() -> dict[str, list[StoreItem]]:
  equipment = mods.open_rtpc(mods.APP_DIR_PATH / "org" / EQUIPMENT_FILE)
  store_items = {}

  store_items["ammo"] = load_equipment_data(equipment.child_table[0].child_table, "ammo")
  store_items["misc"] = load_equipment_data( equipment.child_table[1].child_table, "misc")
  store_items["sight"] = load_equipment_data(equipment.child_table[2].child_table, "sight")
  store_items["optic"] = load_equipment_data(equipment.child_table[3].child_table, "optic")
  # store_items["vehicle"] = load_equipment_data(equipment.child_table[4].child_table, "vehicle")  # free with DLC, $20000 without (multiplayer only). Where is this value?
  store_items["skin"] = load_equipment_data(equipment.child_table[5].child_table, "skin")
  store_items["weapon"] = load_equipment_data(equipment.child_table[6].child_table, "weapon")
  store_items["structure"] = load_equipment_data(equipment.child_table[7].child_table, "structure")
  store_items["lure"] = load_equipment_data(equipment.child_table[8].child_table, "lure")
  # print("Loaded store items")
  return store_items

def build_tab(item_type: str) -> sg.Tab:
  item_list = ALL_STORE_ITEMS[item_type]
  return sg.Tab(item_type.capitalize(), [
    [sg.Combo([item.display_name for item in item_list], metadata=item_list, size=30, key=f"store_list_{item_type}", enable_events=True, expand_x=True)]
  ], key=f"store_tab_{item_type}")

def get_option_elements() -> sg.Column:
  layout = [[
      sg.TabGroup([[
        build_tab(key) for key in ALL_STORE_ITEMS
      ]], k="store_tab_group", enable_events=True),
      sg.Button("Add Category Modification", k="add_mod_group_store", button_color=f"{sg.theme_element_text_color()} on brown", p=((30,0),(30,0))),
    ],
    [sg.Column([
        [
          sg.T("Individual:", p=((10,0),(10,0)), text_color="orange"),
          sg.Checkbox("Auto-update price and quantity", font="_ 12", default=True, k="store_update_price_quantity", enable_events=True, p=((15,0),(10,0))),
        ],
        [sg.T("Price:", p=((30,0),(10,0))), sg.Input("", size=10, p=((34,0),(10,0)), k="store_item_price")],
        [sg.T("Quantity:", p=((30,0),(10,0)), k="store_item_quantity_label"), sg.Input("", size=10, p=((10,0),(10,0)), k="store_item_quantity")],
      ], p=(0,0), element_justification='left', vertical_alignment='top'),
      sg.Column([
        [sg.T("Bulk:", p=((0,0),(10,0)), text_color="orange"), sg.T('(use "Add Category Modification" to apply changes to all items in this category)', font="_ 12 italic", p=((0,0),(10,0)))],
        [sg.T("Category Discount Percent:", p=((20,0),(10,0))), sg.Slider((0,100), 0, 1, orientation="h", p=((10,0),(0,0)), k="store_bulk_discount")],
        [
          sg.T("Free to Price:", p=((20,0),(10,0))),
          sg.Input("0", size=10, p=((10,0),(10,0)), k="store_bulk_free_price"),
          sg.T('Set a price for "free" DLC / mission items in this category', font="_ 12 italic", text_color="orange", p=((10,10),(10,0)))
        ],
        [sg.T("Category Quantity:", p=((20,0),(12,0)), k="store_bulk_quantity_label"), sg.Input("", size=10, p=((10,0),(12,0)), k="store_bulk_quantity")],
      ], p=((190,0),(0,0)), element_justification='left', vertical_alignment='top'),
    ],
  ]
  return sg.Column(layout)

def get_selected_category(window: sg.Window) -> str:
  active_tab = str(window["store_tab_group"].find_currently_active_tab_key()).lower()
  return active_tab.removeprefix("store_tab_")

def get_selected_item(window: sg.Window, values: dict) -> StoreItem:
  item_type = get_selected_category(window)
  item_list = f"store_list_{item_type}"
  item_name = values.get(item_list)
  if item_name:
    try:
      ammo_index = window[item_list].Values.index(item_name)
      return window[item_list].metadata[ammo_index]
    except ValueError as _e:  # user typed/edited data in box and we cannot match
      pass
  return None

def handle_event(event: str, window: sg.Window, values: dict) -> None:
  if event.startswith("store_"):
    item_type = get_selected_category(window)
    selected_item = get_selected_item(window, values)
    if values["store_update_price_quantity"]:  # box checked = update values
      if selected_item:
        window["store_item_price"].update(selected_item.price)
        window["store_item_quantity"].update(selected_item.quantity)
      else:
        window["store_item_price"].update("")
        window["store_item_quantity"].update("")
    if event.startswith("store_tab_"):
      disabled = bool(item_type not in ["ammo", "misc", "lure"])  # disable for categories without quantity
      if not disabled and selected_item:
        disabled = selected_item.quantity == 0  # disable for items with 0 quantity
      window["store_item_quantity"].update(disabled=disabled)
      window["store_bulk_quantity"].update(disabled=disabled)

def add_mod(window: sg.Window, values: dict) -> dict:
  selected_item = get_selected_item(window, values)
  if not selected_item:
    return {
      "invalid": "Please select an item first"
    }
  item_price = values[f"store_item_price"]
  if item_price.isdigit():
    item_price = int(item_price)
  else:
    return {
      "invalid": "Provide a valid item price"
    }
  item_quantity = values[f"store_item_quantity"]
  if item_quantity.isdigit():
    item_quantity = int(item_quantity)
  else:
    return {
      "invalid": "Provide a valid item quantity"
    }

  return {
    "key": f"modify_store_{selected_item.name}",
    "invalid": None,
    "options": {
      "type": selected_item.type,
      "name": selected_item.name,
      "display_name": selected_item.display_name,
      "file": EQUIPMENT_FILE,
      "price": item_price,
      "quantity": item_quantity
    }
  }

def add_mod_group(window: sg.Window, values: dict) -> dict:
  bulk_discount = int(values[f"store_bulk_discount"])

  bulk_free_price = values[f"store_bulk_free_price"]
  if bulk_free_price.isdigit():
    bulk_free_price = int(bulk_free_price)
  else:
    return {
      "invalid": "Provide a valid bulk free price"
    }

  if window["store_bulk_quantity"].Disabled or not values["store_bulk_quantity"]:
    values[f"store_bulk_quantity"] = "0"
  bulk_quantity = values[f"store_bulk_quantity"]
  if bulk_quantity.isdigit():
    bulk_quantity = int(bulk_quantity)
  else:
    return {
      "invalid": "Provide a valid bulk quantity"
    }

  item_type = get_selected_category(window)
  return {
    "key": f"modify_store_{item_type}",
    "invalid": None,
    "options": {
      "type": item_type,
      "file": EQUIPMENT_FILE,
      "discount": bulk_discount,
      "free_price": bulk_free_price,
      "bulk_quantity": bulk_quantity
    }
  }

def format(options: dict) -> str:
  details = []
  if "free_price" in options:  # category - some pre-2.1.0 version didn't have "bulk_quantity"
    details.append(f"-{options['discount']}% discount")
    if options['free_price'] > 0:
      details.append(f"free > {options['free_price']}")
    bulk_quantity = options.get("bulk_quantity", 0)
    if bulk_quantity > 0:
      details.append(f"{bulk_quantity} quantity")
    return f"Modify Store Category: {options['type'].capitalize()} ({' ,'.join(details)})"
  else:  # single item
    display_name = options.get("display_name", options["name"])  # diplay_name added in 2.2.2
    selected_item = match_old_item(options)  # try to match options to a StoreItem
    if selected_item:
      display_name = selected_item.display_name
    details.append(f"${options["price"]}")
    if options["quantity"]:
      details.append(f"{options["quantity"]} quantity")
    return f"Modify Store: {options['type'].capitalize()} - {display_name} ({' ,'.join(details)})"

def handle_key(mod_key: str) -> bool:
  return mod_key.startswith("modify_store")

def get_files(options: dict) -> list[str]:
  return [EQUIPMENT_FILE]

def process(options: dict) -> None:
  updates = []
  item_list = ALL_STORE_ITEMS[options["type"]]

  if "quantity" in options:  # single item
    selected_item = next((i for i in item_list if i.name == options["name"]), None)
    if selected_item:
      updates.append({"offset": selected_item.price_offset, "value": options["price"]})
      if options["quantity"] > 0 and selected_item.quantity_offset > 0:
        updates.append({"offset": selected_item.quantity_offset, "value": options["quantity"]})

  if "bulk_quantity" in options:  # category
    discount = options["discount"]
    free_price = options["free_price"]
    bulk_quantity = options["bulk_quantity"]
    for item in item_list:
      if discount > 0:
        updates.append({"offset": item.price_offset, "value": 1 - discount / 100, "transform": "multiply"})
      if free_price > 0:
        updates.append({"offset": item.price_offset, "value": free_price})
      if bulk_quantity > 0 and item.quantity_offset > 0:
        updates.append({"offset": item.quantity_offset, "value": bulk_quantity})

  mods.apply_updates_to_file(EQUIPMENT_FILE, updates)

def match_old_item(options: dict) -> StoreItem:
  selected_item = None
  # Try to match the old name format. This doesn't work in a few cases where names are not unique
  unmatchable_names = (
    "unknown",
    "trailscout mini daypack",  # small backpack - incorrect color names in save file
    "exoadventurer 32 light daypack",  # medium backpack - incorrect color names in save file
    "summit explorer 6000 pack",  # large backpack - incorrect color names in save file
    "illuminated iron sights",  # does not include associated weapon name
    "store_featured",  # Bolt Action Rifle Pack weapons
    "placeable",  # "placeable decoy" and "placeable" structures are non-unique
    "eurasian teal  decoy",  # strange duplicate "drake" names on both male + female duck decoys
    "eurasian teal decoy",  # including decoys labeled "eurasian teal" that are not eurasian teal decoys
  )
  if not options["name"].lower().startswith(unmatchable_names):
    cleaned_name = re.sub(r"\s*\(id: \d+\)", "", options["name"]).rstrip()  # remove " (id: 12345)"
    selected_item = next((i for i in ALL_STORE_ITEMS[options["type"]] if cleaned_name == i.internal_name), None)
    if not selected_item and options["type"] in ["weapons", "misc"]:
      # some weapons and misc items had special parsing for internal names over 40 characters
      # check against the regex from the old "handle_misc_name()" function
      for item in ALL_STORE_ITEMS[options["type"]]:
        if len(item.internal_name) > 40:
          short_internal_name = re.sub(r'\([\w\s\-\'\./]+\)$', "", item.internal_name).rstrip()
          if cleaned_name == short_internal_name:
            selected_item = item
  # 2.2.1 and prior relied on saved price and quantity offsets
  # This breaks when new items are added to `equipment_data.bin`
  # Try to match on those values. This is less accurate the older the save file is.
  if (
    not selected_item
    and "price_offset" in options
    and "quantity_offset" in options
  ):
    selected_item = next((i for i in ALL_STORE_ITEMS[options["type"]] if (
      options["price_offset"] == i.price_offset
      and options["quantity_offset"] == i.quantity_offset
    )), None)
  return selected_item

def handle_update(mod_key: str, mod_options: dict) -> tuple[str, dict]:
  """
  2.2.2
  - Parse exact prop data from each node for name, price, and quantity (do not save offsets)
  - Use formatted name from 'name_map.yaml' as display_name
  - Attempt to match items from imported save files by old display name or by matching offsets
  """
  if "quantity" in mod_options:  # single item
    selected_item = next((i for i in ALL_STORE_ITEMS[mod_options["type"]] if mod_options["name"] == i.name), None)
    if not selected_item:
      # Try to parse the old item names/offsets to match with a StoreItem object
      selected_item = match_old_item(mod_options)
    if not selected_item:
      raise ValueError(f"Unable to match item \"{mod_options["name"]}\"")

    updated_mod_key = f"modify_store_{selected_item.name}"
    updated_mod_options = {
      "type": selected_item.type,
      "name": selected_item.name,
      "display_name": selected_item.display_name,
      "file": EQUIPMENT_FILE,
      "price": mod_options["price"],
      "quantity": mod_options["quantity"],
    }

  elif "free_price" in mod_options:  # category
    updated_mod_key = f"modify_store_{mod_options["type"]}"
    updated_mod_options = {
      "type": mod_options["type"],
      "file": EQUIPMENT_FILE,
      "discount": mod_options["discount"],
      "free_price": mod_options["free_price"],
      "bulk_quantity":mod_options.get("bulk_quantity", 0)  # some pre-2.1.0 version didn't have "bulk_quantity"
    }

  else:
    raise ValueError(f"Unable to parse config: {mod_options}")
  return updated_mod_key, updated_mod_options

ALL_STORE_ITEMS = load_store_items()
