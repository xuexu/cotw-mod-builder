from modbuilder import mods2

DEBUG = False
NAME = "Increase Speed"
DESCRIPTION = "Increase the movement speed of the player when standing, crouching, and lying prone. The sprint multiplier is a multiplier of a multiplier, so only small adjustments are needed."
FILE = "editor/entities/hp_characters/main_characters/elmer/elmer_movement.mtunec"
OPTIONS = [
  { "name": "Stand Speed Multiplier", "min": 1.0, "max": 20.0, "default": 1, "increment": 0.1 },
  { "name": "Stand Sprint Speed Multiplier", "min": 1.0, "max": 3.0, "default": 1, "increment": 0.1 },
  { "name": "Crouch Speed Multiplier", "min": 1.0, "max": 20.0, "default": 1, "increment": 0.1 },
  { "name": "Crouch Sprint Speed Multiplier", "min": 1.0, "max": 3.0, "default": 1, "increment": 0.1 },
  { "name": "Prone Speed Multiplier", "min": 1.0, "max": 20.0, "default": 1, "increment": 0.1 },
  { "name": "Prone Sprint Speed Multiplier", "min": 1.0, "max": 3.0, "default": 1, "increment": 0.1 },
  { "name": "Jump Speed Multiplier", "min": 1.0, "max": 20.0, "default": 1, "increment": 0.1, "note": "TIP: Use the Impact Resistance skill to reduce falling damage" }
]

def format_options(options: dict) -> str:
  stand_multiplier = options['stand_speed_multiplier']
  stand_sprint_multiplier = options['stand_sprint_speed_multiplier']
  crouch_multiplier = options['crouch_speed_multiplier']
  crouch_sprint_multiplier = options['crouch_sprint_speed_multiplier']
  prone_multiplier = options['prone_speed_multiplier']
  prone_sprint_multiplier = options['prone_sprint_speed_multiplier']
  return f"Increase Speed ({round(stand_multiplier, 1)}/{round(stand_sprint_multiplier, 1)}x, {round(crouch_multiplier, 1)}/{round(crouch_sprint_multiplier, 1)}x, {round(prone_multiplier, 1)}/{round(prone_sprint_multiplier, 1)}x)"

def update_values_at_offset(options: dict) -> None:
  movement_file = mods2.deserialize_adf(FILE)
  fps_settings = movement_file.table_instance_full_values[0].value["FpsSettings"].value
  stand_multiplier = options['stand_speed_multiplier']
  crouch_multiplier = options['crouch_speed_multiplier']
  prone_multiplier = options['prone_speed_multiplier']
  stand_sprint_multiplier = options['stand_sprint_speed_multiplier']
  crouch_sprint_multiplier = options['crouch_sprint_speed_multiplier']
  prone_sprint_multiplier = options['prone_sprint_speed_multiplier']
  jump_multiplier = options['jump_speed_multiplier']

  updates = [
    # Gamepad settings
    {
      "offset": fps_settings["GamepadStanceStandSpeedModifier"].data_offset,
      "transform": "multiply",
      "value": stand_multiplier
    },
    {
      "offset": fps_settings["GamepadStanceStandSprintSpeedModifier"].data_offset,
      "transform": "multiply",
      "value": stand_sprint_multiplier
    },
    {
      "offset": fps_settings["GamepadStanceCrouchSpeedModifier"].data_offset,
      "transform": "multiply",
      "value": crouch_multiplier
    },
    {
      "offset": fps_settings["GamepadStanceCrouchSprintModifier"].data_offset,
      "transform": "multiply",
      "value": crouch_sprint_multiplier
    },
    {
      "offset": fps_settings["GamepadStanceProneSpeedModifier"].data_offset,
      "transform": "multiply",
      "value": prone_multiplier
    },
    {
      "offset": fps_settings["GamepadStanceProneSprintModifier"].data_offset,
      "transform": "multiply",
      "value": prone_sprint_multiplier
    },
    # Keyboard settings
    {
      "offset": fps_settings["KeyboardStanceStandSpeedModifier"].data_offset,
      "transform": "multiply",
      "value": stand_multiplier
    },
    {
      "offset": fps_settings["KeyboardStanceStandSprintSpeedModifier"].data_offset,
      "transform": "multiply",
      "value": stand_sprint_multiplier
    },
    {
      "offset": fps_settings["KeyboardStanceCrouchSpeedModifier"].data_offset,
      "transform": "multiply",
      "value": crouch_multiplier
    },
    {
      "offset": fps_settings["KeyboardStanceCrouchSprintModifier"].data_offset,
      "transform": "multiply",
      "value": crouch_sprint_multiplier
    },
    {
      "offset": fps_settings["KeyboardStanceProneSpeedModifier"].data_offset,
      "transform": "multiply",
      "value": prone_multiplier
    },
    {
      "offset": fps_settings["KeyboardStanceProneSprintModifier"].data_offset,
      "transform": "multiply",
      "value": prone_sprint_multiplier
    },
    # Jump settings
    {
      "offset": fps_settings["JumpSpeed"].data_offset,
      "transform": "multiply",
      "value": jump_multiplier
    }
  ]

  return updates
