DEBUG = True
NAME = "Enhanced Keen Eye"
DESCRIPTION = "Enables you to spot need zones and animal groups from lookup points. You must have the Keen Eye skill unlocked for this modification to take affect. Be careful not to increase the need zones or animal groups too high, or your computer may have performance issues."
FILE = "settings/hp_settings/player_skills.bin"
WARNING = 'Unlocking all Need Zones on a map can have a significant negative performance impact on the game. If you experience issues after revealing large areas of the map, disabling "Need Zone Icons" in the interface settings can help.'
OPTIONS = [
  { "name": "Cooldown Seconds", "min": 1, "max": 1800, "default": 1800, "initial": 10, "increment": 1 },
  { "name": "Zone Distance", "min": 500, "max": 990, "default": 500, "increment": 10 },
  { "name": "Min Number of Zones", "min": 2, "max": 99, "default": 2, "increment": 1 },
  { "name": "Max Number of Zones", "min": 2, "max": 99, "default": 2, "increment": 1 },
  { "name": "Animal Distance", "min": 500, "max": 990, "default": 500, "increment": 10 },
  { "name": "Min Number of Animals", "min": 1, "max": 99, "default": 1, "increment": 1 },
  { "name": "Max Number of Animals", "min": 3, "max": 99, "default": 3, "increment": 1 },
]

def format_options(options: dict) -> str:
  cool = options["cooldown_seconds"]
  max_zones = options["max_number_of_zones"]
  return f"Enhanced Keen Eye ({int(cool)}s, {int(max_zones)} zones)"

def update_values_at_offset(options: dict) -> list[dict]:
  cool = float(options["cooldown_seconds"])
  zone_distance = int(options["zone_distance"])
  min_zones = int(options["min_number_of_zones"])
  max_zones = int(options["max_number_of_zones"])
  animal_distance = int(options["animal_distance"])
  min_animals = int(options["min_number_of_animals"])
  max_animals = int(options["max_number_of_animals"])

  return [
    {
      "offset": 21912,
      "value": f"show_need_zone_in_range_on_map({zone_distance:>3},{min_zones:>2},{max_zones:>2})"
    },
    {
      "offset": 21960,
      "value": f"show_need_zone_in_range_on_map({zone_distance:>3},{min_zones:>2},{max_zones:>2}), show_animal_group_in_range_on_map({animal_distance:>3},{min_animals:>2},{max_animals:>2})"
    },
    {
      "offset": 34472,
      "value": cool
    }
  ]
