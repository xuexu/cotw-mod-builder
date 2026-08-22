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

  def test_game_settings_option_disables_manual_sight_distances(self) -> None:
    use_game_fov = next(option for option in increase_weapon_fov.OPTIONS if option["key"] == "use_game_settings_fov")
    self.assertEqual(use_game_fov["disables"], ["weapon_scope_distance", "weapon_iron_sight_distance"])


if __name__ == "__main__":
  unittest.main()
