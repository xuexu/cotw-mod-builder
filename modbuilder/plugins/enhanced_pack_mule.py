DEBUG = True
NAME = "Enhanced Pack Mule"
DESCRIPTION = "Increases the weight you can carry. You must have the Pack Mule skill unlocked for this modification to take affect."
FILE = "settings/hp_settings/player_skills.bin"
OPTIONS = [
  { "name": "Weight", "min": 24.0, "max": 99.9, "default": 23.0, "initial": 99.9, "increment": 0.1 }
]

def format_options(options: dict) -> str:
  return f"Enhanced Pack Mule ({options['weight']}kg)"

def update_value_at_coordinates(options: dict) -> list[dict]:
  updated_value = options['weight']
  return [
    {
      # skill_03_10, Effects Level 1
      "coordinates": "G11",
      "sheet": "skills_strategic",
      "value": f"set_player_carry_capacity({updated_value})",
    }
  ]
