from modbuilder import mods, mods2

DEBUG = False
NAME = "Modify Animal Senses"
DESCRIPTION = "Modify how animals sense and respond to you. Threshold values determine when an animal enters and exits various behavioral states. The higher the threshold, the longer it takes to enter into that state. Duration values modify how long an animal stays in an elevated state. Detection values modify how sensitive animals are to your character's noise, smell, and visual presence."
FILE = "settings/hp_settings/animal_senses.bin"
WARNING = "This mod modifies dozens of values and takes more time to build than other mods. Mod Builder may appear to hang for a few seconds while applying these changes. Please be patient."
OPTIONS = [
  { "name": "Increase Attentiveness Threshold Percent", "min": 0, "max": 300, "default": 0, "increment": 10 },
  { "name": "Increase Alert Threshold Percent", "min": 0, "max": 300, "default": 0, "increment": 10 },
  { "name": "Increase Alarmed Threshold Percent", "min": 0, "max": 300, "default": 0, "increment": 10 },
  { "name": "Increase Defensive Threshold Percent", "min": 0, "max": 300, "default": 0, "increment": 10 },
  { "name": "Reduce Nervous Duration Percent", "min": 0, "max": 100, "default": 0, "increment": 1 },
  { "name": "Reduce Defensive Duration Percent", "min": 0, "max": 100, "default": 0, "increment": 1 },
  { "name": "Reduce Scent Detection Percent", "min": 0, "max": 100, "default": 0, "increment": 1 },
  { "name": "Reduce Vision Detection Percent", "min": 0, "max": 100, "default": 0, "increment": 1 },
  { "name": "Reduce Sound Detection Percent", "min": 0, "max": 100, "default": 0, "increment": 1 }
]

def format(options: dict) -> str:
  attentive_percent = int(options['increase_attentiveness_threshold_percent'])
  alert_percent = int(options['increase_alert_threshold_percent'])
  alarmed_percent = int(options['increase_alarmed_threshold_percent'])
  defensive_percent = int(options['increase_defensive_threshold_percent'])
  return f"Modify Animal Senses ({attentive_percent}%, {alert_percent}%, {alarmed_percent}%, {defensive_percent}%)"

def update_values_at_coordinates(options: dict) -> list[dict]:
  attentive_percent = 1 + options['increase_attentiveness_threshold_percent'] / 100
  alert_percent = 1 + options['increase_alert_threshold_percent'] / 100
  alarmed_percent = 1 + options['increase_alarmed_threshold_percent'] / 100
  defensive_percent = 1 + options['increase_defensive_threshold_percent'] / 100

  nervous_duration_percent = 1 - options['reduce_nervous_duration_percent'] / 100
  default_defensive_duration_percent = options['reduce_defensive_duration_percent'] if "reduce_defensive_duration_percent" in options else 0
  defensive_duration_percent = 1 - default_defensive_duration_percent / 100
  scent_multiplier = 1 - options['reduce_scent_detection_percent'] / 100
  vision_multiplier = 1 - options['reduce_vision_detection_percent'] / 100
  sound_multiplier = 1 - options['reduce_sound_detection_percent'] / 100

  sound_prone_cells = mods2.range_to_coordinates_list("B", 93, 95)
  sound_crouch_cells = mods2.range_to_coordinates_list("B", 98, 100)
  sound_stand_cells = mods2.range_to_coordinates_list("B", 103, 105)
  sound_run_cells = mods2.range_to_coordinates_list("B", 108, 110)
  sound_swim_cells = mods2.range_to_coordinates_list("B", 113, 116)
  sound_cells = sound_prone_cells + sound_crouch_cells + sound_stand_cells + sound_run_cells + sound_swim_cells

  vision_shadow_cells = mods2.range_to_coordinates_list("B", 39, 43)
  vision_prone_cells = mods2.range_to_coordinates_list("B", 45, 50)
  vision_crouch_cells = mods2.range_to_coordinates_list("B", 54, 59)
  vision_stand_cells = mods2.range_to_coordinates_list("B", 63, 68)
  vision_run_cells = mods2.range_to_coordinates_list("B", 72, 77)
  vision_swim_cells = mods2.range_to_coordinates_list("B", 81, 86)
  vision_cells = vision_shadow_cells + vision_prone_cells + vision_crouch_cells + vision_stand_cells + vision_run_cells + vision_swim_cells

  scent_prone_cells = mods2.range_to_coordinates_list("B", 119, 126)
  scent_crouch_cells = mods2.range_to_coordinates_list("B", 130, 137)
  scent_stand_cells = mods2.range_to_coordinates_list("B", 141, 148)
  scent_run_cells = mods2.range_to_coordinates_list("B", 152, 159)
  scent_swim_cells = mods2.range_to_coordinates_list("B", 163, 170)
  scent_cells = scent_prone_cells + scent_crouch_cells + scent_stand_cells + scent_run_cells + scent_swim_cells

  mods2.update_file_at_multiple_coordinates_with_value(FILE, "species_data", sound_cells, sound_multiplier, transform="multiply")
  mods2.update_file_at_multiple_coordinates_with_value(FILE, "species_data", vision_cells, vision_multiplier, transform="multiply")
  mods2.update_file_at_multiple_coordinates_with_value(FILE, "species_data", scent_cells, scent_multiplier, transform="multiply")

  return [
    {
      # attentive_enter_threshold
      "coordinates": "B4",
      "sheet": "species_data",
      "transform": "multiply",
      "value": attentive_percent
    },
    {
      # attentive_exit_threshold
      "coordinates": "B5",
      "sheet": "species_data",
      "transform": "multiply",
      "value": attentive_percent
    },
    {
      # alert_enter_threshold
      "coordinates": "B6",
      "sheet": "species_data",
      "transform": "multiply",
      "value": alert_percent
    },
    {
      # alert_exit_threshold
      "coordinates": "B7",
      "sheet": "species_data",
      "transform": "multiply",
      "value": alert_percent
    },
    {
      # alarmed_enter_threshold
      "coordinates": "B8",
      "sheet": "species_data",
      "transform": "multiply",
      "value": alarmed_percent
    },
    {
      # alarmed_exit_threshold
      "coordinates": "B9",
      "sheet": "species_data",
      "transform": "multiply",
      "value": alarmed_percent
    },
    {
      # defensive_enter_threshold
      "coordinates": "B10",
      "sheet": "species_data",
      "transform": "multiply",
      "value": defensive_percent
    },
    {
      # defensive_exit_threshold
      "coordinates": "B11",
      "sheet": "species_data",
      "transform": "multiply",
      "value": defensive_percent
    },
    {
      # nervous_min_duration
      "coordinates": "B12",
      "sheet": "species_data",
      "transform": "multiply",
      "value": nervous_duration_percent,
    },
    {
      # nervous_max_duration
      "coordinates": "B13",
      "sheet": "species_data",
      "transform": "multiply",
      "value": nervous_duration_percent
    },
    {
      # defensive_min_duration_easy
      "coordinates": "B14",
      "sheet": "species_data",
      "transform": "multiply",
      "value": defensive_duration_percent
    },
    {
      # defensive_min_duration_difficult
      "coordinates": "B15",
      "sheet": "species_data",
      "transform": "multiply",
      "value": defensive_duration_percent
    },
    {
      # defensive_max_duration_easy
      "coordinates": "B16",
      "sheet": "species_data",
      "transform": "multiply",
      "value": defensive_duration_percent
    },
    {
      # defensive_max_duration_difficult
      "coordinates": "B17",
      "sheet": "species_data",
      "transform": "multiply",
      "value": defensive_duration_percent
    },
  ]