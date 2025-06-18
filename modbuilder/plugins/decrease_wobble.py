from modbuilder import mods2

DEBUG = False
NAME = "Decrease Wobble"
DESCRIPTION = "Reduce the amount of wobble when looking through the scope."
FILE = "editor/entities/hp_characters/main_characters/elmer/elmer_movement.mtunec"
OPTIONS = [
  { "name": "Reduce Stand Percent", "min": 0, "max": 100, "default": 0, "increment": 5 },
  { "name": "Reduce Crouch Percent", "min": 25, "max": 100, "default": 25, "increment": 5 },
  { "name": "Reduce Prone Percent", "min": 50, "max": 100, "default": 50, "increment": 5 }
]
PRESETS = [
  { "name": "Game Defaults", "options": [
    { "name": "reduce_stand_percent", "value": 0 },
    { "name": "reduce_crouch_percent", "value": 25 },
    { "name": "reduce_prone_percent", "value": 50 }
  ]},
  { "name": "Recommended", "options": [
    { "name": "reduce_stand_percent", "value": 25 },
    { "name": "reduce_crouch_percent", "value": 70 },
    { "name": "reduce_prone_percent", "value": 100 }
  ]}
]

def format(options: dict) -> str:
  stand_percent = options['reduce_stand_percent']
  crouch_percent = options['reduce_crouch_percent']
  prone_percent = options['reduce_prone_percent']
  return f"Decrease Wobble (-{int(stand_percent)}% stand, -{int(crouch_percent)}% crouch, -{int(prone_percent)}% prone)"

def update_values_at_offset(options: dict) -> None:
  movement_file = mods2.deserialize_adf(FILE)
  weapon_settings = movement_file.table_instance_full_values[0].value["FpsSettings"].value["WeaponSkillSettings"].value
  updates = [
    {
      "offset": weapon_settings["StandingWoobleModifier"].data_offset,
      "value": round(1.0 - options['reduce_stand_percent'] / 100, 1),
    },
    {
      "offset": weapon_settings["CrouchWoobleModifier"].data_offset,
      "value": round(1.0 - options['reduce_crouch_percent'] / 100, 1),
    },
    {
      "offset": weapon_settings["CrawlWoobleModifier"].data_offset,
      "value": round(1.0 - options['reduce_prone_percent'] / 100, 1),
    },
  ]
  return updates
