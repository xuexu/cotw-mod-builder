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


LOADOUT_FILE = "settings/hp_settings/player_initial_loadout.bin"


class CellTypeConversionTests(unittest.TestCase):
  def test_blank_row_can_be_populated_and_cleared(self) -> None:
    source = mods.get_org_file(LOADOUT_FILE)
    original_mod_path = mods.MOD_PATH

    with tempfile.TemporaryDirectory() as temp_dir:
      try:
        mods.MOD_PATH = Path(temp_dir)
        destination = mods.get_modded_file(LOADOUT_FILE)
        destination.parent.mkdir(parents=True)
        shutil.copy2(source, destination)

        updates = [
          {"sheet": "weapons", "coordinates": "A12", "value": "test_starting_item", "allow_new_data": True},
          {"sheet": "weapons", "coordinates": "B12", "value": 9, "allow_new_data": True},
          {"sheet": "weapons", "coordinates": "C12", "value": 3, "allow_new_data": True},
          {"sheet": "weapons", "coordinates": "D12", "value": "equipment_ammo_243_sp_01", "allow_new_data": True},
          {"sheet": "weapons", "coordinates": "E12", "value": 12, "allow_new_data": True},
          {"sheet": "weapons", "coordinates": "F12", "value": True, "allow_new_data": True},
          {"sheet": "weapons", "coordinates": "G12", "value": True, "allow_new_data": True},
        ]
        mods2.apply_coordinate_updates_to_file(LOADOUT_FILE, updates)

        extracted_adf = mods2.deserialize_adf(LOADOUT_FILE)
        # Adding cell definitions requires ADFv3 for the game to accept the structurally expanded file
        self.assertEqual(extracted_adf.version, 3)
        expected = [
          ("A12", b"test_starting_item", 1),
          ("B12", 9.0, 2),
          ("C12", 3.0, 2),
          ("D12", b"equipment_ammo_243_sp_01", 1),
          ("E12", 12.0, 2),
          ("F12", 1, 0),
          ("G12", 1, 0),
        ]
        for coordinates, value, data_type in expected:
          cell = mods2.XlsxCell(LOADOUT_FILE, extracted_adf, {"sheet": "weapons", "coordinates": coordinates})
          self.assertEqual(cell.value, value)
          self.assertEqual(cell.data_type, data_type)

        clear_updates = [
          {"sheet": "weapons", "coordinates": f"{column}12", "value": True, "allow_new_data": True}
          for column in "ABCDEFG"
        ]
        mods2.apply_coordinate_updates_to_file(LOADOUT_FILE, clear_updates)
        extracted_adf = mods2.deserialize_adf(LOADOUT_FILE)
        for column in "ABCDEFG":
          cell = mods2.XlsxCell(LOADOUT_FILE, extracted_adf, {"sheet": "weapons", "coordinates": f"{column}12"})
          self.assertEqual(cell.value, 1)
          self.assertEqual(cell.data_type, 0)
      finally:
        mods.MOD_PATH = original_mod_path


if __name__ == "__main__":
  unittest.main()
