from modbuilder import mods2

DEBUG = False
NAME = "Modify Player Traits"
DESCRIPTION = "Change the character's default attributes. These settings can enable abilities from Perks and Skills trees without needing to spend points."
WARNING = "These values will be overridden if you invest in the related Skill/Perks"
FILE = "settings/hp_settings/player_skills.bin"
OPTIONS = [
  { "name": "Base Health", "min": 100, "max": 9999, "default": 1000, "initial": 1000, "increment": 1, "note": '"Hardened" skill' },
  { "name": "Carry Capacity", "min": 1, "max": 999, "default": 20, "initial": 20, "increment": 1, "note": '"Pack Mule" skill' },
  { "name": "Reduce Recoil Percent", "min": 0, "max": 100, "default": 0, "initial": 0, "increment": 1, "note": '"Recoil Management" shotgun perk' },
  { "name": "Recoil Recovery Speed", "min": 1.0, "max": 9.9, "default": 1.0, "initial": 1.0, "increment": 0.1, "note": '"Recoil Management" shotgun perk' },
  # { "name": "Raise Weapon Speed", "min": 0.0, "max": 10.0, "default": 0.75, "initial": 0.75, "increment": 0.25, "note": '"Fast Shouldering" shotgun perk' },
  { "name": "Clue Detection Range", "min": 1, "max": 99, "default": 20, "initial": 20, "increment": 1, "note": '"Locate Tracks" skill' },
  { "name": "Clue Direction Angle", "min": 1, "max": 90, "default": 90, "initial": 90, "increment": 1, "note": 'Locate Tracks" skill. Smaller size = more accurate indicator.' },
  { "name": "Show Clue Trails on Map", "style": "boolean", "default": False, "initial": False, "note": '"Connect The Dots" skill' },
  { "name": "Spot Duration", "min": 1, "max": 999, "default": 2, "initial": 2, "increment": 1, "note": '"Tag" skill' },
  { "name": "Multiple Spot Count", "min": 1, "max": 99, "default": 1, "initial": 1, "increment": 1, "note": '"Tag" skill' },
  { "name": "Spot Animals With Scope", "style": "boolean", "default": False, "initial": False, "note": '"Sight Spotting" skill' },
  { "name": "Reload While Running", "style": "boolean", "default": False, "initial": False, "note": '"Sprint & Load" handgun perk' },
  { "name": "Reload While Aiming", "style": "boolean", "default": False, "initial": False, "note": '"Muscle Memory" rifle perk tier 1' },
]

def format(options: dict) -> str:
  trait_details = []

  base_health = int(options["base_health"])
  if base_health != 1000:
    trait_details.append(f"{base_health} HP")

  carry_capacity = int(options["carry_capacity"])
  if carry_capacity != 20:
    trait_details.append(f"{carry_capacity} KG")

  recoil_percent = options["reduce_recoil_percent"]
  recoil_speed = options["recoil_recovery_speed"]
  if recoil_percent > 0 or recoil_speed > 1:
    trait_details.append(f"-{recoil_percent}% + {recoil_speed} recoil")

  # if options["raise_weapon_speed"] > 0.75:
  #   trait_details.append(f"{options['raise_weapon_speed']}x shouldering")

  clue_range = int(options["clue_detection_range"])
  clue_direction_indicator_size = int(options["clue_direction_angle"])
  if clue_range != 20 or clue_direction_indicator_size < 90:
    trait_details.append(f"{clue_range}m + {clue_direction_indicator_size}° clues")

  spot_duration = int(options["spot_duration"])
  spot_count = int(options["multiple_spot_count"])
  if spot_duration != 2 or spot_count != 1:
    trait_details.append(f"{spot_duration}s + {spot_count} spots")

  if options["spot_animals_with_scope"]:
    trait_details.append(f"scope spot")

  if options["reload_while_running"]:
    trait_details.append(f"run reload")

  if options["reload_while_aiming"]:
    trait_details.append(f"aim reload")

  return f"Modify Player Traits ({", ".join(trait_details)})"

def process(options: dict) -> None:
  # values are padded with `.ljust(XX, '\x00')` to ensure they overwrite the original values with null data
  sheet = "skill_component_descriptions"
  updates = []

  carry_capacity = options['carry_capacity']
  if carry_capacity != 20:
    # "set_player_carry_capacity" shares a value "(20.0)" with "audio_clue_accuracy"
    # Shuffle some data and overwrite the unused "thermal" value in the array
    # 1. Point the "thermal" cell at a different definition (piggyback on "(0,0,0)" value from "show_animal_in_group_range_on_map")
    updates.append({"sheet": sheet, "coordinates": "B3", "value": "(0,0,0)"})
    # 2. Now if we write to "set_player_carry_capacity" we can overwrite the unused StringData value
    updates.append({"sheet": sheet, "coordinates": "B44", "value": f"({options['carry_capacity']})".ljust(18, '\x00')})

  updates.append({"sheet": sheet, "coordinates": "B47", "value": f"({options['base_health']})".ljust(8, '\x00')})

  recoil_percent = 1.0 - ( options["reduce_recoil_percent"] / 100 )
  recoil_speed = options["recoil_recovery_speed"]
  updates.append({"sheet": sheet, "coordinates": "B30", "value": f"({recoil_percent}, {recoil_speed})"})

  # weapon_speed = options["raise_weapon_speed"]
  # if weapon_speed > 0.75:
  #   weapon_speed
  #   f"(weapon_category_handguns, {weapon_speed},weapon_category_rifles, {weapon_speed},weapon_category_bows, {weapon_speed},weapon_category_shotguns, {weapon_speed})".ljust(144, '\x00')
  #   updates.append({"sheet": sheet, "coordinates": "B51", "value": weapon_speed})

  clue_spawn = options["clue_detection_range"]
  clue_despawn = round(clue_spawn + 5)  # despawn range should be longer to prevent flickering
  clue_despawn = min(clue_despawn, 99)  # still capped at 99
  clue_range = f"({clue_spawn:.1f}, {clue_despawn:.1f})"
  updates.append({"sheet": sheet, "coordinates": "B8", "value": clue_range.ljust(12, '\x00')})

  clue_angle = int(options["clue_direction_angle"])
  if clue_angle < 90:
    clue_cone = "WIDE"
    if clue_angle < 70:
      clue_cone = "MEDIUM"
    if clue_angle < 45:
      clue_cone = "NARROW"
    clue_indicator = f"({clue_cone}, {clue_angle})".ljust(12, '\x00')
    updates.append({"sheet": sheet, "coordinates": "B7", "value": clue_indicator.ljust(12, '\x00')})

  if options["show_clue_trails_on_map"]:
    updates.append({"sheet": sheet, "coordinates": "B26", "value": "(true)"})

  updates.append({"sheet": sheet, "coordinates": "B23", "value": f"({options["spot_duration"]}, {int(options["multiple_spot_count"])})".ljust(16, '\x00')})

  if options["spot_animals_with_scope"]:
    updates.append({"sheet": sheet, "coordinates": "B29", "value": "(true)"})

  if options["reload_while_running"]:
    updates.append({"sheet": sheet, "coordinates": "B70", "value": "(true)"})

  if options["reload_while_aiming"]:
    updates.append({"sheet": sheet, "coordinates": "B22", "value": "(1.0)"})

  mods2.apply_coordinate_updates_to_file(FILE, updates)
