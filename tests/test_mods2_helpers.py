import sys
import types
import unittest
from types import SimpleNamespace
from unittest.mock import ANY, call, patch


class _GuiStub:
  def __init__(self, *args, **kwargs):
    pass


# Importing mods only needs the GUI names for annotations in these tests.
gui_module = types.ModuleType("FreeSimpleGUI")
gui_module.__getattr__ = lambda _name: _GuiStub
sys.modules.setdefault("FreeSimpleGUI", gui_module)

from modbuilder import mods2


def _value(value, data_offset=0):
  return SimpleNamespace(value=value, data_offset=data_offset)


class Mods2HelperTests(unittest.TestCase):
  def test_coordinate_range_defaults_to_entire_sheet(self) -> None:
    sheet = _value({
      "Name": _value(b"example"),
      "Rows": _value(2),
      "Cols": _value(3),
    })
    adf = SimpleNamespace(
      table_instance_full_values=[_value({"Sheet": _value([sheet])})]
    )

    with patch.object(mods2, "deserialize_adf", return_value=adf):
      coordinates = mods2.get_coordinates_range_from_file("example.bin", "example")

    self.assertEqual(coordinates, ["A1", "A2", "B1", "B2", "C1", "C2"])

  def test_batch_update_options_do_not_leak_to_later_updates(self) -> None:
    updates = [
      {
        "sheet": "example",
        "coordinates": "A1",
        "value": 1,
        "allow_new_data": True,
        "skip_add_data": True,
        "force": True,
      },
      {"sheet": "example", "coordinates": "A2", "value": 2},
    ]

    with (
      patch.object(mods2, "deserialize_adf", return_value=object()),
      patch.object(mods2, "XlsxCell", side_effect=lambda _filename, _adf, update: update),
      patch.object(mods2, "process_cell_update", return_value=[]) as process_update,
      patch.object(mods2.mods, "apply_updates_to_file"),
    ):
      mods2.apply_coordinate_updates_to_file("example.bin", updates)

    self.assertEqual(process_update.call_args_list, [
      call(updates[0], ANY, skip_add_data=True, allow_new_data=True, force=True),
      call(updates[1], ANY, skip_add_data=False, allow_new_data=False, force=False),
    ])

  def test_find_closest_value_handles_large_differences(self) -> None:
    self.assertEqual(mods2.find_closest_value([0.0, 1.0], 20_000_000.0), (1, 1.0))

  def test_find_closest_value_rejects_empty_array(self) -> None:
    with self.assertRaisesRegex(ValueError, "empty array"):
      mods2.find_closest_value([], 1.0)

  def test_get_data_array_for_data_type_rejects_unknown_type(self) -> None:
    with self.assertRaisesRegex(ValueError, "Unsupported cell data type"):
      mods2.get_data_array_for_data_type({}, 99)

  def test_overwrite_value_supports_bool_data(self) -> None:
    bool_data = _value([0], data_offset=100)
    adf = SimpleNamespace(table_instance_full_values=[_value({"BoolData": bool_data})])
    cell = SimpleNamespace(
      value_index=0,
      value=0,
      value_offset=100,
      desired_value=True,
      desired_data_array_name="BoolData",
    )

    updates = mods2.overwrite_value(adf, cell)

    self.assertEqual(updates, [{"offset": 100, "value": 1, "format": "uint08"}])
    self.assertEqual(bool_data.value, [1])


if __name__ == "__main__":
  unittest.main()
