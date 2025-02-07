from modbuilder import mods
from deca.ff_rtpc import rtpc_from_binary

DEBUG = False
NAME = "Modify Weather"
DESCRIPTION = "Control the weather. Select all weather conditions you want to keep."
PRESETS_FILE = "environment/environment_presets_config.bin"

def set_weather_conditions() -> tuple[list[str], list[str]]:
    with(open(f"{mods.APP_DIR_PATH}/org/{PRESETS_FILE}", "rb") as f):
        data = rtpc_from_binary(f)
        condition_nodes = data.root_node.child_table[0].child_table
        available_conditions = []
        protected_conditions = []
        for node in condition_nodes:
            condition = node.prop_table[1].data.decode("utf-8")
            if (
                condition in ["base", "damage_effect", "heal_effect", "huntermate"]
                or condition.startswith("night_vision")
            ):
                protected_conditions.append(condition)
                continue
            if not condition.startswith("reserve_"):
                available_conditions.append(condition)
    return sorted(available_conditions), sorted(protected_conditions)

AVAILABLE_WEATHER_CONDITIONS, PROTECTED_WEATHER_CONDITIONS = set_weather_conditions()

OPTIONS = [
  {
    "name": "Allowed Weather Conditions",
    "style": "listbox",
    "values": AVAILABLE_WEATHER_CONDITIONS,
    "initial": None,
    "size": 6
  }
]
PRESETS = [
  {
    "name": "Game Defaults",
    "options": [
      {"name": "allowed_weather_conditions", "values": list(range(0, len(AVAILABLE_WEATHER_CONDITIONS))) }
    ]
  },
  {
    "name": "Always Sunny",
    "options": [
      {"name": "allowed_weather_conditions", "values": [AVAILABLE_WEATHER_CONDITIONS.index("forced_sunny")]}
    ]
  }
]

def format(options: dict) -> str:
  return f"Modify Weather ({len(options['allowed_weather_conditions'])} conditions)"

def get_files(options: dict) -> list[str]:
  return [PRESETS_FILE]

def process(options: dict) -> None:
    with(open(f"{mods.APP_DIR_PATH}/org/{PRESETS_FILE}", "rb") as f):
        data = rtpc_from_binary(f)
    condition_nodes = data.root_node.child_table[0].child_table
    allowed_weather_conditions = options['allowed_weather_conditions']
    not_allowed_weather_conditions = []
    for node in condition_nodes:
        prop = node.prop_table[1]
        condition = prop.data.decode("utf-8")
        if (
            condition not in PROTECTED_WEATHER_CONDITIONS
            and condition not in allowed_weather_conditions
        ):
            not_allowed_weather_conditions.append((prop.data_pos, "xxx"))
    if len(not_allowed_weather_conditions) > 0:
        mods.update_file_at_offsets_with_values(PRESETS_FILE, not_allowed_weather_conditions)

def handle_update(mod_key: str, mod_options: dict) -> dict:
  """
  2.2.2
  - Prevent non-weather fullscreen effects from being disabled (night vision, healing/damage indicators)
  """
  allowed_weather_conditions = [weather for weather in mod_options["allowed_weather_conditions"] if weather in AVAILABLE_WEATHER_CONDITIONS]
  updated_mod_key = mod_key
  updated_mod_options = {"allowed_weather_conditions": allowed_weather_conditions}
  return updated_mod_key, updated_mod_options
