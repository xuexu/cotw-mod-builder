import unittest

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
