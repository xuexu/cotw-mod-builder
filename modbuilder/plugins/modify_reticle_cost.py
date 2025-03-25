from modbuilder import mods
from deca.ff_rtpc import RtpcNode

DEBUG = False
NAME = "Modify Reticle Cost"
DESCRIPTION = "Reduce the cost of changing the reticle on your scopes. Requires the Scopes and Crosshairs DLC pack."
FILE = mods.EQUIPMENT_DATA_FILE
OPTIONS = [
    {
     "name": "Cost",
     "style": "slider",
     "min": 0.0,
     "max": 4500.0,
     "initial": 4500.0,
     "increment": 10,
    }
]
PRESETS = [
  {
   "name": "Game Defaults",
   "options": [
     {"name": "cost", "value": 4500.0},
    ]
  },
  {
   "name": "Free",
   "options": [
     {"name": "cost", "value": 0.0},
    ]
  },
]

class Reticle:
  def __init__(self, equipment_node: RtpcNode) -> None:
    if type(equipment_node.prop_table[2].data) == bytes:
      name = equipment_node.prop_table[2].data.decode('utf-8')
      if "reticle" in name:
        self.name = name
        if type(equipment_node.prop_table[0].data) == int:
          self.cost = equipment_node.prop_table[0].data
          self.offset = equipment_node.prop_table[0].data_pos
        else:
          raise ValueError("Item does not have an integer at position 0")
      else:
        raise ValueError('Name does not contain "reticle"')
    else:
      raise ValueError("Item does not have a name at position 2")

def load_reticles() -> list[Reticle]:
  reticles = []
  equipment_data = mods.open_rtpc(mods.APP_DIR_PATH / "org" / FILE)
  # reticles are stored in the "skins" table at index 5
  for equipment_node in equipment_data.child_table[5].child_table:
    try:
      reticle = Reticle(equipment_node)
      reticles.append(reticle)
    except ValueError as e:  # Reticle.__init__ () returns a ValueError if it fails to match reticle data
      continue  # safely ignore the error and skip the item
  return reticles

def format(options: dict) -> str:
  cost = int(options['cost'])
  return f"Modify Reticle Cost (${cost})"

def update_values_at_offset(options: dict) -> list[dict]:
  offsets_and_values = []
  cost = int(options["cost"])
  reticles = load_reticles()
  for reticle in reticles:
    update = {"offset": reticle.offset, "value": cost}
    offsets_and_values.append(update)
  return offsets_and_values
