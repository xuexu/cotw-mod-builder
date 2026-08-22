import shutil
import sys
import tempfile
import types
import unittest
from pathlib import Path


class _GuiStub:
  def __init__(self, *args, **kwargs):
    pass


# Importing mods only needs the GUI names for annotations in these tests.
gui_module = types.ModuleType("FreeSimpleGUI")
gui_module.__getattr__ = lambda _name: _GuiStub
sys.modules.setdefault("FreeSimpleGUI", gui_module)

from modbuilder import mods, mods2


class CellDefinitionAlignmentTests(unittest.TestCase):
  def test_added_cell_definitions_keep_following_arrays_aligned(self) -> None:
    source = mods.get_org_file(mods.EQUIPMENT_UI_FILE)
    original_mod_path = mods.MOD_PATH

    with tempfile.TemporaryDirectory() as temp_dir:
      try:
        mods.MOD_PATH = Path(temp_dir)
        destination = mods.get_modded_file(mods.EQUIPMENT_UI_FILE)
        destination.parent.mkdir(parents=True)
        shutil.copy2(source, destination)

        original_adf = mods2.deserialize_adf(mods.EQUIPMENT_UI_FILE)
        original_value_data = list(original_adf.table_instance_full_values[0].value["ValueData"].value)

        updates = [
          {
            "sheet": "ammo",
            "coordinates": "F2",
            "value": "test-classes-one",
            "allow_new_data": True,
          },
          {
            "sheet": "ammo",
            "coordinates": "F4",
            "value": "test-classes-two",
            "allow_new_data": True,
          },
        ]
        mods2.apply_coordinate_updates_to_file(mods.EQUIPMENT_UI_FILE, updates)

        extracted_adf = mods2.deserialize_adf(mods.EQUIPMENT_UI_FILE)
        adf_values = extracted_adf.table_instance_full_values[0].value
        self.assertEqual(adf_values["StringData"].data_offset % 8, 0)
        self.assertEqual(adf_values["ValueData"].data_offset % 8, 0)
        self.assertEqual(adf_values["ValueData"].value, original_value_data)

        for update in updates:
          cell = mods2.XlsxCell(
            mods.EQUIPMENT_UI_FILE,
            extracted_adf,
            update,
          )
          self.assertEqual(cell.value, update["value"].encode("utf-8"))
      finally:
        mods.MOD_PATH = original_mod_path

  def test_added_floats_replace_valuedata_alignment_padding(self) -> None:
    source_file = "settings/hp_settings/player_skill_trees.bin"
    source = mods.get_org_file(source_file)
    original_mod_path = mods.MOD_PATH

    with tempfile.TemporaryDirectory() as temp_dir:
      try:
        mods.MOD_PATH = Path(temp_dir)
        destination = mods.get_modded_file(source_file)
        destination.parent.mkdir(parents=True)
        shutil.copy2(source, destination)

        original_size = destination.stat().st_size
        extracted_adf = mods2.deserialize_adf(source_file)
        original_values = list(extracted_adf.table_instance_full_values[0].value["ValueData"].value)
        file_updates = []
        for value in [2.0, 3.0, 4.0]:
          file_updates.extend(mods2.add_float_to_valuedata(extracted_adf, value))
        mods.apply_updates_to_file(source_file, file_updates)

        # Five original floats have 4 bytes of padding. Growing to eight floats consumes that padding, so the net growth is only 8 bytes
        self.assertEqual(destination.stat().st_size, original_size + 8)
        extracted_adf = mods2.deserialize_adf(source_file)
        adf_values = extracted_adf.table_instance_full_values[0].value
        self.assertEqual(adf_values["ValueData"].value, original_values + [2.0, 3.0, 4.0])
        for array_name in ["Sheet", "Cell", "StringData", "ValueData", "BoolData", "ColorData", "Attribute"]:
          self.assertEqual(adf_values[array_name].data_offset % 8, 0, array_name)
      finally:
        mods.MOD_PATH = original_mod_path


if __name__ == "__main__":
  unittest.main()
