from modbuilder import mods, mods2

DEBUG = False
NAME = "Modify ATV"
DESCRIPTION = "Allows you to modify the performance of the ATV (all colors). The top speed is not exact, since the acceleration settings will slightly change the top seed. Higher top speeds will need additional acceleration no matter what you pick."
OPTIONS = [
  { "name": "Top Speed", "style": "list", "default": "60", "initial": ["70", "90", "120", "150", "170"] },
  { "name": "Acceleration", "style": "list", "initial": ["default", "medium", "high"] },
  { "name": "Traction", "style": "list", "initial": ["default", "medium", "high"] },
  { "name": "Noise Distance", "style": "slider", "min": 0.0, "max": 500.0, "default": 500.0, "initial": 500.0, "increment": 50.0, "note": "how far the ATV noise travels" },
  { "name": "Vision Distance", "style": "slider", "min": 0.0, "max": 200.0, "default": 200.0, "initial": 200.0, "increment": 50.0, "note": "how far you are visible on the ATV" }
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
NOISE_PATH = "settings/hp_settings/animal_senses.bin"

def map_options(options: dict) -> dict:
  top_speed = options["top_speed"] if options["top_speed"] else "70"
  acceleration = options["acceleration"] if options["acceleration"] else "default"
  traction = options["traction"] if options["traction"] else "default"
  noise = options["noise_distance"] if "noise_distance" in options else 500.0
  vision = options["vision_distance"] if "vision_distance" in options else 200.0

  if top_speed != "70" and acceleration == "default":
    acceleration = "medium"
  elif top_speed == "170" and acceleration != "high":
    acceleration = "high"

  return {
    "top_speed": top_speed,
    "acceleration": acceleration,
    "traction": traction,
    "noise_distance": noise,
    "vision_distance": vision
  }


def format_options(options: dict) -> str:
  options = map_options(options)
  top_speed = options["top_speed"]
  acceleration = options["acceleration"]
  traction = options["traction"]
  noise = options["noise_distance"]
  vision = options["vision_distance"]
  return f"Modify ATV ({top_speed}km/h, {acceleration}, {traction}, {int(noise)}m, {int(vision)}m)"

def get_files(options: dict) -> list[str]:
  noise = options["noise_distance"]
  atv_files = [TRANSMISSION_FILE, LANDENGINE_FILE, AERODYNAMICS_FILE, LANDGLOBAL_FILE]
  if noise != 500.0:
    atv_files.append(NOISE_PATH)
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

def update_noise_file(noise: float, vision: float) -> None:
  if noise != 500.0:
    mods2.update_file_at_multiple_coordinates_with_value(NOISE_PATH, "vehicle_data", ["B4", "C4"], int(noise))
    if noise < 150:
      mods2.update_file_at_multiple_coordinates_with_value(NOISE_PATH, "vehicle_data", ["B3", "C3"], int(noise))
  if vision != 200.0:
    mods2.update_file_at_multiple_coordinates_with_value(NOISE_PATH, "vehicle_data", ["B9", "C9"], int(vision))
    if vision < 50:
      mods2.update_file_at_multiple_coordinates_with_value(NOISE_PATH, "vehicle_data", ["B8", "C8"], int(noise))

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

  update_transmission_file(speed_options)
  update_landengine_file(speed_options, torque_option)
  update_landglobal_file(traction_option)
  update_aerodynamics_file()
  update_noise_file(options["noise_distance"], options["vision_distance"])

def merge_files(files: list[str], options: dict) -> None:
  for bundle_file in [RED_MERGE_PATH, SILVER_MERGE_PATH, JADE_MERGE_PATH]:
    bundle_lookup = mods.get_sarc_file_info(mods.APP_DIR_PATH / "org" / bundle_file)
    for file in files:
      if file != NOISE_PATH:
        mods.merge_into_archive(file, str(bundle_file), bundle_lookup)
