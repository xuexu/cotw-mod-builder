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
from modbuilder.plugins import increase_deployables as deployables


class IncreaseDeployablesTests(unittest.TestCase):
  def setUp(self) -> None:
    self.original_mod_path = mods.MOD_PATH
    self.temp_dir = tempfile.TemporaryDirectory()
    mods.MOD_PATH = Path(self.temp_dir.name)

  def tearDown(self) -> None:
    mods.MOD_PATH = self.original_mod_path
    self.temp_dir.cleanup()

  def _copy_reserve(self, reserve_id: int) -> Path:
    relative = Path(f"settings/hp_settings/reserve_{reserve_id}.bin")
    destination = mods.MOD_PATH / relative
    destination.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(mods.get_org_file(relative.as_posix()), destination)
    return destination

  def test_fractional_multiplier_is_preserved_in_display(self) -> None:
    self.assertEqual(
      deployables.format_options({"deployable_multiplier": 1.5}),
      "Increase Deployables (1.5x)",
    )

  def test_one_multiplier_leaves_reserve_byte_for_byte_unchanged(self) -> None:
    reserve = self._copy_reserve(0)
    original = reserve.read_bytes()

    deployables.process({"deployable_multiplier": 1.0})

    self.assertEqual(reserve.read_bytes(), original)

  def test_fractional_multiplier_changes_only_deployable_limits(self) -> None:
    reserve = self._copy_reserve(0)
    original_bytes = reserve.read_bytes()
    values = deployables._deployable_max_counts(deployables._open_reserve(reserve), 0)
    expected = bytearray(original_bytes)
    for prop in values:
      expected[prop.data_pos:prop.data_pos + 4] = struct.pack("i", round(prop.data * 1.1))

    deployables.process({"deployable_multiplier": 1.1})

    self.assertEqual(reserve.read_bytes(), expected)
    modified_values = deployables._deployable_max_counts(deployables._open_reserve(reserve), 0)
    self.assertEqual(
      [prop.data for prop in modified_values],
      [round(prop.data * 1.1) for prop in values],
    )

  def test_all_modified_reserves_still_parse(self) -> None:
    copied_ids = []
    for source, reserve_id in deployables._reserve_files(mods.get_org_file(deployables.RESERVE_DIRECTORY)):
      if reserve_id in deployables.TROPHY_LODGE_IDS:
        continue
      self._copy_reserve(reserve_id)
      copied_ids.append(reserve_id)

    deployables.process({"deployable_multiplier": 1.5})

    for reserve_id in copied_ids:
      reserve = mods.MOD_PATH / f"settings/hp_settings/reserve_{reserve_id}.bin"
      root = deployables._open_reserve(reserve)
      self.assertTrue(deployables._deployable_max_counts(root, reserve_id))

  def test_duplicate_style_reserve_filename_is_ignored(self) -> None:
    source = mods.MOD_PATH / deployables.RESERVE_DIRECTORY
    source.mkdir(parents=True)
    valid = source / "reserve_0.bin"
    invalid = source / "reserve_0 (2).bin"
    valid.touch()
    invalid.touch()

    self.assertEqual(list(deployables._reserve_files(source)), [(valid, 0)])


if __name__ == "__main__":
  unittest.main()
