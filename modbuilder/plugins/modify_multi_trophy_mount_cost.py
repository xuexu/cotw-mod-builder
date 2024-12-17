from modbuilder import mods

DEBUG = False
NAME = "Modify Multi Trophy Mount Cost"
DESCRIPTION = "Change the cost of assembling Matmat's Multi Trophy Mounts to place in your lodges."
FILE = "settings/hp_settings/hybrid_mount_recipes.bin"
OPTIONS = [
    {
     "name": "Modified Cost Percent",
     "style": "slider",
     "min": 1.0,
     "max": 100.0,
     "initial": 100.0,
     "increment": 1,
     "note": "100% = full price, 1% = incredibly cheap"
    }
]

def load_multi_mount_prices() -> list[int]:
  mount_recipes_data = mods.open_rtpc(mods.APP_DIR_PATH / "org" / FILE)
  cost_offsets = []
  for mount_recipe in mount_recipes_data.child_table[0].child_table:
    if type(mount_recipe.prop_table[2].data) == int:
      cost_offsets.append(mount_recipe.prop_table[2].data_pos)
  return cost_offsets

def format(options: dict) -> str:
  modified_cost_percent = int(options['modified_cost_percent'])
  return f"Modify Multi Trophy Mount Cost ({modified_cost_percent}%)"

def update_values_at_offset(options: dict) -> list[dict]:
  cost_multiplier = options["modified_cost_percent"] / 100
  cost_offsets = load_multi_mount_prices()
  offsets_and_values = []
  for cost_offset in cost_offsets:
    update = {"offset": cost_offset, "value": cost_multiplier, "transform": "multiply"}
    offsets_and_values.append(update)
  return offsets_and_values
