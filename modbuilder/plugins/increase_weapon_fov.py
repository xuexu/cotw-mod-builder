import FreeSimpleGUI as sg

from modbuilder import mods, mods2

DEBUG = False
NAME = "Increase Weapon FOV"
DESCRIPTION = 'Increase the first-person field of view when holding a weapon, effectively zooming out the camera so you can see more of your weapon skin. Includes additional controls for scope distance, iron sights distance, and mouse acceleration.'
WARNING = 'The first-person camera only renders the player\'s arms and weapon. Settings higher than ~60 may show "floating" arms with no body when holding some weapons.'

FIRST_PERSON_FOV_FILE = "editor/entities/cameras/default_first_person.ctunec"
PRONE_FOV_FILE = "editor/entities/cameras/prone_first_person.ctunec"
AIM_SCOPE_FOV_FILE = "editor/entities/cameras/aim_scope_first_person.ctunec"
IRON_SIGHT_FOV_FILE = "editor/entities/cameras/iron_sight_first_person.ctunec"
IRON_SIGHT_PRONE_FOV_FILE = "editor/entities/cameras/iron_sight_prone_first_person.ctunec"

FIRST_PERSON_FOV_DEFAULT = mods2.deserialize_adf(FIRST_PERSON_FOV_FILE, modded=False).table_instance_full_values[0].value["ForeGroundFOV"].value
SCOPE_FOV_DEFAULT = mods2.deserialize_adf(AIM_SCOPE_FOV_FILE, modded=False).table_instance_full_values[0].value["ForeGroundFOV"].value
IRON_SIGHT_FOV_DEFAULT = mods2.deserialize_adf(IRON_SIGHT_FOV_FILE, modded=False).table_instance_full_values[0].value["ForeGroundFOV"].value

def get_option_elements() -> sg.Column:
  layout = [
    [sg.T("First-Person Weapon FOV: "), sg.Slider((15, 90), FIRST_PERSON_FOV_DEFAULT, 1, orientation="h", k="first-person_weapon_fov", s=(50,20), p=((10,0),(0,5)))],
    [sg.T("Weapon Scope Distance: "), sg.Slider((15, 90), SCOPE_FOV_DEFAULT, 0.5, orientation="h", k="weapon_scope_distance", s=(50,20), p=((10,0),(0,5)))],
    [sg.T("Weapon Iron Sight Distance: "), sg.Slider((15, 90), IRON_SIGHT_FOV_DEFAULT, 0.5, orientation="h", k="weapon_iron_sight_distance", s=(50,20), p=((10,0),(0,5)))],
    [
      sg.Checkbox("Sights Use FOV from Game Settings", False, k="use_game_settings_fov", enable_events=True),
      sg.T('Force scopes + iron sights to use the "Field of View" value found in the in-game Video settings', font="_ 12 italic", text_color="orange"),
    ],
    [
      sg.Checkbox("Disable Scope Acceleration", False, k="disable_scope_acceleration"),
      sg.T("Removes input acceleration while aiming down sights. Do NOT check this if you play the game with a controller", font="_ 12 italic", text_color="orange"),
    ],
  ]
  return sg.Column(layout)

def handle_event(event: str, window: sg.Window, values: dict) -> None:
  if event == "use_game_settings_fov":
    for slider_key in ["weapon_scope_distance", "weapon_iron_sight_distance"]:
      # FreeSimpleGUI does not change the slider appearance when disabled
      # Modify the underlying Tkinter widget
      slider = window[slider_key]
      slider.update(disabled=values["use_game_settings_fov"])
      tk_slider = slider.Widget
      if values["use_game_settings_fov"]:
        tk_slider["troughcolor"] = "white"
      else:
        tk_slider["troughcolor"] = "#705e52"  # color for our theme: print(tk_slider["troughcolor"])

def add_mod(window: sg.Window, values: dict) -> dict:
  return {
    "key": "increase_weapon_fov",
    "invalid": None,
    "options": {
      "first-person_weapon_fov": values["first-person_weapon_fov"],
      "weapon_scope_distance": values["weapon_scope_distance"],
      "weapon_iron_sight_distance": values["weapon_iron_sight_distance"],
      "disable_scope_acceleration": values["disable_scope_acceleration"],
      "use_game_settings_fov": values["use_game_settings_fov"],
    }
  }

def map_options(options: dict) -> dict:
  return {
    "first-person_weapon_fov": options.get("first-person_weapon_fov", FIRST_PERSON_FOV_DEFAULT),
    "weapon_scope_distance": options.get("weapon_scope_distance", SCOPE_FOV_DEFAULT),
    "weapon_iron_sight_distance": options.get("weapon_iron_sight_distance", IRON_SIGHT_FOV_DEFAULT),
    "disable_scope_acceleration": options.get("disable_scope_acceleration", False),
    "use_game_settings_fov": options.get("use_game_settings_fov", False),
  }

def format_options(options: dict) -> str:
  options = map_options(options)
  weapon_fov = options["first-person_weapon_fov"]
  options_text = f"Weapon: {int(weapon_fov)}"
  if options["use_game_settings_fov"]:
    options_text += ", Use Game FOV for Sights"
  else:
    scope_fov = options["weapon_scope_distance"]
    iron_sight_fov = options["weapon_iron_sight_distance"]
    options_text += f", Scope: {scope_fov:.1f}, Iron Sight: {iron_sight_fov:.1f}"
  accel = "Disabled" if options["disable_scope_acceleration"] else "Enabled"
  options_text += f", Acceleration: {accel}"
  return f"Increase Weapon FOV ({options_text})"

def handle_key(mod_key: str) -> bool:
  return mod_key == "increase_weapon_fov"

def get_files(options: dict) -> list[str]:
  options = map_options(options)
  fov_files = []
  if options["first-person_weapon_fov"] != FIRST_PERSON_FOV_DEFAULT:
    fov_files.extend([FIRST_PERSON_FOV_FILE, PRONE_FOV_FILE])
  if options["weapon_scope_distance"] != SCOPE_FOV_DEFAULT or options["disable_scope_acceleration"] or options["use_game_settings_fov"]:
    fov_files.append(AIM_SCOPE_FOV_FILE)
  if options["weapon_iron_sight_distance"] != IRON_SIGHT_FOV_DEFAULT or options["disable_scope_acceleration"] or options["use_game_settings_fov"]:
    fov_files.extend([IRON_SIGHT_FOV_FILE, IRON_SIGHT_PRONE_FOV_FILE])
  return fov_files

def process(options: dict) -> None:
  options = map_options(options)

  if options["first-person_weapon_fov"] != FIRST_PERSON_FOV_DEFAULT:
    for file in [FIRST_PERSON_FOV_FILE, PRONE_FOV_FILE]:
      weapon_fov_file = mods2.deserialize_adf(file)
      weapon_fov = weapon_fov_file.table_instance_full_values[0].value["ForeGroundFOV"]
      updates = [{"offset": weapon_fov.data_offset, "value": float(options["first-person_weapon_fov"])}]
      mods.apply_updates_to_file(file, updates)

  if options["weapon_scope_distance"] != SCOPE_FOV_DEFAULT or options["disable_scope_acceleration"] or options["use_game_settings_fov"]:
    scope_file = mods2.deserialize_adf(AIM_SCOPE_FOV_FILE)
    scope_fov = scope_file.table_instance_full_values[0].value["ForeGroundFOV"]
    updates = [{"offset": scope_fov.data_offset, "value": float(options["weapon_scope_distance"])}]
    if options["disable_scope_acceleration"]:
      input_acceleration = scope_file.table_instance_full_values[0].value["InputAcceleration"]
      input_acceleration_start_at = scope_file.table_instance_full_values[0].value["InputAccelerationStartAt"]
      updates.extend([
        {"offset": input_acceleration.data_offset, "value": 0.0},
        {"offset": input_acceleration_start_at.data_offset, "value": 0.0}
      ])
    if options["use_game_settings_fov"]:
      game_settings_world_fov = scope_file.table_instance_full_values[0].value["UseGameSettingsWorldFov"]
      updates.append({"offset": game_settings_world_fov.data_offset, "value": 1, "type": "uint8"})
    mods.apply_updates_to_file(AIM_SCOPE_FOV_FILE, updates)

  if options["weapon_iron_sight_distance"] != IRON_SIGHT_FOV_DEFAULT or options["disable_scope_acceleration"] or options["use_game_settings_fov"]:
    for file in [IRON_SIGHT_FOV_FILE, IRON_SIGHT_PRONE_FOV_FILE]:
      iron_sight_file = mods2.deserialize_adf(file)
      iron_sight_fov = iron_sight_file.table_instance_full_values[0].value["ForeGroundFOV"]
      updates = [
        {"offset": iron_sight_fov.data_offset, "value": float(options["weapon_iron_sight_distance"])}
      ]
      if options["disable_scope_acceleration"]:
        input_acceleration = iron_sight_file.table_instance_full_values[0].value["InputAcceleration"]
        input_acceleration_start_at = iron_sight_file.table_instance_full_values[0].value["InputAccelerationStartAt"]
        updates.extend([
          {"offset": input_acceleration.data_offset, "value": 0.0},
          {"offset": input_acceleration_start_at.data_offset, "value": 0.0}
        ])
      if options["use_game_settings_fov"]:
        game_settings_world_fov = iron_sight_file.table_instance_full_values[0].value["UseGameSettingsWorldFov"]
        updates.append({"offset": game_settings_world_fov.data_offset, "value": 1, "type": "uint8"})
      mods.apply_updates_to_file(file, updates)
