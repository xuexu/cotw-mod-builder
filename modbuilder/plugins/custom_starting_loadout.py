import FreeSimpleGUI as sg

from modbuilder import mods, mods2

try:  # running normally (source)
  from modbuilder.plugins import modify_store
except ModuleNotFoundError:  # running as an exe (PyInstaller)
  from plugins import modify_store


DEBUG = False
NAME = "Custom Starting Loadout"
DESCRIPTION = (
  "Build a customized loadout of weapons and equipment that are provided to a new character. All items are placed in the inventory with an option to assign them directly to the weapon wheel."
  "\nThis is not a save file editor. It only takes effect after deleting your current save files or pressing New Game on the main menu."
)
WARNING = (
  "Pressing New Game will delete your current progress (unlocks, money, XP, skills/perks, etc). Taxidermied animals and trophies in Lodges should be preserved."
  "\nBack up your save files and proceed at your own risk."
)
FILE = "settings/hp_settings/player_initial_loadout.bin"

SHEET = "weapons"
KEY = "modify_starting_loadout"
NAME_KEY = "starting_loadout_name"
EMPTY_ITEM = "(Empty row)"
NO_SUBITEM = "None"
NO_WHEEL_SLOT = "None"
MIN_ROW = 1
MAX_ROW = 39
ADF_ROW_OFFSET = 1  # row 1 in the ADF sheet contains headers, so user-facing loadout row 1 maps to ADF row 2


class StartingItem:
  __slots__ = ("name", "display_name", "type", "detailed_type", "compatible_weapons", "locked_offset")

  def __init__(
    self,
    name: str,
    display_name: str,
    item_type: str,
    detailed_type: str,
    compatible_weapons: tuple[str, ...],
    locked_offset: int,
  ) -> None:
    self.name = name
    self.display_name = display_name
    self.type = item_type
    self.detailed_type = detailed_type
    self.compatible_weapons = compatible_weapons
    self.locked_offset = locked_offset

  @property
  def is_wearable(self) -> bool:
    return self.type == "misc" and self.detailed_type in ("Clothing", "Upgrade")

  @property
  def supports_quantity(self) -> bool:
    return (
      self.type in ("ammo", "structure")
      or (self.type == "misc" and self.detailed_type == "Consumable")
      or (self.type == "lure" and self.detailed_type in ("Decoy", "Scent"))
    )


class StartingLoadoutRow:
  __slots__ = ("row", "item", "inventory_slot", "units", "subitem_1", "subitem_1_units", "subitem_2", "subitem_2_units")

  def __init__(self, row: int, values: list) -> None:
    self.row = row
    self.item = values[0] if isinstance(values[0], bytes) else None
    self.inventory_slot = int(values[1]) if not isinstance(values[1], (bytes, bool)) else -1
    self.units = int(values[2]) if not isinstance(values[2], (bytes, bool)) else 1
    self.subitem_1 = values[3] if isinstance(values[3], bytes) else None
    self.subitem_1_units = int(values[4]) if not isinstance(values[4], (bytes, bool)) else 1
    self.subitem_2 = values[5] if isinstance(values[5], bytes) else None
    self.subitem_2_units = int(values[6]) if not isinstance(values[6], (bytes, bool)) else 1


def _load_starting_items() -> list[StartingItem]:
  # Reuse the equipment parsing and name_map.yaml matching from Modify Store
  supported_types = ("ammo", "misc", "sight", "optic", "weapon", "structure", "lure")
  items = {}
  for item_type in supported_types:
    for store_item in modify_store.ALL_STORE_ITEMS[item_type]:
      category = mods.title_from_key(item_type)
      display_name = f"{category}: {store_item.display_name}"
      items[store_item.name] = StartingItem(
        store_item.name,
        display_name,
        item_type,
        store_item.detailed_type,
        store_item.compatible_weapons,
        store_item.locked.offset,
      )
  return sorted(items.values(), key=lambda item: (item.type, item.display_name, item.name))


def _load_default_rows() -> dict[int, StartingLoadoutRow]:
  extracted_adf = mods2.deserialize_adf(FILE, modded=False)
  rows = {}
  for row in range(MIN_ROW, MAX_ROW + 1):
    adf_row = row + ADF_ROW_OFFSET
    values = [
      mods2.XlsxCell(FILE, extracted_adf, {"sheet": SHEET, "coordinates": f"{column}{adf_row}"}).value
      for column in "ABCDEFG"
    ]
    rows[row] = StartingLoadoutRow(row, values)
  return rows


STARTING_ITEMS = _load_starting_items()
ITEM_BY_NAME = {item.name: item for item in STARTING_ITEMS}
ITEM_BY_DISPLAY_NAME = {item.display_name: item for item in STARTING_ITEMS}
DEFAULT_ROWS = _load_default_rows()

ITEMS = STARTING_ITEMS
ITEM_DISPLAY_NAMES = [item.display_name for item in ITEMS]


def _short_attachment_name(item: StartingItem) -> str:
  # The column header already identifies these as ammo or scopes, so omit the redundant outer equipment category
  prefix = "Ammo: " if item.type == "ammo" else "Sight: "
  return item.display_name.removeprefix(prefix)


AMMO_ITEMS = [item for item in ITEMS if item.type == "ammo"]
SCOPE_ITEMS = [item for item in ITEMS if item.type == "sight"]
AMMO_BY_DISPLAY_NAME = {_short_attachment_name(item): item for item in AMMO_ITEMS}
SCOPE_BY_DISPLAY_NAME = {_short_attachment_name(item): item for item in SCOPE_ITEMS}
AMMO_DISPLAY_NAMES = list(AMMO_BY_DISPLAY_NAME)
SCOPE_DISPLAY_NAMES = list(SCOPE_BY_DISPLAY_NAME)


def _compatible_attachment_names(weapon: StartingItem | None, attachments: list[StartingItem]) -> list[str]:
  if weapon is None or weapon.type != "weapon":
    return []
  return [
    _short_attachment_name(attachment)
    for attachment in attachments
    if weapon.name in attachment.compatible_weapons
  ]


def _key(field: str, row: int) -> str:
  return f"starting_loadout_{field}_{row}"


def _item_from_name(name: bytes | str | None) -> StartingItem | None:
  if isinstance(name, bytes):
    name = name.decode("utf-8")
  return ITEM_BY_NAME.get(name) if name else None


def _attachment_display_name(name: bytes | str | None, item_type: str) -> str:
  item = _item_from_name(name)
  if item is None or item.type != item_type:
    return NO_SUBITEM
  return _short_attachment_name(item)


def _default_row_options(row: int) -> dict:
  default = DEFAULT_ROWS[row]
  item = _item_from_name(default.item)
  if item is None:
    return {"item": None}
  return {
    "item": item.name,
    "inventory_slot": default.inventory_slot,
    "units": default.units if item.supports_quantity else 1,
    "subitem_1": _item_from_name(default.subitem_1).name if _item_from_name(default.subitem_1) else None,
    "subitem_1_units": default.subitem_1_units,
    "subitem_2": _item_from_name(default.subitem_2).name if _item_from_name(default.subitem_2) else None,
  }


def _cell(element, width: int) -> sg.Column:
  # Fixed-width cells keep controls aligned with the pixel-sized headers and prevent hidden controls from shifting later columns
  return sg.Column([[element]], size=(width, 38), p=(2, 0), element_justification="left")


def _header(text: str, width: int) -> sg.Column:
  return sg.Column([[sg.T(text, text_color="orange", p=(2, 4))]], size=(width, 34), p=(2, 0))


def _row_elements(row: int) -> list:
  options = _default_row_options(row)
  item = ITEM_BY_NAME.get(options.get("item"))
  is_weapon = item is not None and item.type == "weapon"
  is_wearable = item is not None and item.is_wearable
  supports_quantity = item is not None and item.supports_quantity
  ammo_names = _compatible_attachment_names(item, AMMO_ITEMS)
  scope_names = _compatible_attachment_names(item, SCOPE_ITEMS)
  ammo_value = _attachment_display_name(options.get("subitem_1"), "ammo")
  scope_value = _attachment_display_name(options.get("subitem_2"), "sight")
  ammo_value = ammo_value if ammo_value in ammo_names else NO_SUBITEM
  scope_value = scope_value if scope_value in scope_names else NO_SUBITEM
  slot = options.get("inventory_slot", 0)
  slot_display = NO_WHEEL_SLOT if slot == 0 else slot

  slot_controls = sg.Column([[
    sg.Combo(
      [NO_WHEEL_SLOT] + list(range(1, 11)),
      default_value=slot_display,
      readonly=True,
      visible=bool(item) and not is_wearable,
      k=_key("slot", row),
      size=(7, 11),
    ),
    sg.Checkbox("Equip", default=slot == 0, visible=is_wearable, k=_key("equipped", row), p=(0, 2)),
  ]], p=(0, 0), size=(115, 34))

  quantity = sg.Input(
    str(options.get("units", 1)) if item else "",
    disabled=not supports_quantity,
    visible=bool(item) and not is_wearable,
    k=_key("quantity", row),
    size=5,
  )
  ammo = sg.Combo(
    [NO_SUBITEM] + ammo_names,
    default_value=ammo_value,
    readonly=True,
    visible=is_weapon,
    enable_events=True,
    k=_key("ammo", row),
    size=34,
  )
  ammo_quantity = sg.Input(
    str(options.get("subitem_1_units", 1)),
    disabled=not (is_weapon and options.get("subitem_1")),
    visible=is_weapon,
    k=_key("ammo_quantity", row),
    size=5,
  )
  scope = sg.Combo(
    [NO_SUBITEM] + scope_names,
    default_value=scope_value,
    readonly=True,
    visible=is_weapon,
    k=_key("scope", row),
    size=29,
  )

  return [
    _cell(sg.T(str(row), justification="right", size=3, p=(4, 4)), 42),
    _cell(sg.Combo([EMPTY_ITEM] + ITEM_DISPLAY_NAMES, default_value=item.display_name if item else EMPTY_ITEM, readonly=True, enable_events=True, k=_key("item", row), size=45), 372),
    _cell(slot_controls, 122),
    _cell(quantity, 60),
    _cell(ammo, 282),
    _cell(ammo_quantity, 60),
    _cell(scope, 245),
  ]


def get_option_elements() -> sg.Column:
  layout = [[
    sg.T("Loadout name:", p=((4, 8), (6, 10))),
    sg.Input("", k=NAME_KEY, size=45, p=((0, 0), (6, 10))),
  ], [
    _header("Row", 42),
    _header("Item", 372),
    _header("Wheel Slot", 122),
    _header("Qty", 60),
    _header("Equipped ammo", 282),
    _header("Qty", 60),
    _header("Equipped scope", 245),
  ]]
  layout.extend(_row_elements(row) for row in range(MIN_ROW, MAX_ROW + 1))
  return sg.Column(layout, p=(0, 0))


def _selected_item(display_name: str) -> StartingItem | None:
  return None if display_name == EMPTY_ITEM else ITEM_BY_DISPLAY_NAME.get(display_name)


def _update_row_controls(
  window: sg.Window,
  row: int,
  item: StartingItem | None,
  ammo_display: str = NO_SUBITEM,
  scope_display: str = NO_SUBITEM,
) -> None:
  is_weapon = item is not None and item.type == "weapon"
  is_wearable = item is not None and item.is_wearable
  supports_quantity = item is not None and item.supports_quantity

  window[_key("slot", row)].update(visible=item is not None and not is_wearable)
  window[_key("equipped", row)].update(visible=is_wearable)
  window[_key("quantity", row)].update(visible=item is not None and not is_wearable, disabled=not supports_quantity)
  if item is not None and not supports_quantity:
    window[_key("quantity", row)].update("1")
  ammo_names = _compatible_attachment_names(item, AMMO_ITEMS)
  scope_names = _compatible_attachment_names(item, SCOPE_ITEMS)
  ammo_display = ammo_display if ammo_display in ammo_names else NO_SUBITEM
  scope_display = scope_display if scope_display in scope_names else NO_SUBITEM
  window[_key("ammo", row)].update(values=[NO_SUBITEM] + ammo_names, value=ammo_display)
  window[_key("scope", row)].update(values=[NO_SUBITEM] + scope_names, value=scope_display)
  for field in ("ammo", "ammo_quantity", "scope"):
    window[_key(field, row)].update(visible=is_weapon)
  window[_key("ammo_quantity", row)].update(disabled=not (is_weapon and ammo_display != NO_SUBITEM))
  if not is_weapon:
    window[_key("ammo", row)].update(NO_SUBITEM)
    window[_key("ammo_quantity", row)].update("1")
    window[_key("scope", row)].update(NO_SUBITEM)


def handle_event(event: str, window: sg.Window, values: dict) -> None:
  if not isinstance(event, str):
    return
  item_prefix = "starting_loadout_item_"
  ammo_prefix = "starting_loadout_ammo_"
  if event.startswith(item_prefix):
    row = int(event.removeprefix(item_prefix))
    item = _selected_item(values[event])
    _update_row_controls(
      window,
      row,
      item,
      ammo_display=values.get(_key("ammo", row), NO_SUBITEM),
      scope_display=values.get(_key("scope", row), NO_SUBITEM),
    )
  elif event.startswith(ammo_prefix):
    row = int(event.removeprefix(ammo_prefix))
    has_ammo = values[event] != NO_SUBITEM
    window[_key("ammo_quantity", row)].update(disabled=not has_ammo)
    if not has_ammo:
      window[_key("ammo_quantity", row)].update("1")
  else:
    return
  window["options"].contents_changed()


def _positive_integer(value: str, label: str, row: int) -> tuple[int | None, str | None]:
  try:
    parsed = int(value)
    if parsed < 1:
      raise ValueError
    return parsed, None
  except (TypeError, ValueError):
    return None, f"Loadout row {row}: {label} must be a whole number of at least 1"


def _read_row(values: dict, row: int) -> tuple[dict | None, str | None]:
  item_display = values[_key("item", row)]
  item = _selected_item(item_display)
  if item_display != EMPTY_ITEM and item is None:
    return None, f"Loadout row {row}: please select a valid item"
  if item is None:
    return {"item": None}, None

  if item.is_wearable:
    inventory_slot = 0 if values[_key("equipped", row)] else -1
  else:
    slot = values[_key("slot", row)]
    try:
      inventory_slot = 0 if slot == NO_WHEEL_SLOT else int(slot)
      if not 0 <= inventory_slot <= 10:
        raise ValueError
    except (TypeError, ValueError):
      return None, f"Loadout row {row}: weapon wheel slot must be None or a number from 1 to 10"

  quantity = 1
  if item.supports_quantity:
    quantity, error = _positive_integer(values[_key("quantity", row)], "quantity", row)
    if error:
      return None, error

  ammo = None
  ammo_quantity = 1
  scope = None
  if item.type == "weapon":
    ammo_display = values[_key("ammo", row)]
    ammo = AMMO_BY_DISPLAY_NAME.get(ammo_display) if ammo_display != NO_SUBITEM else None
    if ammo_display != NO_SUBITEM and ammo is None:
      return None, f"Loadout row {row}: please select valid equipped ammo"
    if ammo and item.name not in ammo.compatible_weapons:
      return None, f'Loadout row {row}: "{_short_attachment_name(ammo)}" is not compatible with "{item.display_name}"'
    if ammo:
      ammo_quantity, error = _positive_integer(values[_key("ammo_quantity", row)], "ammo quantity", row)
      if error:
        return None, error

    scope_display = values[_key("scope", row)]
    scope = SCOPE_BY_DISPLAY_NAME.get(scope_display) if scope_display != NO_SUBITEM else None
    if scope_display != NO_SUBITEM and scope is None:
      return None, f"Loadout row {row}: please select a valid equipped scope"
    if scope and item.name not in scope.compatible_weapons:
      return None, f'Loadout row {row}: "{_short_attachment_name(scope)}" is not compatible with "{item.display_name}"'

  return {
    "item": item.name,
    "inventory_slot": inventory_slot,
    "units": quantity,
    "subitem_1": ammo.name if ammo else None,
    "subitem_1_units": ammo_quantity,
    "subitem_2": scope.name if scope else None,
  }, None


def add_mod(window: sg.Window, values: dict) -> dict:
  name = str(values.get(NAME_KEY, "")).strip()
  if not name:
    return {"invalid": "Please enter a loadout name"}
  rows = {}
  for row in range(MIN_ROW, MAX_ROW + 1):
    row_options, error = _read_row(values, row)
    if error:
      return {"invalid": error}
    rows[str(row)] = row_options
  if error := _validate_equipped_wearables(rows):
    return {"invalid": error}
  if error := _validate_attachment_compatibility(rows):
    return {"invalid": error}
  return {"key": KEY, "invalid": None, "options": {"name": name, "rows": rows}}


def _validate_equipped_wearables(rows: dict) -> str | None:
  equipped_outfits = 0
  equipped_backpacks = 0
  for row_options in rows.values():
    if not row_options.get("item") or int(row_options.get("inventory_slot", -1)) != 0:
      continue
    item = ITEM_BY_NAME.get(row_options["item"])
    if item is None or item.type != "misc":
      continue
    if item.detailed_type == "Clothing":
      equipped_outfits += 1
    elif item.detailed_type == "Upgrade":
      equipped_backpacks += 1
  if equipped_outfits != 1:
    return f"Exactly one outfit must be equipped (found {equipped_outfits})"
  if equipped_backpacks > 1:
    return f"A maximum of one backpack can be equipped (found {equipped_backpacks})"
  return None


def _validate_attachment_compatibility(rows: dict) -> str | None:
  attachment_fields = (("subitem_1", "ammo"), ("subitem_2", "sight"))
  for row, row_options in rows.items():
    item_name = row_options.get("item")
    if not item_name:
      continue
    weapon = ITEM_BY_NAME.get(item_name)
    for field, expected_type in attachment_fields:
      attachment_name = row_options.get(field)
      if not attachment_name:
        continue
      attachment = ITEM_BY_NAME.get(attachment_name)
      if weapon is None or weapon.type != "weapon":
        return f"Loadout row {row}: only weapons can have equipped ammo or scopes"
      if attachment is None or attachment.type != expected_type:
        return f"Loadout row {row}: equipped {expected_type} is no longer available"
      if weapon.name not in attachment.compatible_weapons:
        return (
          f'Loadout row {row}: "{_short_attachment_name(attachment)}" '
          f'is not compatible with "{weapon.display_name}"'
        )
  return None


def _unlock_loadout_items(rows: dict) -> None:
  item_names = {
    item_name
    for row_options in rows.values()
    for item_name in (
      row_options.get("item"),
      row_options.get("subitem_1"),
      row_options.get("subitem_2"),
    )
    if item_name
  }
  updates = [
    {"offset": ITEM_BY_NAME[item_name].locked_offset, "value": 1}
    for item_name in sorted(item_names)
    if item_name in ITEM_BY_NAME and ITEM_BY_NAME[item_name].locked_offset > 0
  ]
  if updates:
    mods.apply_updates_to_file(modify_store.EQUIPMENT_FILE, updates)


def load_options(window: sg.Window, options: dict) -> None:
  window[NAME_KEY].update(options.get("name", ""))
  rows = options.get("rows", {})
  for row in range(MIN_ROW, MAX_ROW + 1):
    row_options = rows.get(str(row), rows.get(row, _default_row_options(row)))
    item = ITEM_BY_NAME.get(row_options.get("item")) if row_options.get("item") else None
    window[_key("item", row)].update(item.display_name if item else EMPTY_ITEM)
    slot = int(row_options.get("inventory_slot", 0))
    window[_key("slot", row)].update(NO_WHEEL_SLOT if slot == 0 else slot)
    window[_key("equipped", row)].update(slot == 0)
    window[_key("quantity", row)].update(str(row_options.get("units", 1)) if item else "")
    window[_key("ammo_quantity", row)].update(str(row_options.get("subitem_1_units", 1)))
    _update_row_controls(
      window,
      row,
      item,
      ammo_display=_attachment_display_name(row_options.get("subitem_1"), "ammo"),
      scope_display=_attachment_display_name(row_options.get("subitem_2"), "sight"),
    )
  window["options"].contents_changed()


def handle_key(mod_key: str) -> bool:
  return mod_key == KEY


def format_options(options: dict) -> str:
  populated = sum(bool(row.get("item")) for row in options.get("rows", {}).values())
  name = str(options.get("name", "")).strip()
  if name:
    return f"{NAME}: {name} ({populated} items)"
  return f"{NAME} ({populated} items)"


def get_files(options: dict) -> list[str]:
  return [FILE, modify_store.EQUIPMENT_FILE]


def build_coordinate_updates(options: dict) -> list[dict]:
  row = int(options["row"])
  if not MIN_ROW <= row <= MAX_ROW:
    raise ValueError(f"Loadout row must be between {MIN_ROW} and {MAX_ROW}")
  adf_row = row + ADF_ROW_OFFSET

  if not options.get("item"):
    values = [True] * 7
  else:
    item = ITEM_BY_NAME.get(options["item"])
    is_wearable = item is not None and item.is_wearable
    is_weapon = item is not None and item.type == "weapon"
    if is_wearable:
      equipped = options.get("equipped", int(options["inventory_slot"]) == 0)
      inventory_slot = 0 if equipped else -1
      units = 1
    else:
      inventory_slot = int(options["inventory_slot"])
      units = int(options["units"]) if item is None or item.supports_quantity else 1
    subitem_1 = options.get("subitem_1") if is_weapon else None
    subitem_2 = options.get("subitem_2") if is_weapon else None
    values = [
      options["item"], inventory_slot, units,
      subitem_1 or True, int(options["subitem_1_units"]) if subitem_1 else True,
      subitem_2 or True, 1 if subitem_2 else True,
    ]

  return [
    {
      "sheet": SHEET,
      "coordinates": f"{column}{adf_row}",
      "value": value,
      "allow_new_data": True,
    }
    for column, value in zip("ABCDEFG", values)
  ]


def _complete_rows(options: dict) -> dict[str, dict]:
  rows = options.get("rows", {})
  return {
    str(row): rows.get(str(row), rows.get(row, _default_row_options(row)))
    for row in range(MIN_ROW, MAX_ROW + 1)
  }


def process(options: dict) -> None:
  updates = []
  complete_rows = _complete_rows(options)
  if error := _validate_equipped_wearables(complete_rows):
    raise ValueError(error)
  if error := _validate_attachment_compatibility(complete_rows):
    raise ValueError(error)
  for row in range(MIN_ROW, MAX_ROW + 1):
    row_options = complete_rows[str(row)]
    updates.extend(build_coordinate_updates({"row": row, **row_options}))
  mods2.apply_coordinate_updates_to_file(FILE, updates, allow_new_data=True)


def finalize(options: dict) -> None:
  _unlock_loadout_items(_complete_rows(options))
