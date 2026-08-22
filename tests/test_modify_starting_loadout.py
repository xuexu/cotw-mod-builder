import shutil
import struct
import sys
import tempfile
import types
import unittest
from pathlib import Path
from unittest.mock import Mock, patch


class _GuiStub:
  def __init__(self, *args, **kwargs):
    pass


gui_module = types.ModuleType("FreeSimpleGUI")
gui_module.__getattr__ = lambda _name: _GuiStub
sys.modules.setdefault("FreeSimpleGUI", gui_module)

from modbuilder import mods, mods2
from modbuilder.plugins import \
    custom_starting_loadout as modify_starting_loadout

# Short local aliases keep the test cases focused on behavior.
loadout_data = modify_starting_loadout
loadout_plugin = modify_starting_loadout
modify_starting_items = loadout_data
modify_starting_items_2 = loadout_plugin


class ModifyStartingLoadoutTests(unittest.TestCase):
  def test_attachment_names_omit_redundant_categories(self) -> None:
    self.assertTrue(loadout_plugin.AMMO_DISPLAY_NAMES)
    self.assertTrue(loadout_plugin.SCOPE_DISPLAY_NAMES)
    self.assertTrue(all(not name.startswith("Ammo: ") for name in loadout_plugin.AMMO_DISPLAY_NAMES))
    self.assertTrue(all(not name.startswith("Sight: ") for name in loadout_plugin.SCOPE_DISPLAY_NAMES))

  def test_default_configuration_contains_every_loadout_row(self) -> None:
    rows = {
      str(row): loadout_plugin._default_row_options(row)
      for row in range(loadout_data.MIN_ROW, loadout_data.MAX_ROW + 1)
    }

    self.assertEqual(len(rows), 39)
    self.assertEqual(rows["1"]["item"], "equipment_weapon_ba_rifle_243_01")
    self.assertIsNone(rows["11"]["item"])
    self.assertEqual(loadout_plugin.format_options({"rows": rows}), "Custom Starting Loadout (10 items)")
    self.assertEqual(
      loadout_plugin.format_options({"name": "Rifle Hunter", "rows": rows}),
      "Custom Starting Loadout: Rifle Hunter (10 items)",
    )
    self.assertIsNone(loadout_plugin._validate_equipped_wearables(rows))

  def test_wearable_validation_requires_one_outfit_and_at_most_one_backpack(self) -> None:
    rows = {
      str(row): modify_starting_items_2._default_row_options(row)
      for row in range(modify_starting_items.MIN_ROW, modify_starting_items.MAX_ROW + 1)
    }
    equipped_outfit = next(
      row for row, options in rows.items()
      if options.get("inventory_slot") == 0
      and modify_starting_items_2.ITEM_BY_NAME[options["item"]].detailed_type == "Clothing"
    )
    rows[equipped_outfit]["inventory_slot"] = -1
    self.assertIn("Exactly one outfit", modify_starting_items_2._validate_equipped_wearables(rows))

    second_outfit = next(item for item in modify_starting_items_2.ITEMS if item.detailed_type == "Clothing")
    rows["11"] = {"item": second_outfit.name, "inventory_slot": 0, "units": 1}
    rows["12"] = {"item": second_outfit.name, "inventory_slot": 0, "units": 1}
    self.assertIn("Exactly one outfit", modify_starting_items_2._validate_equipped_wearables(rows))

    rows["12"] = {"item": None}
    backpack = next(item for item in modify_starting_items_2.ITEMS if item.detailed_type == "Upgrade")
    rows["12"] = {"item": backpack.name, "inventory_slot": 0, "units": 1}
    rows["13"] = {"item": backpack.name, "inventory_slot": 0, "units": 1}
    self.assertIn("maximum of one backpack", modify_starting_items_2._validate_equipped_wearables(rows))

  def test_wearable_validation_runs_when_adding_and_building(self) -> None:
    rows = {
      str(row): modify_starting_items_2._default_row_options(row)
      for row in range(modify_starting_items.MIN_ROW, modify_starting_items.MAX_ROW + 1)
    }
    for row_options in rows.values():
      item = modify_starting_items_2.ITEM_BY_NAME.get(row_options.get("item"))
      if item and item.detailed_type == "Clothing":
        row_options["inventory_slot"] = -1

    read_results = [(rows[str(row)], None) for row in range(1, 40)]
    with patch.object(modify_starting_items_2, "_read_row", side_effect=read_results):
      result = modify_starting_items_2.add_mod(None, {modify_starting_items_2.NAME_KEY: "Invalid Outfit Test"})
    self.assertIn("Exactly one outfit", result["invalid"])

    with self.assertRaisesRegex(ValueError, "Exactly one outfit"):
      modify_starting_items_2.process({"rows": rows})

  def test_loadout_name_is_required_when_adding(self) -> None:
    result = modify_starting_items_2.add_mod(None, {modify_starting_items_2.NAME_KEY: "  "})
    self.assertEqual(result["invalid"], "Please enter a loadout name")

  def test_removing_ammo_disables_and_resets_its_quantity(self) -> None:
    ammo_quantity = Mock()
    options_column = Mock()
    window = {
      modify_starting_items_2._key("ammo_quantity", 1): ammo_quantity,
      "options": options_column,
    }
    event = modify_starting_items_2._key("ammo", 1)

    modify_starting_items_2.handle_event(event, window, {event: modify_starting_items_2.NO_SUBITEM})

    ammo_quantity.update.assert_any_call(disabled=True)
    ammo_quantity.update.assert_any_call("1")

  def test_attachment_compatibility_comes_from_equipment_data(self) -> None:
    weapon = loadout_plugin.ITEM_BY_NAME["equipment_weapon_ba_rifle_243_01"]
    compatible_ammo = loadout_plugin.ITEM_BY_NAME["equipment_ammo_243_sp_01"]
    incompatible_ammo = next(
      ammo for ammo in loadout_plugin.AMMO_ITEMS
      if weapon.name not in ammo.compatible_weapons
    )
    compatible_scope = loadout_plugin.ITEM_BY_NAME["equipment_sight_rifle_scope_1-4x_24mm_01"]

    self.assertIn(weapon.name, compatible_ammo.compatible_weapons)
    self.assertIn(weapon.name, compatible_scope.compatible_weapons)
    self.assertNotIn(
      loadout_plugin._short_attachment_name(incompatible_ammo),
      loadout_plugin._compatible_attachment_names(weapon, loadout_plugin.AMMO_ITEMS),
    )

  def test_attachment_compatibility_is_validated_during_build(self) -> None:
    rows = {
      str(row): loadout_plugin._default_row_options(row)
      for row in range(loadout_plugin.MIN_ROW, loadout_plugin.MAX_ROW + 1)
    }
    weapon = loadout_plugin.ITEM_BY_NAME["equipment_weapon_ba_rifle_243_01"]
    incompatible_ammo = next(
      ammo for ammo in loadout_plugin.AMMO_ITEMS
      if weapon.name not in ammo.compatible_weapons
    )
    rows["1"]["subitem_1"] = incompatible_ammo.name

    error = loadout_plugin._validate_attachment_compatibility(rows)

    self.assertIn("is not compatible", error)

  def test_loadout_items_are_unlocked_in_equipment_data(self) -> None:
    rows = {
      "1": {
        "item": "equipment_weapon_ba_rifle_243_01",
        "subitem_1": "equipment_ammo_243_sp_01",
        "subitem_2": "equipment_sight_rifle_scope_1-4x_24mm_01",
      }
    }

    with patch.object(loadout_plugin.mods, "apply_updates_to_file") as apply_updates:
      loadout_plugin._unlock_loadout_items(rows)

    filename, updates = apply_updates.call_args.args
    self.assertEqual(filename, loadout_plugin.modify_store.EQUIPMENT_FILE)
    self.assertEqual(len(updates), 3)
    self.assertTrue(all(update["value"] == 1 and update["offset"] > 0 for update in updates))
    self.assertEqual(
      loadout_plugin.get_files({}),
      [loadout_plugin.FILE, loadout_plugin.modify_store.EQUIPMENT_FILE],
    )

  def test_finalize_unlocks_items_after_normal_processing(self) -> None:
    rows = {
      str(row): loadout_plugin._default_row_options(row)
      for row in range(loadout_plugin.MIN_ROW, loadout_plugin.MAX_ROW + 1)
    }

    with patch.object(loadout_plugin, "_unlock_loadout_items") as unlock_items:
      loadout_plugin.finalize({"rows": rows})

    unlock_items.assert_called_once_with(rows)

  def _assert_loadout_finalize_overrides_store_lock(self, store_options: dict, store_lock: int) -> None:
    weapon = loadout_plugin.modify_store.ALL_STORE_ITEMS["weapon"][0]
    rows = {"1": {"item": weapon.name}}
    original_mod_path = mods.MOD_PATH

    with tempfile.TemporaryDirectory() as temp_dir:
      try:
        mods.MOD_PATH = Path(temp_dir)
        source = mods.get_org_file(loadout_plugin.modify_store.EQUIPMENT_FILE)
        destination = mods.get_modded_file(loadout_plugin.modify_store.EQUIPMENT_FILE)
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, destination)

        loadout_plugin.modify_store.process(store_options)
        with destination.open("rb") as equipment_file:
          equipment_file.seek(weapon.locked.offset)
          self.assertEqual(struct.unpack("<i", equipment_file.read(4))[0], store_lock)

        loadout_plugin.finalize({"rows": rows})
        with destination.open("rb") as equipment_file:
          equipment_file.seek(weapon.locked.offset)
          self.assertEqual(struct.unpack("<i", equipment_file.read(4))[0], 1)
      finally:
        mods.MOD_PATH = original_mod_path

  def test_finalize_overrides_single_item_store_lock(self) -> None:
    weapon = loadout_plugin.modify_store.ALL_STORE_ITEMS["weapon"][0]
    self._assert_loadout_finalize_overrides_store_lock({
      "type": "weapon",
      "name": weapon.name,
      "price": weapon.price.value,
      "quantity": 0,
      "weight": -1,
      "locked": 5,
    }, 5)

  def test_finalize_overrides_category_store_lock(self) -> None:
    self._assert_loadout_finalize_overrides_store_lock({
      "type": "weapon",
      "discount": 0,
      "free_price": 0,
      "bulk_quantity": 0,
      "bulk_weight": -1,
      "bulk_locked": 4,
    }, 4)

  def test_process_applies_all_rows_as_one_mod(self) -> None:
    rows = {
      str(row): modify_starting_items_2._default_row_options(row)
      for row in range(modify_starting_items.MIN_ROW, modify_starting_items.MAX_ROW + 1)
    }
    existing_names = {row.item.decode("utf-8") for row in modify_starting_items.DEFAULT_ROWS.values() if row.item}
    weapon = next(
      item for item in modify_starting_items.STARTING_ITEMS
      if item.type == "weapon"
      and item.name not in existing_names
      and any(item.name in ammo.compatible_weapons for ammo in modify_starting_items.AMMO_ITEMS)
      and any(item.name in scope.compatible_weapons for scope in modify_starting_items.SCOPE_ITEMS)
    )
    ammo = next(item for item in modify_starting_items.AMMO_ITEMS if weapon.name in item.compatible_weapons)
    scope = next(item for item in modify_starting_items.SCOPE_ITEMS if weapon.name in item.compatible_weapons)
    rows["11"] = {
      "item": weapon.name,
      "inventory_slot": 9,
      "units": 1,
      "subitem_1": ammo.name,
      "subitem_1_units": 75,
      "subitem_2": scope.name,
    }
    original_mod_path = mods.MOD_PATH

    with tempfile.TemporaryDirectory() as temp_dir:
      try:
        mods.MOD_PATH = Path(temp_dir)
        source = mods.get_org_file(modify_starting_items_2.FILE)
        destination = mods.get_modded_file(modify_starting_items_2.FILE)
        destination.parent.mkdir(parents=True)
        shutil.copy2(source, destination)
        equipment_source = mods.get_org_file(modify_starting_items_2.modify_store.EQUIPMENT_FILE)
        equipment_destination = mods.get_modded_file(modify_starting_items_2.modify_store.EQUIPMENT_FILE)
        equipment_destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(equipment_source, equipment_destination)

        modify_starting_items_2.process({"rows": rows})

        extracted_adf = mods2.deserialize_adf(modify_starting_items_2.FILE)
        expected = {
          "A12": (weapon.name.encode("utf-8"), 1),
          "B12": (9.0, 2),
          "C12": (1.0, 2),
          "D12": (ammo.name.encode("utf-8"), 1),
          "E12": (75.0, 2),
          "F12": (scope.name.encode("utf-8"), 1),
          "G12": (1.0, 2),
        }
        for coordinates, (value, data_type) in expected.items():
          cell = mods2.XlsxCell(
            modify_starting_items_2.FILE,
            extracted_adf,
            {"sheet": modify_starting_items.SHEET, "coordinates": coordinates},
          )
          self.assertEqual(cell.value, value)
          self.assertEqual(cell.data_type, data_type)
        self.assertEqual(extracted_adf.version, 3)
      finally:
        mods.MOD_PATH = original_mod_path


if __name__ == "__main__":
  unittest.main()
