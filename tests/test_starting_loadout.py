import shutil
import sys
import tempfile
import types
import unittest
from pathlib import Path


class _GuiStub:
  def __init__(self, *args, **kwargs):
    pass


gui_module = types.ModuleType("FreeSimpleGUI")
gui_module.__getattr__ = lambda _name: _GuiStub
sys.modules.setdefault("FreeSimpleGUI", gui_module)

from modbuilder import mods, mods2
from modbuilder.plugins import custom_starting_loadout as starting_loadout


class StartingLoadoutTests(unittest.TestCase):
  def test_default_loadout_rows_are_parsed(self) -> None:
    rifle = starting_loadout.DEFAULT_ROWS[1]
    self.assertEqual(rifle.item, b"equipment_weapon_ba_rifle_243_01")
    self.assertEqual(rifle.inventory_slot, 1)
    self.assertEqual(rifle.units, 1)
    self.assertEqual(rifle.subitem_1, b"equipment_ammo_243_sp_01")
    self.assertEqual(rifle.subitem_1_units, 50)
    self.assertEqual(rifle.subitem_2, b"equipment_sight_rifle_scope_1-4x_24mm_01")

    self.assertIsNone(starting_loadout.DEFAULT_ROWS[11].item)

  def test_process_populates_a_blank_row_with_equipment_data_item(self) -> None:
    existing_names = {
      row.item.decode("utf-8")
      for row in starting_loadout.DEFAULT_ROWS.values()
      if row.item
    }
    selected_item = next(item for item in starting_loadout.STARTING_ITEMS if item.type == "weapon" and item.name not in existing_names)
    options = {
      "row": 11,
      "item": selected_item.name,
      "item_display_name": selected_item.display_name,
      "inventory_slot": 9,
      "units": 2,
      "subitem_1": "equipment_ammo_243_sp_01",
      "subitem_1_units": 100,
      "subitem_2": None,
    }
    original_mod_path = mods.MOD_PATH

    with tempfile.TemporaryDirectory() as temp_dir:
      try:
        mods.MOD_PATH = Path(temp_dir)
        source = mods.get_org_file(starting_loadout.FILE)
        destination = mods.get_modded_file(starting_loadout.FILE)
        destination.parent.mkdir(parents=True)
        shutil.copy2(source, destination)

        mods2.apply_coordinate_updates_to_file(
          starting_loadout.FILE,
          starting_loadout.build_coordinate_updates(options),
          allow_new_data=True,
        )

        extracted_adf = mods2.deserialize_adf(starting_loadout.FILE)
        expected = {
          "A12": (selected_item.name.encode("utf-8"), 1),
          "B12": (9.0, 2),
          "C12": (1.0, 2),
          "D12": (b"equipment_ammo_243_sp_01", 1),
          "E12": (100.0, 2),
          "F12": (1, 0),
          "G12": (1, 0),
        }
        for coordinates, (value, data_type) in expected.items():
          cell = mods2.XlsxCell(
            starting_loadout.FILE,
            extracted_adf,
            {"sheet": starting_loadout.SHEET, "coordinates": coordinates},
          )
          self.assertEqual(cell.value, value)
          self.assertEqual(cell.data_type, data_type)
        # Adding cell definitions requires ADFv3 for the game to accept the structurally expanded file
        self.assertEqual(extracted_adf.version, 3)
      finally:
        mods.MOD_PATH = original_mod_path

  def test_scope_quantity_is_fixed_and_loadout_rows_skip_the_header(self) -> None:
    updates = starting_loadout.build_coordinate_updates({
      "row": 1,
      "item": "equipment_weapon_ba_rifle_243_01",
      "inventory_slot": 1,
      "units": 1,
      "subitem_1": None,
      "subitem_1_units": 1,
      "subitem_2": "equipment_sight_rifle_scope_1-4x_24mm_01",
      "subitem_2_units": 99,
    })

    self.assertEqual(updates[0]["coordinates"], "A2")
    self.assertEqual(updates[6]["coordinates"], "G2")
    self.assertEqual(updates[6]["value"], 1)

  def test_outfit_and_backpack_values_use_equipped_state(self) -> None:
    for detailed_type in ("Clothing", "Upgrade"):
      item = next(item for item in starting_loadout.STARTING_ITEMS if item.detailed_type == detailed_type)
      base_options = {
        "row": 11,
        "item": item.name,
        "inventory_slot": 8,
        "units": 50,
        "subitem_1": None,
        "subitem_1_units": 1,
        "subitem_2": None,
      }

      unlocked = starting_loadout.build_coordinate_updates({**base_options, "equipped": False})
      equipped = starting_loadout.build_coordinate_updates({**base_options, "equipped": True})

      self.assertEqual(unlocked[1]["value"], -1)
      self.assertEqual(equipped[1]["value"], 0)
      self.assertEqual(unlocked[2]["value"], 1)

  def test_only_stackable_item_categories_support_quantity(self) -> None:
    for item in starting_loadout.STARTING_ITEMS:
      expected = (
        item.type in ("ammo", "structure")
        or (item.type == "misc" and item.detailed_type == "Consumable")
        or (item.type == "lure" and item.detailed_type in ("Decoy", "Scent"))
      )
      self.assertEqual(item.supports_quantity, expected, item.display_name)

    weapon = next(item for item in starting_loadout.STARTING_ITEMS if item.type == "weapon")
    updates = starting_loadout.build_coordinate_updates({
      "row": 11,
      "item": weapon.name,
      "inventory_slot": 1,
      "units": 99,
      "subitem_1": None,
      "subitem_1_units": 1,
      "subitem_2": None,
    })
    self.assertEqual(updates[2]["value"], 1)


if __name__ == "__main__":
  unittest.main()
