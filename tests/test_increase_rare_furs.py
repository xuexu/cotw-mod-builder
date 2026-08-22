import shutil
import struct
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace

from modbuilder import mods
from modbuilder.plugins import increase_rare_furs


def fur(weight: int, rarity: int, offset: int, gender: int = 0):
  return SimpleNamespace(weight=weight, rarity=rarity, weight_offset=offset, gender=gender)


class IncreaseRareFursTests(unittest.TestCase):
  def setUp(self) -> None:
    # Brown, grey, tan, piebald, albino, and leucistic from the documented example
    self.furs = [
      fur(100, 0, 1),
      fur(100, 0, 2),
      fur(25, 1, 3),
      fur(5, 2, 4),
      fur(1, 3, 5),
      fur(1, 3, 6),
    ]

  def test_zero_percent_preserves_original_weights(self) -> None:
    weights = increase_rare_furs.calculate_fur_weights(self.furs, 0)

    self.assertEqual(weights, {1: 100, 2: 100, 3: 25, 4: 5, 5: 1, 6: 1})

  def test_fur_fields_are_read_by_hash_when_optional_properties_are_missing(self) -> None:
    variant = SimpleNamespace(prop_map={
      increase_rare_furs.FUR_NAME_HASH: SimpleNamespace(data=b"animal_visual_variation_mosaic", data_pos=10),
      increase_rare_furs.FUR_WEIGHT_HASH: SimpleNamespace(data=100, data_pos=20),
      increase_rare_furs.FUR_RARITY_HASH: SimpleNamespace(data=2, data_pos=30),
      increase_rare_furs.FUR_GENDER_HASH: SimpleNamespace(data=1, data_pos=40),
    })

    parsed = increase_rare_furs.Fur(variant)

    self.assertEqual(parsed.name, "animal_visual_variation_mosaic")
    self.assertEqual(parsed.weight, 100)
    self.assertEqual(parsed.weight_offset, 20)
    self.assertEqual(parsed.rarity, 2)
    self.assertEqual(parsed.rarity_offset, 30)
    self.assertEqual(parsed.gender, increase_rare_furs.GENDER_MALE)
    self.assertFalse(parsed.is_great_one)

  def test_great_one_property_excludes_fur_without_obvious_name(self) -> None:
    variant = SimpleNamespace(
      name_hash=1,
      prop_map={
        increase_rare_furs.CLASS_HASH: SimpleNamespace(
          data=increase_rare_furs.VISUAL_VARIATION_CLASS,
        ),
        increase_rare_furs.FUR_NAME_HASH: SimpleNamespace(
          data=b"animal_visual_variation_frostbite",
        ),
        increase_rare_furs.FUR_WEIGHT_HASH: SimpleNamespace(data=25, data_pos=20),
        increase_rare_furs.FUR_RARITY_HASH: SimpleNamespace(data=3, data_pos=30),
        increase_rare_furs.FUR_GENDER_HASH: SimpleNamespace(data=1, data_pos=40),
        increase_rare_furs.FUR_GREAT_ONE_HASH: SimpleNamespace(data=1),
      },
    )

    self.assertEqual(increase_rare_furs.get_furs([variant]), [])

    parsed = increase_rare_furs.Fur(variant)
    self.assertTrue(parsed.is_great_one)

  def test_great_one_name_remains_a_fallback_when_property_is_missing(self) -> None:
    variant = SimpleNamespace(
      name_hash=1,
      prop_map={
        increase_rare_furs.CLASS_HASH: SimpleNamespace(
          data=increase_rare_furs.VISUAL_VARIATION_CLASS,
        ),
        increase_rare_furs.FUR_NAME_HASH: SimpleNamespace(
          data=b"animal_visual_variation_great_one_example",
        ),
        increase_rare_furs.FUR_WEIGHT_HASH: SimpleNamespace(data=25, data_pos=20),
        increase_rare_furs.FUR_RARITY_HASH: SimpleNamespace(data=3, data_pos=30),
        increase_rare_furs.FUR_GENDER_HASH: SimpleNamespace(data=1, data_pos=40),
      },
    )

    self.assertEqual(increase_rare_furs.get_furs([variant]), [])

    parsed = increase_rare_furs.Fur(variant)
    self.assertTrue(parsed.is_great_one)

  def test_one_hundred_percent_removes_nonrares_and_evenly_splits_rares(self) -> None:
    weights = increase_rare_furs.calculate_fur_weights(self.furs, 100)

    self.assertEqual([weights[i] for i in (1, 2, 3)], [0, 0, 0])
    self.assertEqual(sum(weights.values()), 232)
    self.assertLessEqual(max(weights[i] for i in (4, 5, 6)) - min(weights[i] for i in (4, 5, 6)), 1)

  def test_midpoint_preserves_total_weight_and_nonrare_ratios(self) -> None:
    weights = increase_rare_furs.calculate_fur_weights(self.furs, 50)

    self.assertEqual(sum(weights.values()), 232)
    self.assertEqual(weights[1], weights[2])
    self.assertAlmostEqual(weights[1] / weights[3], 4, delta=0.2)
    self.assertGreater(sum(weights[i] for i in (4, 5, 6)), 116)

  def test_species_without_rare_furs_are_unchanged(self) -> None:
    common_furs = [fur(75, 0, 1), fur(25, 1, 2)]

    self.assertEqual(increase_rare_furs.calculate_fur_weights(common_furs, 100), {1: 75, 2: 25})

  def test_zero_weight_quest_furs_require_explicit_opt_in(self) -> None:
    furs = [fur(100, 0, 1), fur(5, 2, 2), fur(0, 3, 3)]

    excluded = increase_rare_furs.calculate_fur_weights(furs, 100)
    included = increase_rare_furs.calculate_fur_weights(furs, 100, include_quest_only_furs=True)

    self.assertEqual(excluded, {1: 0, 2: 105, 3: 0})
    self.assertEqual(included[1], 0)
    self.assertEqual(sum(included.values()), 105)
    self.assertLessEqual(abs(included[2] - included[3]), 1)

  def test_gender_without_rare_furs_is_not_drained(self) -> None:
    furs = [
      fur(100, 0, 1, increase_rare_furs.GENDER_MALE),
      fur(5, 2, 2, increase_rare_furs.GENDER_MALE),
      fur(100, 0, 3, increase_rare_furs.GENDER_FEMALE),
    ]

    weights = increase_rare_furs.calculate_fur_weights(furs, 100)

    self.assertEqual(weights, {1: 0, 2: 105, 3: 100})

  def test_shared_fur_is_protected_if_either_applicable_gender_has_no_rare_fur(self) -> None:
    furs = [
      fur(100, 0, 1, increase_rare_furs.GENDER_BOTH),
      fur(5, 2, 2, increase_rare_furs.GENDER_MALE),
      fur(100, 0, 3, increase_rare_furs.GENDER_FEMALE),
    ]

    weights = increase_rare_furs.calculate_fur_weights(furs, 100)

    self.assertEqual(weights, {1: 100, 2: 5, 3: 100})

  def test_whitetail_great_one_receives_removed_male_common_weight(self) -> None:
    all_furs = [
      SimpleNamespace(
        name="animal_visual_variation_tan",
        gender=increase_rare_furs.GENDER_MALE,
        weight=25_000,
        weight_offset=1,
      ),
      SimpleNamespace(
        name="animal_visual_variation_brown",
        gender=increase_rare_furs.GENDER_MALE,
        weight=25_000,
        weight_offset=2,
      ),
      SimpleNamespace(
        name="animal_visual_variation_dark_brown",
        gender=increase_rare_furs.GENDER_MALE,
        weight=25_000,
        weight_offset=3,
      ),
      SimpleNamespace(
        name="animal_visual_variation_great_one_whitetail",
        gender=increase_rare_furs.GENDER_MALE,
        weight=38,
        weight_offset=4,
      ),
    ]
    ordinary_updates = {1: 12_500, 2: 12_500, 3: 12_500, 9: 123}

    great_one_updates = increase_rare_furs._whitetail_great_one_updates(
      all_furs,
      ordinary_updates,
    )

    self.assertEqual(great_one_updates, {4: 37_538})
    self.assertEqual(ordinary_updates, {1: 12_500, 2: 12_500, 3: 12_500, 9: 123})

  def test_old_slider_values_are_converted_to_the_new_scale(self) -> None:
    cases = {
      1.5: 0.0,
      10.0: 8.5,
      25.0: 24.0,
      50.0: 49.0,
      100.0: 100.0,
    }
    for old_value, expected in cases.items():
      key, options = increase_rare_furs.handle_update(
        "increase_rare_furs",
        {"rare_fur_percentage": old_value},
        "old-version",
      )
      self.assertEqual(key, "increase_rare_furs")
      self.assertEqual(options, {
        "rare_fur_increase": expected,
        "include_quest_only_furs": False,
      })

  def test_new_slider_saves_do_not_require_conversion(self) -> None:
    original = {"rare_fur_increase": 50.0, "include_quest_only_furs": True}

    key, options = increase_rare_furs.handle_update("increase_rare_furs", original, "new-version")

    self.assertEqual(key, "increase_rare_furs")
    self.assertIs(options, original)

  def test_new_slider_saves_gain_the_new_quest_fur_default(self) -> None:
    key, options = increase_rare_furs.handle_update(
      "increase_rare_furs",
      {"rare_fur_increase": 50.0},
      "new-version",
    )

    self.assertEqual(key, "increase_rare_furs")
    self.assertEqual(options, {"rare_fur_increase": 50.0, "include_quest_only_furs": False})


class IncreaseRareFursFileTests(unittest.TestCase):
  def setUp(self) -> None:
    self.original_mod_path = mods.MOD_PATH
    self.temp_dir = tempfile.TemporaryDirectory()
    mods.MOD_PATH = Path(self.temp_dir.name)
    self.destination = mods.MOD_PATH / increase_rare_furs.FILE
    self.destination.parent.mkdir(parents=True)
    shutil.copy2(mods.get_org_file(increase_rare_furs.FILE), self.destination)

  def tearDown(self) -> None:
    mods.MOD_PATH = self.original_mod_path
    self.temp_dir.cleanup()

  def test_process_changes_only_calculated_fur_weight_fields(self) -> None:
    original = self.destination.read_bytes()
    root = mods.open_rtpc(self.destination)
    expected = bytearray(original)
    expected_update_count = 0
    for animal in root.child_table[0].child_table:
      variations = increase_rare_furs.get_variations_table(animal)
      if variations is None:
        continue
      all_furs = increase_rare_furs.get_all_furs(variations.child_table)
      furs = [fur for fur in all_furs if not fur.is_great_one]
      updates = increase_rare_furs.calculate_fur_weights(furs, 25.0, True)
      updates.update(increase_rare_furs._whitetail_great_one_updates(all_furs, updates))
      for offset, value in updates.items():
        expected[offset:offset + 4] = struct.pack("i", value)
        expected_update_count += 1

    increase_rare_furs.process({
      "rare_fur_increase": 25.0,
      "include_quest_only_furs": True,
    })

    self.assertGreater(expected_update_count, 0)
    self.assertEqual(self.destination.read_bytes(), expected)
    self.assertIsNotNone(mods.open_rtpc(self.destination))

  def test_process_rejects_out_of_range_percentage(self) -> None:
    with self.assertRaisesRegex(ValueError, "between 0 and 100"):
      increase_rare_furs.process({"rare_fur_increase": 100.5})

  def test_one_hundred_percent_preserves_every_non_whitetail_great_one_weight(self) -> None:
    root = mods.open_rtpc(self.destination)
    great_one_furs = []
    for animal in root.child_table[0].child_table:
      variations = increase_rare_furs.get_variations_table(animal)
      if variations is None:
        continue
      great_one_furs.extend(
        fur
        for fur in increase_rare_furs.get_all_furs(variations.child_table)
        if fur.is_great_one
      )

    increase_rare_furs.process({
      "rare_fur_increase": 100.0,
      "include_quest_only_furs": True,
    })

    modified_bytes = self.destination.read_bytes()
    checked = 0
    for fur in great_one_furs:
      modified_weight = struct.unpack_from("i", modified_bytes, fur.weight_offset)[0]
      if fur.name == "animal_visual_variation_great_one_whitetail":
        self.assertEqual(modified_weight, 75_038)
      else:
        self.assertEqual(modified_weight, fur.weight, fur.name)
        checked += 1
    self.assertEqual(checked, 79)


if __name__ == "__main__":
  unittest.main()
