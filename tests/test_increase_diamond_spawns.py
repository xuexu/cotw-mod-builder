import shutil
import struct
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

from modbuilder import mods
from modbuilder.plugins import increase_diamond_spawns as diamonds


class IncreaseDiamondSpawnsTests(unittest.TestCase):
  def setUp(self) -> None:
    self.original_mod_path = mods.MOD_PATH
    self.temp_dir = tempfile.TemporaryDirectory()
    mods.MOD_PATH = Path(self.temp_dir.name)
    self.destination = mods.MOD_PATH / diamonds.FILE
    self.destination.parent.mkdir(parents=True)
    shutil.copy2(mods.get_org_file(diamonds.FILE), self.destination)

  def tearDown(self) -> None:
    mods.MOD_PATH = self.original_mod_path
    self.temp_dir.cleanup()

  def test_zero_bias_leaves_file_byte_for_byte_unchanged(self) -> None:
    original = self.destination.read_bytes()

    diamonds.process({"weight_bias": 0.0})

    self.assertEqual(self.destination.read_bytes(), original)

  def test_only_positive_score_weight_bias_values_change(self) -> None:
    original = self.destination.read_bytes()
    root = mods.open_rtpc(self.destination)
    expected = bytearray(original)
    updates = diamonds._weight_bias_updates(root, 0.001)
    for update in updates:
      expected[update["offset"]:update["offset"] + 4] = struct.pack("f", update["value"])

    diamonds.process({"weight_bias": 0.001})

    self.assertEqual(self.destination.read_bytes(), expected)
    self.assertEqual(len(updates), 244)
    self.assertIsNotNone(mods.open_rtpc(self.destination))

  def test_low_bias_preserves_values_below_one_hundredth(self) -> None:
    root = mods.open_rtpc(self.destination)
    updates = diamonds._weight_bias_updates(root, 0.001)

    self.assertTrue(any(0 < update["value"] < 0.01 for update in updates))

  def test_rejects_out_of_range_bias(self) -> None:
    with self.assertRaisesRegex(ValueError, "between 0.0 and 0.5"):
      diamonds.process({"weight_bias": 0.501})


if __name__ == "__main__":
  unittest.main()
