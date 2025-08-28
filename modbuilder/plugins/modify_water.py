from modbuilder import mods, mods2

DEBUG=False
NAME = "Modify Water"
DESCRIPTION = "This mod allows you to walk underwater."
WARNING = "Currently bugged. Movement speed in water is incredibly fast and you may be launched upward upon reaching shore. Use Modify Skills and increase Impact Resistance to keep yourself alive"
BASE_WATER_FILE = "settings/hp_settings/player_deep_water_handling.bin"
OPTIONS = [
    {
     "name": "Max Depth",
     "style": "slider",
     "min": 1.0,
     "max": 60.0,
     "initial": 1.0,
     "increment": 1.0,
     "note": "how deep you can go before you cannot move",
    },
    {
     "name": "Player Movement",
     "style": "slider",
     "min": -1000.0,
     "max": 0.0,
     "initial": -90,
     "increment": 0.5,
     "note": "how much player slows down in water",
    },
]
PRESETS = [
  {
   "name": "Game Defaults",
   "options": [
     {"name": "max_depth", "value": 1.0},
     {"name": "player_movement", "value": -90.0},
    ]
  },
  {
   "name": "Recommended",
   "options": [
     {"name": "max_depth", "value": 28.0},
     {"name": "player_movement", "value": -5.0},
    ]
  },
]

def format_options(options: dict) -> str:
  max_depth = int(options["max_depth"])
  player_movement = int(options["player_movement"])
  return f"Water ({max_depth} depth, {player_movement} speed)"

def get_files(options: dict) -> list[str]:
  return [BASE_WATER_FILE]

def process(options: dict) -> None:
  depth_cells = ["B2","B3","B4","B5"]
  # "force=True" since we have two cells that point at the same value
  mods2.update_file_at_multiple_coordinates_with_value(BASE_WATER_FILE, "Sheet1", depth_cells, options["max_depth"], force = True)
