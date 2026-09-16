import sys
import types
import unittest


class _GuiStub:
  def __init__(self, *args, **kwargs):
    pass


gui_module = types.ModuleType("FreeSimpleGUI")
gui_module.__getattr__ = lambda _name: _GuiStub
sys.modules.setdefault("FreeSimpleGUI", gui_module)

from modbuilder.plugins import increase_weapon_fov


class IncreaseWeaponFovTests(unittest.TestCase):
  def test_plugin_uses_standard_options_with_legacy_save_keys(self) -> None:
    self.assertTrue(increase_weapon_fov.OPTIONS)
    self.assertFalse(hasattr(increase_weapon_fov, "get_option_elements"))
    self.assertFalse(hasattr(increase_weapon_fov, "add_mod"))
    self.assertFalse(hasattr(increase_weapon_fov, "load_options"))
    self.assertEqual(
      [option["key"] for option in increase_weapon_fov.OPTIONS],
      [
        "first-person_weapon_fov",
        "weapon_scope_distance",
        "weapon_iron_sight_distance",
        "use_game_settings_fov",
        "disable_scope_acceleration",
      ],
    )

  def test_legacy_partial_save_uses_defaults_for_newer_options(self) -> None:
    mapped = increase_weapon_fov.map_options({"first-person_weapon_fov": 50.0})

    self.assertEqual(mapped["first-person_weapon_fov"], 50.0)
    self.assertEqual(mapped["weapon_scope_distance"], increase_weapon_fov.SCOPE_FOV_DEFAULT)
    self.assertEqual(mapped["weapon_iron_sight_distance"], increase_weapon_fov.IRON_SIGHT_FOV_DEFAULT)
    self.assertFalse(mapped["use_game_settings_fov"])
    self.assertFalse(mapped["disable_scope_acceleration"])

  def test_game_fov_option_does_not_disable_sight_distance_controls(self) -> None:
    option = next(
      option
      for option in increase_weapon_fov.OPTIONS
      if option["key"] == "use_game_settings_fov"
    )

    self.assertNotIn("disables", option)

  def test_formatted_settings_include_sight_distances_and_background_fov(self) -> None:
    formatted = increase_weapon_fov.format_options({
      "first-person_weapon_fov": 70,
      "weapon_scope_distance": 42.5,
      "weapon_iron_sight_distance": 38.0,
      "use_game_settings_fov": True,
      "disable_scope_acceleration": False,
    })

    self.assertIn("Scope: 42.5", formatted)
    self.assertIn("Iron Sight: 38.0", formatted)
    self.assertIn("Aiming Background: Game FOV", formatted)


if __name__ == "__main__":
  unittest.main()
