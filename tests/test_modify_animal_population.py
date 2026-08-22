import shutil
import sys
import tempfile
import types
import unittest
from pathlib import Path
from unittest.mock import patch


class _GuiStub:
  def __init__(self, *args, **kwargs):
    pass


gui_module = types.ModuleType("FreeSimpleGUI")
gui_module.__getattr__ = lambda _name: _GuiStub
sys.modules.setdefault("FreeSimpleGUI", gui_module)

from modbuilder import mods
from modbuilder.plugins import modify_animal_population as population


class AnimalPopulationTests(unittest.TestCase):
  def test_reserve_selection_uses_numeric_prefix_not_display_name(self) -> None:
    selected = population._selected_reserve({
      "animal_population_reserve": "0: A translated or renamed reserve",
    })

    self.assertEqual(selected.reserve_id, 0)

  def test_reserve_display_labels_begin_with_their_stable_id(self) -> None:
    for reserve in population.ALL_RESERVES:
      self.assertTrue(reserve.display_name.startswith(f"{reserve.reserve_id}: "))

  def test_formatted_mod_resolves_current_reserve_name_from_id(self) -> None:
    text = population.format_options({
      "reserve_id": 0,
      "reserve_name": "Stale saved name",
      "species_display_name": "Red Deer",
      "male_population": 200,
      "female_population": 400,
      "advanced": False,
    })

    self.assertIn(population._get_reserve(0).display_name, text)
    self.assertNotIn("Stale saved name", text)

  def test_hirschfelden_population_fields_match_generated_baseline(self) -> None:
    reserve = population._get_reserve(0)
    red_deer = population._get_animal(reserve, 2)

    self.assertEqual(red_deer.name, "red_deer")
    self.assertEqual(red_deer.male_population, 200)
    self.assertEqual(red_deer.female_population, 400)
    self.assertEqual(red_deer.total_population, 600)
    self.assertEqual(len(red_deer.group_templates), 1)

  def test_population_allocation_preserves_solo_and_group_structure(self) -> None:
    reserve = population._get_reserve(0)
    red_deer = population._get_animal(reserve, 2)

    self.assertEqual(
      population._allocate_structural_population(red_deer, 600, 0),
      [(100, 0), (500, 0)],
    )
    self.assertEqual(
      population._allocate_structural_population(red_deer, 200, 400),
      [(100, 0), (100, 400)],
    )

  def test_group_estimates_cover_flexible_and_fixed_templates(self) -> None:
    reserve = population._get_reserve(0)
    red_deer = population._get_animal(reserve, 2)
    default_template = population._template_values(red_deer.group_templates[0])

    self.assertEqual(
      population._estimate_template_groups(default_template),
      (67, 50, 100),
    )
    fixed_template = {
      "males": 500,
      "females": 0,
      "min_males": 10,
      "max_males": 10,
      "min_females": 0,
      "max_females": 0,
      "max_size": 10,
    }
    self.assertEqual(
      population._estimate_template_groups(fixed_template),
      (50, 50, 50),
    )

  def test_group_estimate_stops_when_first_sex_pool_is_exhausted(self) -> None:
    reserve = population._get_reserve(19)
    caribou = population._get_animal(reserve, 111)
    template = population._template_values(caribou.group_templates[0])

    self.assertEqual(
      population._estimate_template_groups(template),
      (30, 20, 40),
    )

  def test_population_summary_warns_when_sex_maxima_exceed_total_size(self) -> None:
    conflicting_template = {
      "males": 250,
      "females": 250,
      "min_males": 1,
      "max_males": 4,
      "min_females": 1,
      "max_females": 4,
      "max_size": 5,
    }

    summary = population._population_summary("Modified", 0, 0, [conflicting_template])
    self.assertIn("WARNING: max males + females per group is 8 but max group size is only 5", summary)

  def test_population_summary_uses_compact_group_ranges(self) -> None:
    reserve = population._get_reserve(11)
    sheep = population._get_animal(reserve, 115)

    summary = population._population_summary(
      "Default",
      sheep.solo_males.data,
      sheep.solo_females.data,
      [population._template_values(template) for template in sheep.group_templates],
    )

    self.assertEqual(
      summary,
      "Default: 200 total animals (75 male, 125 female)  |  "
      "25 solo (25 male, 0 female)  |  33-57 groups\n"
      "  Template 1: 125 animals in 16-32 groups  |  "
      "4-8 per group (0-0 male, 4-8 female)\n"
      "  Template 2: 50 animals in 17-25 groups  |  "
      "2-3 per group (2-3 male, 0-0 female)",
    )

  def test_population_summary_hides_template_details_in_simple_mode(self) -> None:
    reserve = population._get_reserve(11)
    sheep = population._get_animal(reserve, 115)

    summary = population._population_summary(
      "Default",
      sheep.solo_males.data,
      sheep.solo_females.data,
      [population._template_values(template) for template in sheep.group_templates],
      show_templates=False,
    )

    self.assertEqual(
      summary,
      "Default: 200 total animals (75 male, 125 female)  |  "
      "25 solo (25 male, 0 female)  |  33-57 groups",
    )

  def test_population_limit_warns_at_20000(self) -> None:
    self.assertIsNone(population._population_limit_warning(9_999, 10_000))
    self.assertEqual(
      population._population_limit_warning(10_000, 10_000),
      "Reserve population of 20,000 or more may cause crashes.",
    )

  def test_advanced_options_allow_population_above_warning_threshold(self) -> None:
    red_deer = population._get_animal(population._get_reserve(0), 2)
    template = population._template_values(red_deer.group_templates[0])
    values = {
      "animal_population_solo_males": "100",
      "animal_population_solo_females": "0",
    }
    for field, value in template.items():
      values[population._template_key(0, field)] = str(value)
    values[population._template_key(0, "males")] = "24501"

    options, error = population._advanced_options(red_deer, values)

    self.assertIsNone(error)
    self.assertEqual(options["solo_males"], 100)
    self.assertEqual(options["group_templates"][0]["males"], 24_501)

  def test_population_preview_shows_warning_before_modified_values(self) -> None:
    reserve = population._get_reserve(0)
    red_deer = population._get_animal(reserve, 2)
    values = {
      "animal_population_advanced": False,
      "animal_population_males": "10000",
      "animal_population_females": "10000",
    }

    with patch.object(population, "_update_details_text") as update_details:
      population._update_population_details(object(), values, red_deer)

    preview = update_details.call_args.args[1]
    warning = "WARNING: Reserve population of 20,000 or more may cause crashes."
    self.assertIn(warning, preview)
    self.assertIn("Modified: 20000 animals", preview)
    self.assertLess(preview.index(warning), preview.index("Modified:"))

  def test_add_mod_returns_non_blocking_population_warning(self) -> None:
    reserve = population._get_reserve(0)
    red_deer = population._get_animal(reserve, 2)

    result = population.add_mod(None, {
      "animal_population_reserve": reserve.display_name,
      "animal_population_species": red_deer.display_name,
      "animal_population_advanced": False,
      "animal_population_males": "10000",
      "animal_population_females": "10000",
    })

    self.assertIsNone(result["invalid"])
    self.assertEqual(
      result["warning"],
      "Reserve population of 20,000 or more may cause crashes.",
    )

  def test_process_can_create_an_all_male_red_deer_population_target(self) -> None:
    source = mods.get_org_file(population.RESERVE_FILE.format(reserve_id=0))
    original_mod_path = mods.MOD_PATH

    with tempfile.TemporaryDirectory() as temp_dir:
      try:
        mods.MOD_PATH = Path(temp_dir)
        relative_file = population.RESERVE_FILE.format(reserve_id=0)
        destination = mods.get_modded_file(relative_file)
        destination.parent.mkdir(parents=True)
        shutil.copy2(source, destination)

        population.process({
          "reserve_id": 0,
          "species_id": 2,
          "male_population": 600,
          "female_population": 0,
        })

        reserve = population._load_reserve(destination, population.SPECIES_NAMES)
        red_deer = population._get_animal(reserve, 2)
        self.assertEqual(red_deer.male_population, 600)
        self.assertEqual(red_deer.female_population, 0)
        self.assertEqual(red_deer.solo_males.data, 100)
        self.assertEqual(red_deer.group_templates[0].male_population.data, 500)
        for template in red_deer.group_templates:
          self.assertEqual(template.min_females.data, 0)
          self.assertEqual(template.max_females.data, 0)
          self.assertEqual(template.min_males.data, 5)
          self.assertEqual(template.max_males.data, 10)
      finally:
        mods.MOD_PATH = original_mod_path

  def test_process_allows_saved_population_above_warning_threshold(self) -> None:
    source = mods.get_org_file(population.RESERVE_FILE.format(reserve_id=0))
    original_mod_path = mods.MOD_PATH

    with tempfile.TemporaryDirectory() as temp_dir:
      try:
        mods.MOD_PATH = Path(temp_dir)
        relative_file = population.RESERVE_FILE.format(reserve_id=0)
        destination = mods.get_modded_file(relative_file)
        destination.parent.mkdir(parents=True)
        shutil.copy2(source, destination)
        population.process({
          "reserve_id": 0,
          "species_id": 2,
          "male_population": 20_001,
          "female_population": 0,
        })

        reserve = population._load_reserve(destination, population.SPECIES_NAMES)
        red_deer = population._get_animal(reserve, 2)
        self.assertEqual(red_deer.male_population, 20_001)
        self.assertEqual(red_deer.female_population, 0)
      finally:
        mods.MOD_PATH = original_mod_path

  def test_process_can_create_fixed_size_red_deer_groups(self) -> None:
    source = mods.get_org_file(population.RESERVE_FILE.format(reserve_id=0))
    original_mod_path = mods.MOD_PATH

    with tempfile.TemporaryDirectory() as temp_dir:
      try:
        mods.MOD_PATH = Path(temp_dir)
        relative_file = population.RESERVE_FILE.format(reserve_id=0)
        destination = mods.get_modded_file(relative_file)
        destination.parent.mkdir(parents=True)
        shutil.copy2(source, destination)

        population.process({
          "reserve_id": 0,
          "species_id": 2,
          "advanced": True,
          "advanced_options": {
            "solo_males": 100,
            "solo_females": 0,
            "group_templates": [{
              "males": 500,
              "females": 0,
              "min_males": 10,
              "max_males": 10,
              "min_females": 0,
              "max_females": 0,
              "max_size": 10,
            }],
          },
        })

        reserve = population._load_reserve(destination, population.SPECIES_NAMES)
        red_deer = population._get_animal(reserve, 2)
        template = red_deer.group_templates[0]
        self.assertEqual(red_deer.solo_males.data, 100)
        self.assertEqual(red_deer.solo_females.data, 0)
        self.assertEqual(template.male_population.data, 500)
        self.assertEqual(template.female_population.data, 0)
        self.assertEqual(template.min_males.data, 10)
        self.assertEqual(template.max_males.data, 10)
        self.assertEqual(template.min_females.data, 0)
        self.assertEqual(template.max_females.data, 0)
        self.assertEqual(template.max_group_size.data, 10)
      finally:
        mods.MOD_PATH = original_mod_path


if __name__ == "__main__":
  unittest.main()
