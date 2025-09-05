from modbuilder import mods, mods2

DEBUG = False
NAME = "Modify ATV"
DESCRIPTION = "Allows you to modify the performance of the ATV (all colors). The top speed is not exact, since the acceleration settings will slightly change the top speed. Higher top speeds may benefit from higher acceleration settings."
OPTIONS = [
  { "name": "Top Speed", "style": "list", "default": "default", "initial": ["70", "90", "120", "150", "170"] },
  { "name": "Acceleration", "style": "list", "initial": ["default", "medium", "high"] },
  { "name": "Traction", "style": "list", "initial": ["default", "medium", "high"] },
  { "name": "Noise Distance", "style": "slider", "min": 0.0, "max": 1000.0, "default": 500.0, "initial": 500.0, "increment": 50.0, "note": "how far the ATV noise travels" },
  { "name": "Vision Distance", "style": "slider", "min": 0.0, "max": 1000.0, "default": 200.0, "initial": 200.0, "increment": 50.0, "note": "how far you are visible on the ATV" },
  { "name": "Camera Distance", "style": "slider", "min": 0.05, "max": 20.0, "default": 3.75, "initial": 3.75, "increment": 0.05 , "note": "larger distance = wider FOV"},
]
SPEED_70 = {
  "gears": [2.2309999465942383, 1.7999999523162842, 1.5290000438690186, 1.277999997138977, 1.0479999780654907, 0.0, 0.0, 0.0],
  "upshift": [6800.0, 6800.0, 6800.0, 6800.0, 6800.0, 0.0, 0.0, 0.0],
  "downshift": [3840.820068359375, 4044.43994140625, 3976.830078125, 3902.60009765625, 0.0, 0.0, 0.0, 0.0],
  "max_rpm": 6850.0,
  "optimal_rpm": 5000.0,
}
SPEED_90 = {
  "gears": [2.2309999465942383, 1.7999999523162842, 1.5290000438690186, 1.277999997138977, 1.0479999780654907, 0.0, 0.0, 0.0],
  "upshift": [8000.0, 8000.0, 8000.0, 8000.0, 8000.0, 0.0, 0.0, 0.0],
  "downshift": [4000.0, 4000.0, 4000.0, 4000.0, 0.0, 0.0, 0.0, 0.0],
  "max_rpm": 8500.0,
  "optimal_rpm": 4000.0,
}
SPEED_120 = {
  "gears": [2.2309999465942383, 1.7999999523162842, 1.5290000438690186, 1.277999997138977, 1.0479999780654907, 0.0, 0.0, 0.0],
  "upshift": [15000.0, 15000.0, 15000.0, 15000.0, 15000.0, 0.0, 0.0, 0.0],
  "downshift": [7500.0, 7500.0, 7500.0, 7500.0, 0.0, 0.0, 0.0, 0.0],
  "max_rpm": 15500.0,
  "optimal_rpm": 5000.0,
}
SPEED_150 = {
  "gears": [2.2309999465942383, 1.7999999523162842, 1.5290000438690186, 1.277999997138977, 1.0479999780654907, 0.0, 0.0, 0.0],
  "upshift": [20000.0, 20000.0, 20000.0, 20000.0, 20000.0, 0.0, 0.0, 0.0],
  "downshift": [10000.0, 10000.0, 10000.0, 10000.0, 0.0, 0.0, 0.0, 0.0],
  "max_rpm": 25000.0,
  "optimal_rpm": 5000.0,
}
SPEED_170 = {
  "gears": [2.2309999465942383, 1.7999999523162842, 1.5290000438690186, 1.277999997138977, 1.0479999780654907, 1.0, 0.0, 0.0],
  "upshift": [20000.0, 20000.0, 20000.0, 20000.0, 20000.0, 20000.0, 0.0, 0.0],
  "downshift": [10000.0, 10000.0, 10000.0, 10000.0, 10000.0, 0.0, 0.0, 0.0],
  "max_rpm": 25000.0,
  "optimal_rpm": 4500.0,
}

TORQUE_DEFAULT = {
  "min": 1.0,
  "max": 0.8999999761581421,
  "optimal": 17.5
}
TORQUE_MEDIUM = {
  "min": 2.0,
  "max": 4.0,
  "optimal": 17.5
}
TORQUE_HIGH = {
  "min": 4.0,
  "max": 12.0,
  "optimal": 14.0
}

TRACTION_DEFAULT = {
  "front_friction": 1.5,
  "rear_friction": 1.5
}
TRACTION_MEDIUM = {
  "front_friction": 2.0,
  "rear_friction": 2.0
}
TRACTION_HIGH = {
  "front_friction": 2.75,
  "rear_friction": 3.0
}

TRANSMISSION_FILE = "editor/entities/vehicles/01_land/v001_car_atv/modules/default/v001_car_atv_transmission.vmodc"
AERODYNAMICS_FILE = "editor/entities/vehicles/01_land/v001_car_atv/modules/default/v001_car_atv_land_aerodynamics.vmodc"
LANDGLOBAL_FILE = "editor/entities/vehicles/01_land/v001_car_atv/modules/default/v001_car_atv_land_global.vmodc"
LANDENGINE_FILE = "editor/entities/vehicles/01_land/v001_car_atv/modules/default/v001_car_atv_land_engine.vmodc"

RED_MERGE_PATH = "editor/entities/vehicles/01_land/v001_car_atv/v001_car_atv_black_red.ee"
SILVER_MERGE_PATH = "editor/entities/vehicles/01_land/v001_car_atv/v001_car_atv_black_silver.ee"
JADE_MERGE_PATH = "editor/entities/vehicles/01_land/v001_car_atv/v001_car_atv_default.ee"

ANIMAL_SENSES_FILE = "settings/hp_settings/animal_senses.bin"
CAMERA_FILE = "editor/entities/cameras/tp_atv_framing.ctunec"

def map_options(options: dict) -> dict:
  top_speed = options["top_speed"] if options["top_speed"] else "default"
  acceleration = options["acceleration"] if options["acceleration"] else "default"
  traction = options["traction"] if options["traction"] else "default"
  noise = options["noise_distance"] if "noise_distance" in options else mods.get_mod_option_default("noise_distance", OPTIONS)
  vision = options["vision_distance"] if "vision_distance" in options else mods.get_mod_option_default("vision_distance", OPTIONS)
  camera_distance = options["camera_distance"] if "camera_distance" in options else mods.get_mod_option_default("camera_distance", OPTIONS)

  return {
    "top_speed": top_speed,
    "acceleration": acceleration,
    "traction": traction,
    "noise_distance": noise,
    "vision_distance": vision,
    "camera_distance": camera_distance,
  }


def format_options(options: dict) -> str:
  options = map_options(options)
  top_speed = options["top_speed"]
  top_speed_text = f"Speed {top_speed}km/h" if top_speed != "default" else ""
  acceleration = options["acceleration"]
  acceleration_text = f"Acceleration {acceleration}" if acceleration != "default" else ""
  traction = options["traction"]
  traction_text = f"Traction {traction}" if traction != "default" else ""
  noise_distance = options["noise_distance"]
  noise_text = f"Noise {noise_distance}m" if noise_distance != mods.get_mod_option_default("noise_distance", OPTIONS) else ""
  vision_distance = options["vision_distance"]
  vision_text = f"Vision {vision_distance}m" if vision_distance != mods.get_mod_option_default("vision_distance", OPTIONS) else ""
  camera_distance = options["camera_distance"]
  camera_text = f"Camera {camera_distance}m" if camera_distance != mods.get_mod_option_default("camera_distance", OPTIONS) else ""

  options_text_array = [top_speed_text, acceleration_text, traction_text, noise_text, vision_text, camera_text]
  options_text = ", ".join([s for s in options_text_array if s and s.strip()])
  options_text = options_text if options_text else "No Changes"

  return f"Modify ATV ({options_text})"

def get_files(options: dict) -> list[str]:
  options = map_options(options)
  atv_files = []
  if options["top_speed"] != "default":
    atv_files.extend([TRANSMISSION_FILE, LANDENGINE_FILE, AERODYNAMICS_FILE])
  if options["acceleration"] != "default":
    atv_files.append(LANDENGINE_FILE)
  if options["traction"] != "default":
    atv_files.append(LANDGLOBAL_FILE)
  if (
    options["noise_distance"] != mods.get_mod_option_default("noise_distance", OPTIONS)
    or options["vision_distance"] != mods.get_mod_option_default("vision_distance", OPTIONS)
  ):
    atv_files.append(ANIMAL_SENSES_FILE)
  if options["camera_distance"] != mods.get_mod_option_default("camera_distance", OPTIONS):
    atv_files.append(CAMERA_FILE)
  return atv_files

def _update_gears(values: list[float], start_offset: int) -> None:
  updates = []
  for i, value in enumerate(values):
    updates.append({"offset": start_offset + (i * 4), "value": float(value)})
  return updates

def update_transmission_file(speed_options: dict) -> None:
  transmission = mods2.deserialize_adf(TRANSMISSION_FILE).table_instance_full_values[0].value
  updates = [
    {"offset": transmission["nitrous_gears"].data_offset, "value": 1},
    {"offset": transmission["top_speed"].data_offset, "value": 250.0},
    {"offset": transmission["reverse_gear_ratio"].data_offset, "value": 3.0},
  ]
  updates.extend(_update_gears(speed_options["gears"], transmission["gear_ratios"].data_offset))
  updates.extend(_update_gears(speed_options["upshift"], transmission["upshift_rpm"].data_offset))
  updates.extend(_update_gears(speed_options["downshift"], transmission["downshift_rpm"].data_offset))
  mods.apply_updates_to_file(TRANSMISSION_FILE, updates)

def update_landengine_file(speed_options: dict, torque_option: dict) -> None:
  landengine = mods2.deserialize_adf(LANDENGINE_FILE).table_instance_full_values[0].value
  updates = [
    {"offset": landengine["resistance_at_max_rpm"].data_offset, "value": 0.05},
    {"offset": landengine["max_rpm"].data_offset, "value": speed_options["max_rpm"]},
    {"offset": landengine["optimal_rpm"].data_offset, "value": speed_options["optimal_rpm"]},
    {"offset": landengine["torque_factor_at_max_rpm"].data_offset, "value": torque_option["max"]},
    {"offset": landengine["torque_factor_at_min_rpm"].data_offset, "value": torque_option["min"]},
    {"offset": landengine["torque_factor_at_optimal_rpm"].data_offset, "value": torque_option["optimal"]},
  ]
  mods.apply_updates_to_file(LANDENGINE_FILE, updates)

def update_landglobal_file(traction_option: dict) -> None:
  landglobal = mods2.deserialize_adf(LANDGLOBAL_FILE).table_instance_full_values[0].value
  updates = [
    {"offset": landglobal["front_wheels"].value["arcade_friction_multiplier"].data_offset, "value": traction_option["front_friction"]},
    {"offset": landglobal["front_wheels"].value["arcade_drag_multiplier"].data_offset, "value": 0.0},
    {"offset": landglobal["rear_wheels"].value["arcade_friction_multiplier"].data_offset, "value": traction_option["rear_friction"]},
    {"offset": landglobal["rear_wheels"].value["arcade_drag_multiplier"].data_offset, "value": 0.0},
    {"offset": landglobal["front_wheels"].value["use_shape_cast"].data_offset, "value": 0, "format": "sint08"},
    {"offset": landglobal["rear_wheels"].value["use_shape_cast"].data_offset, "value": 0, "format": "sint08"},
  ]
  mods.apply_updates_to_file(LANDGLOBAL_FILE, updates)

def update_aerodynamics_file() -> None:
  aerodynamics = mods2.deserialize_adf(AERODYNAMICS_FILE).table_instance_full_values[0].value
  updates = [
    {"offset": aerodynamics["frontal_area"].data_offset, "value": 1.25},
    {"offset": aerodynamics["drag_coefficient"].data_offset, "value": 0.3},
    {"offset": aerodynamics["top_speed_drag_coefficient"].data_offset, "value": 0.3},
  ]
  mods.apply_updates_to_file(AERODYNAMICS_FILE, updates)

def update_camera_file(distance: float) -> None:
  camera = mods2.deserialize_adf(CAMERA_FILE).table_instance_full_values[0].value
  updates = [
    {"offset": camera["Distance"].data_offset, "value": distance}
  ]
  mods.apply_updates_to_file(CAMERA_FILE, updates)

def update_animal_senses_file(noise: float, vision: float) -> None:
  if noise != mods.get_mod_option_default("noise_distance", OPTIONS):
    mods2.update_file_at_multiple_coordinates_with_value(ANIMAL_SENSES_FILE, "vehicle_data", ["B4", "C4"], int(noise))
    if noise < 150:
      mods2.update_file_at_multiple_coordinates_with_value(ANIMAL_SENSES_FILE, "vehicle_data", ["B3", "C3"], int(noise))
  if vision != mods.get_mod_option_default("vision_distance", OPTIONS):
    mods2.update_file_at_multiple_coordinates_with_value(ANIMAL_SENSES_FILE, "vehicle_data", ["B9", "C9"], int(vision))
    if vision < 50:
      mods2.update_file_at_multiple_coordinates_with_value(ANIMAL_SENSES_FILE, "vehicle_data", ["B8", "C8"], int(noise))

def process(options: dict) -> None:
  options = map_options(options)

  speed_options = {
    "90": SPEED_90,
    "120": SPEED_120,
    "150": SPEED_150,
    "170": SPEED_170,
  }.get(options["top_speed"], SPEED_70)

  torque_option = {
    "medium": TORQUE_MEDIUM,
    "high": TORQUE_HIGH,
  }.get(options["acceleration"], TORQUE_DEFAULT)

  traction_option = {
    "medium": TRACTION_MEDIUM,
    "high": TRACTION_HIGH,
  }.get(options["traction"], TRACTION_DEFAULT)

  if options["top_speed"] != "default":
    update_transmission_file(speed_options)
    update_aerodynamics_file()
    update_landengine_file(speed_options, torque_option)

  if options["acceleration"] != "default":
    update_landengine_file(speed_options, torque_option)

  if options["traction"] != "default":
    update_landglobal_file(traction_option)

  if (
    options["noise_distance"] != mods.get_mod_option_default("noise_distance", OPTIONS)
    or options["vision_distance"] != mods.get_mod_option_default("vision_distance", OPTIONS)
  ):
    update_animal_senses_file(options["noise_distance"], options["vision_distance"])

  if options["camera_distance"] != mods.get_mod_option_default("camera_distance", OPTIONS):
    update_camera_file(options["camera_distance"])

def merge_files(files: list[str], options: dict) -> None:
  for bundle_file in [RED_MERGE_PATH, SILVER_MERGE_PATH, JADE_MERGE_PATH]:
    bundle_lookup = mods.get_sarc_file_info(mods.APP_DIR_PATH / "org" / bundle_file)
    for file in files:
      if file not in [ANIMAL_SENSES_FILE, CAMERA_FILE]:
        mods.merge_into_archive(file, str(bundle_file), bundle_lookup)
