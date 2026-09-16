import unittest
from unittest.mock import patch

from modbuilder import mods


# Weapon and ammo plugins use the shared equipment UI table while importing.
mods.load_equipment_ui_data()

from modbuilder.plugins import modify_ammo, modify_store, modify_weapon  # noqa: E402


def find_unmapped_equipment(items: list, equipment_type: str) -> list[str]:
  """Return every internal equipment name missing from name_map.yaml."""
  return sorted({item.name for item in items if not mods.map_equipment(item.name, equipment_type)})


class EquipmentMappingTests(unittest.TestCase):
  def assert_all_mapped(self, items: list, equipment_type: str, plugin_name: str) -> None:
    unmapped = find_unmapped_equipment(items, equipment_type)
    details = "\n".join(f"  - {name}" for name in unmapped)
    self.assertFalse(
      unmapped,
      f"{plugin_name} contains equipment missing from name_map.yaml:\n{details}",
    )

  def test_modify_store_equipment_is_mapped(self) -> None:
    # These types generate their display names from their source data rather than
    # name_map.yaml, so only test the store types that require an explicit mapping.
    generated_name_types = {"feeder_bait", "skin", "trophy_holder"}
    for equipment_type, items in modify_store.ALL_STORE_ITEMS.items():
      if equipment_type not in generated_name_types:
        with self.subTest(equipment_type=equipment_type):
          self.assert_all_mapped(items, equipment_type, "Modify Store")

  def test_modify_weapon_equipment_is_mapped(self) -> None:
    weapons = [weapon for category in modify_weapon.ALL_WEAPONS.values() for weapon in category]
    self.assert_all_mapped(weapons, "weapon", "Modify Weapon")

  def test_modify_ammo_equipment_is_mapped(self) -> None:
    ammo = [item for category in modify_ammo.ALL_AMMO.values() for item in category]
    self.assert_all_mapped(ammo, "ammo", "Modify Ammo")

  def test_modify_ammo_items_are_grouped_by_resolved_type(self) -> None:
    for ammo_type, ammo_list in modify_ammo.ALL_AMMO.items():
      with self.subTest(ammo_type=ammo_type):
        self.assertTrue(all(ammo.type == ammo_type for ammo in ammo_list))

  def test_modify_ammo_uses_case_normalized_mapped_type_override(self) -> None:
    ammo = object.__new__(modify_ammo.Ammo)
    ammo.file = "editor/entities/hp_weapons/ammunition/rifles/equipment_ammo_test_01.ammotunec"
    mapped = {"map_name": "test_01", "name": "Test Ammo", "type": "Handgun"}

    with patch.object(modify_ammo.mods, "map_equipment", return_value=mapped):
      ammo._parse_name_and_type()

    self.assertEqual(ammo.type, "handgun")

  def test_modify_ammo_unmapped_type_falls_back_to_source_directory(self) -> None:
    ammo = object.__new__(modify_ammo.Ammo)
    ammo.file = "editor/entities/hp_weapons/ammunition/rifles/equipment_ammo_test_01.ammotunec"

    with patch.object(modify_ammo.mods, "map_equipment", return_value={}):
      ammo._parse_name_and_type()

    self.assertEqual(ammo.type, "rifle")
    self.assertEqual(ammo.display_name, "equipment_ammo_test_01")

  def test_44_40_ammo_is_only_in_handgun_category(self) -> None:
    ammo_names = {"44_40_bp_rnfp_01", "44_40_fmj_01"}
    handgun_ammo = [ammo for ammo in modify_ammo.ALL_AMMO["handgun"] if ammo.name in ammo_names]
    rifle_ammo = [ammo for ammo in modify_ammo.ALL_AMMO["rifle"] if ammo.name in ammo_names]

    self.assertEqual({ammo.name for ammo in handgun_ammo}, ammo_names)
    self.assertFalse(rifle_ammo)

    handgun_category_files = set(modify_ammo.get_files({"type": "handgun"}))
    rifle_category_files = set(modify_ammo.get_files({"type": "rifle"}))
    for ammo in handgun_ammo:
      self.assertIn(ammo.file, handgun_category_files)
      self.assertNotIn(ammo.file, rifle_category_files)


class ModifyWeaponEventTests(unittest.TestCase):
  def test_bullet_drop_does_not_reselect_default_magazine_size(self) -> None:
    self.assertFalse(modify_weapon.should_update_magazine_settings("modify_weapon_disable_bullet_drop"))

  def test_weapon_and_auto_magazine_events_reselect_default_magazine_size(self) -> None:
    self.assertTrue(modify_weapon.should_update_magazine_settings("modify_weapon_list_rifle"))
    self.assertTrue(modify_weapon.should_update_magazine_settings("modify_weapon_tab_group"))
    self.assertTrue(modify_weapon.should_update_magazine_settings("modify_weapon_select_default_magazine_size"))
