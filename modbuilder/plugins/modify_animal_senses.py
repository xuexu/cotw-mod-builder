from modbuilder import mods, mods2

DEBUG = False
NAME = "Modify Animal Senses"
DESCRIPTION = "Modify how animals sense and respond to you. Threshold = time until an animal enters/exits behavioral state. Duration = how long an animal stays in an elevated state. Detection = how sensitive animals are to your character's noise, smell, and visual presence. Distances are in meters."
ANIMAL_SENSES_FILE = "settings/hp_settings/animal_senses.bin"
AI_FILE = "ai/aisystem.aisystunec"
OPTIONS = [
  { "name": "Tent Detection Distance", "min": 0, "max": 1000, "default": 500, "initial": 500, "increment": 50, "note": "Animals near the tent will spook when you fast travel." },
  { "name": "Weapon Fire Detection Distance", "min": 0, "max": 1000, "default": 300, "initial": 300, "increment": 50, "note": "Adjusts base value. Bows/Pistols with shorter ranges will be scaled." },
  { "name": "Increase Attentiveness Threshold Percent", "min": 0, "max": 300, "default": 0, "increment": 10 },
  { "name": "Increase Alert Threshold Percent", "min": 0, "max": 300, "default": 0, "increment": 10 },
  { "name": "Increase Alarmed Threshold Percent", "min": 0, "max": 300, "default": 0, "increment": 10 },
  { "name": "Increase Defensive Threshold Percent", "min": 0, "max": 300, "default": 0, "increment": 10 },
  { "name": "Reduce Nervous Duration Percent", "min": 0, "max": 100, "default": 0, "increment": 1 },
  { "name": "Reduce Defensive Duration Percent", "min": 0, "max": 100, "default": 0, "increment": 1 },
  { "name": "Reduce Scent Detection Percent", "min": 0, "max": 100, "default": 0, "increment": 1 },
  { "name": "Reduce Vision Detection Percent", "min": 0, "max": 100, "default": 0, "increment": 1 },
  { "name": "Reduce Sound Detection Percent", "min": 0, "max": 100, "default": 0, "increment": 1 },
]

def format(options: dict) -> str:
  senses_details = []

  tent_distance = options.get("tent_detection_distance")
  if tent_distance is not None:
    senses_details.append(f"{int(tent_distance)}m tent spook")

  weapon_fire_distance = options.get("weapon_fire_detection_distance")
  if weapon_fire_distance is not None:
   senses_details.append(f"{int(weapon_fire_distance)}m weapon fire")

  attentive_percent = int(options['increase_attentiveness_threshold_percent'])
  alert_percent = int(options['increase_alert_threshold_percent'])
  alarmed_percent = int(options['increase_alarmed_threshold_percent'])
  defensive_percent = int(options['increase_defensive_threshold_percent'])
  senses_details.append(f"+{attentive_percent}% attent., +{alert_percent}% alert, +{alarmed_percent}% alarm, +{defensive_percent}% defense")
  formatted_text =  f"Modify Animal Senses ({", ".join(senses_details)})"
  return formatted_text

def get_files(options: dict) -> list[str]:
  files = [ANIMAL_SENSES_FILE]
  if options.get("tent_detection_distance") is not None:
    files.append(AI_FILE)
  return files

def process(options: dict) -> list[dict]:
  # We're modifying nearly 100 cells in a file with 62K+ cells
  # There are ~350 float values in the file already
  # Pass `skip_add_data=True` to our mods2 functions to save a ton of time
  # This will just re-use the closest existing value in the file instead of
  #  checking every cell for an unused value to overwrite or adding hundreds of new values

  vision_shadow_cells = mods2.range_to_coordinates_list("B", 39, 43)
  vision_prone_cells = mods2.range_to_coordinates_list("B", 45, 50)
  vision_crouch_cells = mods2.range_to_coordinates_list("B", 54, 59)
  vision_stand_cells = mods2.range_to_coordinates_list("B", 63, 68)
  vision_run_cells = mods2.range_to_coordinates_list("B", 72, 77)
  vision_swim_cells = mods2.range_to_coordinates_list("B", 81, 86)
  vision_cells = vision_shadow_cells + vision_prone_cells + vision_crouch_cells + vision_stand_cells + vision_run_cells + vision_swim_cells
  vision_multiplier = 1 - options['reduce_vision_detection_percent'] / 100
  mods2.update_file_at_multiple_coordinates_with_value(ANIMAL_SENSES_FILE, "species_data", vision_cells, vision_multiplier, transform="multiply", skip_add_data=True)

  sound_prone_cells = mods2.range_to_coordinates_list("B", 93, 95)
  sound_crouch_cells = mods2.range_to_coordinates_list("B", 98, 100)
  sound_stand_cells = mods2.range_to_coordinates_list("B", 103, 105)
  sound_run_cells = mods2.range_to_coordinates_list("B", 108, 110)
  sound_swim_cells = mods2.range_to_coordinates_list("B", 113, 116)
  sound_cells = sound_prone_cells + sound_crouch_cells + sound_stand_cells + sound_run_cells + sound_swim_cells
  sound_multiplier = 1 - options['reduce_sound_detection_percent'] / 100
  mods2.update_file_at_multiple_coordinates_with_value(ANIMAL_SENSES_FILE, "species_data", sound_cells, sound_multiplier, transform="multiply", skip_add_data=True)

  scent_prone_cells = mods2.range_to_coordinates_list("B", 119, 126)
  scent_crouch_cells = mods2.range_to_coordinates_list("B", 130, 137)
  scent_stand_cells = mods2.range_to_coordinates_list("B", 141, 148)
  scent_run_cells = mods2.range_to_coordinates_list("B", 152, 159)
  scent_swim_cells = mods2.range_to_coordinates_list("B", 163, 170)
  scent_cells = scent_prone_cells + scent_crouch_cells + scent_stand_cells + scent_run_cells + scent_swim_cells
  scent_multiplier = 1 - options['reduce_scent_detection_percent'] / 100
  mods2.update_file_at_multiple_coordinates_with_value(ANIMAL_SENSES_FILE, "species_data", scent_cells, scent_multiplier, transform="multiply", skip_add_data=True)

  attentive_percent = 1 + options['increase_attentiveness_threshold_percent'] / 100
  mods2.update_file_at_multiple_coordinates_with_value(ANIMAL_SENSES_FILE, "species_data", ["B4", "B5"], attentive_percent, transform="multiply", skip_add_data=True)

  alert_percent = 1 + options['increase_alert_threshold_percent'] / 100
  mods2.update_file_at_multiple_coordinates_with_value(ANIMAL_SENSES_FILE, "species_data", ["B6", "B7"], alert_percent, transform="multiply", skip_add_data=True)

  alarmed_percent = 1 + options['increase_alarmed_threshold_percent'] / 100
  mods2.update_file_at_multiple_coordinates_with_value(ANIMAL_SENSES_FILE, "species_data", ["B8", "B9"], alarmed_percent, transform="multiply", skip_add_data=True)

  defensive_percent = 1 + options['increase_defensive_threshold_percent'] / 100
  mods2.update_file_at_multiple_coordinates_with_value(ANIMAL_SENSES_FILE, "species_data", ["B10", "B11"], defensive_percent, transform="multiply", skip_add_data=True)

  nervous_duration_percent = 1 - options['reduce_nervous_duration_percent'] / 100
  mods2.update_file_at_multiple_coordinates_with_value(ANIMAL_SENSES_FILE, "species_data", ["B12", "B13"], nervous_duration_percent, transform="multiply", skip_add_data=True)

  defensive_duration_percent = 1 - options.get('reduce_defensive_duration_percent', 0) / 100
  mods2.update_file_at_multiple_coordinates_with_value(ANIMAL_SENSES_FILE, "species_data", ["B14", "B15", "B16", "B17"], defensive_duration_percent, transform="multiply", skip_add_data=True)

  tent_distance = options.get("tent_detection_distance")
  if tent_distance is not None:
    mods.update_file_at_offset(AI_FILE, 800, tent_distance)

  weapon_fire_distance = options.get("weapon_fire_detection_distance")
  if weapon_fire_distance is not None:
    weapon_fire_distance_multiplier = weapon_fire_distance / 300  # default range
    weapon_fire_coordinates = mods2.get_coordinates_range_from_file(ANIMAL_SENSES_FILE, "weapon_data", rows=(3, 4), cols=("B", None))
    mods2.update_file_at_multiple_coordinates_with_value(ANIMAL_SENSES_FILE, "weapon_data", weapon_fire_coordinates, weapon_fire_distance_multiplier, transform="multiply", skip_add_data=True)
