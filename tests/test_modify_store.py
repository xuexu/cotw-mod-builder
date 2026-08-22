import unittest
from types import SimpleNamespace
from unittest.mock import patch

from modbuilder.plugins import modify_store


class ModifyStoreTests(unittest.TestCase):
  def setUp(self) -> None:
    self.feeder_bait = SimpleNamespace(
      type="feeder_bait",
      name="equipment_bait_site_test",
      price=SimpleNamespace(value=100, offset=10),
      quantity=SimpleNamespace(value=0, offset=0),
      weight=SimpleNamespace(value=-1, offset=0),
    )

  def test_individual_feeder_bait_does_not_require_locked_property(self) -> None:
    options = {
      "type": "feeder_bait",
      "name": self.feeder_bait.name,
      "price": 150,
      "quantity": 0,
      "weight": -1,
      "locked": -1,
    }

    with (
      patch.dict(modify_store.ALL_STORE_ITEMS, {"feeder_bait": [self.feeder_bait]}, clear=True),
      patch.object(modify_store.mods, "apply_updates_to_file") as apply_updates,
    ):
      modify_store.process(options)

    apply_updates.assert_called_once_with(modify_store.LURE_FILE, [{"offset": 10, "value": 150}])

  def test_feeder_bait_category_ignores_locked_setting(self) -> None:
    options = {
      "type": "feeder_bait",
      "discount": 10,
      "free_price": 0,
      "bulk_quantity": 0,
      "bulk_weight": -1,
      "bulk_locked": 5,
    }

    with (
      patch.dict(modify_store.ALL_STORE_ITEMS, {"feeder_bait": [self.feeder_bait]}, clear=True),
      patch.object(modify_store.mods, "apply_updates_to_file") as apply_updates,
    ):
      modify_store.process(options)

    apply_updates.assert_called_once_with(modify_store.LURE_FILE, [{"offset": 10, "value": 90}])


if __name__ == "__main__":
  unittest.main()
