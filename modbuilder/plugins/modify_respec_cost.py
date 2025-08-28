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

def format_options(options: dict) -> str:
  cost = int(options['cost'])
  return f"Modify Respec Cost (${cost})"

def process(options: dict) -> None:
  cost_string = str(options["cost"])  # The game stores respec cost in the StringData array
  respec_cost_cells = ["B2", "B3"]
  # force=True because these are the only two cells that point at that value
  mods2.update_file_at_multiple_coordinates_with_value(FILE, "respec", respec_cost_cells, cost_string, force=True)
