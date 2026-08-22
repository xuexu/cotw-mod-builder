import shutil
import tempfile
import unittest
from pathlib import Path

from deca.ff_rtpc import rtpc_from_binary
from modbuilder import mods
from modbuilder.plugins import modify_weather
from modbuilder.widgets import option_key


def _condition_names(path: Path) -> list[str]:
  with path.open("rb") as fp:
    data = rtpc_from_binary(fp)
  nodes = data.root_node.child_table[0].child_table
  return [node.prop_table[1].data.decode("utf-8") for node in nodes]


def _condition_nodes(path: Path):
  with path.open("rb") as fp:
    data = rtpc_from_binary(fp)
  return data.root_node.child_table[0].child_table


class ModifyWeatherTests(unittest.TestCase):
  def test_experimental_checkbox_uses_the_expected_event_key(self) -> None:
    experimental_option = modify_weather.OPTIONS[0]
    self.assertEqual(option_key(experimental_option), "experimental_show_all_weathers")
    self.assertEqual(
      modify_weather.EXPERIMENTAL_OPTION_KEY,
      f"modify_weather__{option_key(experimental_option)}",
    )

  def test_reserve_and_engine_conditions_are_protected(self) -> None:
    self.assertTrue(any(name.startswith("reserve_") for name in modify_weather.RESERVE_WEATHER_CONDITIONS))
    self.assertIn("damage_effect", modify_weather.PROTECTED_WEATHER_CONDITIONS)
    self.assertIn("base", modify_weather.PROTECTED_WEATHER_CONDITIONS)
    self.assertFalse(any(name.startswith("reserve_") for name in modify_weather.AVAILABLE_WEATHER_CONDITIONS))

  def test_process_only_disables_selectable_weather_conditions(self) -> None:
    source = mods.get_org_file(modify_weather.PRESETS_FILE)
    original_mod_path = mods.MOD_PATH

    with tempfile.TemporaryDirectory() as temp_dir:
      try:
        mods.MOD_PATH = Path(temp_dir)
        destination = mods.get_modded_file(modify_weather.PRESETS_FILE)
        destination.parent.mkdir(parents=True)
        shutil.copy2(source, destination)

        original_nodes = _condition_nodes(source)
        modify_weather.process({"allowed_weather_conditions": ["forced_sunny"]})
        modified_nodes = _condition_nodes(destination)

        for original, modified in zip(original_nodes, modified_nodes):
          original_name = original.prop_table[1].data.decode("utf-8")
          modified_name = modified.prop_table[1].data.decode("utf-8")
          self.assertEqual(modified.name_hash, original.name_hash)
          if (
            original_name == "forced_sunny"
            or original_name in modify_weather.PROTECTED_WEATHER_CONDITIONS
            or original_name in modify_weather.RESERVE_WEATHER_CONDITIONS
          ):
            self.assertEqual(modified_name, original_name)
          else:
            self.assertEqual(modified_name, "base")
      finally:
        mods.MOD_PATH = original_mod_path

  def test_experimental_mode_can_redirect_a_reserve_override(self) -> None:
    source = mods.get_org_file(modify_weather.PRESETS_FILE)
    original_mod_path = mods.MOD_PATH

    with tempfile.TemporaryDirectory() as temp_dir:
      try:
        mods.MOD_PATH = Path(temp_dir)
        destination = mods.get_modded_file(modify_weather.PRESETS_FILE)
        destination.parent.mkdir(parents=True)
        shutil.copy2(source, destination)

        allowed = modify_weather.ALL_WEATHER_CONDITIONS.copy()
        allowed.remove("reserve_19_snowstorm")
        modify_weather.process({
          "experimental_show_all_weathers": True,
          "allowed_weather_conditions": allowed,
        })

        names_by_hash = {
          node.name_hash: node.prop_table[1].data.decode("utf-8")
          for node in _condition_nodes(destination)
        }
        original_nodes = _condition_nodes(source)
        snowstorm_hash = next(
          node.name_hash
          for node in original_nodes
          if node.prop_table[1].data == b"reserve_19_snowstorm"
        )
        self.assertEqual(names_by_hash[snowstorm_hash], "reserve_19")
      finally:
        mods.MOD_PATH = original_mod_path

  def test_game_defaults_leave_file_unchanged(self) -> None:
    source = mods.get_org_file(modify_weather.PRESETS_FILE)
    original_mod_path = mods.MOD_PATH

    with tempfile.TemporaryDirectory() as temp_dir:
      try:
        mods.MOD_PATH = Path(temp_dir)
        destination = mods.get_modded_file(modify_weather.PRESETS_FILE)
        destination.parent.mkdir(parents=True)
        shutil.copy2(source, destination)

        modify_weather.process({"allowed_weather_conditions": modify_weather.AVAILABLE_WEATHER_CONDITIONS})

        self.assertEqual(destination.read_bytes(), source.read_bytes())
      finally:
        mods.MOD_PATH = original_mod_path


if __name__ == "__main__":
  unittest.main()
