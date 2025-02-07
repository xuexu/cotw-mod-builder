from modbuilder import mods2

DEBUG = False
NAME = "Modify Respec Cost"
DESCRIPTION = "Reduce the cost of respeccing Skill and Perk trees."
FILE = "settings/hp_settings/player_rewards.bin"
OPTIONS = [
    {
     "name": "Cost",
     "style": "slider",
     "min": 1.0,
     "max": 3500.0,
     "initial": 3500.0,
     "increment": 1,
     "note": "Cost is per point invested in the tree being respecced. Default cost to refund 2 points is $7000"
    }
]
PRESETS = [
  {
   "name": "Game Defaults",
   "options": [
     {"name": "cost", "value": 3500.0},
    ]
  },
  {
   "name": "Cheap",
   "options": [
     {"name": "cost", "value": 1.0},
    ]
  },
]

def format(options: dict) -> str:
  cost = int(options['cost'])
  return f"Modify Respec Cost (${cost})"

def process(options: dict) -> None:
  cost = options["cost"]
  # The game stores respec cost values in the StringData array
  # Massage our float value into a properly-formatted string for the destination
  cost_string = f"{cost:06.1f}"
  updates = [
    {
      # skillpoint_respec_price
      "coordinates": "B2",
      "sheet": "respec",
      "value": cost_string,
    },
    {
      # perkpoint_respec_price
      "coordinates": "B3",
      "sheet": "respec",
      "value": cost_string,
    },
  ]
  # "force=True" since we have two cells that point at the same value
  mods2.apply_coordinate_updates_to_file(FILE, updates, force=True)
