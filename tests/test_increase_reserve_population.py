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
from modbuilder.plugins import increase_reserve_population as population


class IncreaseReservePopulationTests(unittest.TestCase):
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

  @staticmethod
  def _animals(file: Path, reserve_id: int) -> list[population.AnimalPopulationProperties]:
    root = population._open_reserve(file)
    return population._animal_populations(root, reserve_id)

  def test_one_multiplier_leaves_reserve_byte_for_byte_unchanged(self) -> None:
    reserve = self._copy_reserve(0)
    original = reserve.read_bytes()

    population.process({"population_multiplier": 1.0})

    self.assertEqual(reserve.read_bytes(), original)

  def test_integer_multiplier_changes_only_population_values(self) -> None:
    reserve = self._copy_reserve(0)
    original_bytes = reserve.read_bytes()
    animals = self._animals(reserve, 0)
    expected = bytearray(original_bytes)
    for animal in animals:
      for prop in animal.values:
        expected[prop.data_pos:prop.data_pos + 4] = struct.pack("i", prop.data * 3)

    population.process({"population_multiplier": 3.0})

    self.assertEqual(reserve.read_bytes(), expected)
    self.assertIsNotNone(population._open_reserve(reserve))

  def test_fractional_multiplier_has_exact_sex_totals_and_preserves_zeroes(self) -> None:
    reserve = self._copy_reserve(20)
    before = {
      animal.species_id: animal
      for animal in self._animals(reserve, 20)
    }

    population.process({"population_multiplier": 0.1})

    after = {
      animal.species_id: animal
      for animal in self._animals(reserve, 20)
    }
    for species_id, original in before.items():
      modified = after[species_id]
      for hashes in (
        population.MALE_POPULATION_HASHES,
        population.FEMALE_POPULATION_HASHES,
      ):
        original_values = [prop.data for prop in original.values if prop.name_hash in hashes]
        modified_values = [prop.data for prop in modified.values if prop.name_hash in hashes]
        self.assertEqual(sum(modified_values), round(sum(original_values) * 0.1))
        for old, new in zip(original_values, modified_values):
          if old == 0:
            self.assertEqual(new, 0)

  def test_all_modified_reserves_still_parse(self) -> None:
    copied_ids = []
    for source, reserve_id in population._reserve_files(mods.get_org_file(population.RESERVE_DIRECTORY)):
      if reserve_id in population.TROPHY_LODGE_IDS:
        continue
      self._copy_reserve(reserve_id)
      copied_ids.append(reserve_id)

    population.process({"population_multiplier": 1.5})

    for reserve_id in copied_ids:
      reserve = mods.MOD_PATH / f"settings/hp_settings/reserve_{reserve_id}.bin"
      self.assertTrue(self._animals(reserve, reserve_id))

  def test_duplicate_style_reserve_filename_is_ignored(self) -> None:
    source = mods.MOD_PATH / population.RESERVE_DIRECTORY
    source.mkdir(parents=True)
    valid = source / "reserve_0.bin"
    invalid = source / "reserve_0 (2).bin"
    valid.touch()
    invalid.touch()

    self.assertEqual(list(population._reserve_files(source)), [(valid, 0)])


if __name__ == "__main__":
  unittest.main()
