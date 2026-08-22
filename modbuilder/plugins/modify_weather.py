from deca.ff_rtpc import rtpc_from_binary
from modbuilder import mods

DEBUG = False
NAME = "Modify Weather"
DESCRIPTION = "Control the weather. Select all weather conditions you want to keep."
PRESETS_FILE = "environment/environment_presets_config.bin"

ALWAYS_PROTECTED_CONDITIONS = {"base", "damage_effect", "heal_effect", "huntermate"}


def _get_condition_nodes():
    """Parse and return the condition nodes from the original weather preset file."""
    with open(mods.get_org_file(PRESETS_FILE), "rb") as f:
        data = rtpc_from_binary(f)
    return data.root_node.child_table[0].child_table


def _is_always_protected_condition(condition: str) -> bool:
    """Return whether a preset is an engine effect that users must not disable."""
    return (
        condition in ALWAYS_PROTECTED_CONDITIONS
        or condition.startswith("night_vision")
    )

def set_weather_conditions() -> tuple[list[str], list[str], list[str]]:
    available_conditions = []
    reserve_conditions = []
    protected_conditions = []
    for node in _get_condition_nodes():
        condition = node.prop_table[1].data.decode("utf-8")
        if _is_always_protected_condition(condition):
            protected_conditions.append(condition)
        elif condition.startswith("reserve_"):
            reserve_conditions.append(condition)
        else:
            available_conditions.append(condition)
    return sorted(available_conditions), sorted(reserve_conditions), sorted(protected_conditions)

AVAILABLE_WEATHER_CONDITIONS, RESERVE_WEATHER_CONDITIONS, PROTECTED_WEATHER_CONDITIONS = set_weather_conditions()
ALL_WEATHER_CONDITIONS = AVAILABLE_WEATHER_CONDITIONS + RESERVE_WEATHER_CONDITIONS

EXPERIMENTAL_OPTION_KEY = "modify_weather__experimental_show_all_weathers"
WEATHER_LIST_KEY = "modify_weather__allowed_weather_conditions"

OPTIONS = [
  {
    "name": "Experimental: Show all weathers",
    "key": "experimental_show_all_weathers",
    "style": "boolean",
    "initial": False,
    "enable_events": True,
    "note": "Reserve-specific weather may be used by missions or cutscenes. Disabling it could interfere with scripted events."
  },
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

def format_options(options: dict) -> str:
  return f"Modify Weather ({len(options['allowed_weather_conditions'])} conditions)"

def get_files(options: dict) -> list[str]:
  return [PRESETS_FILE]


def _update_weather_list(window, show_all: bool, selected_conditions: list[str] | None = None) -> None:
    """Show safe or experimental weather entries while preserving selections."""
    current_values = selected_conditions
    if current_values is None:
        current_values = list(window[WEATHER_LIST_KEY].get())
        if show_all:
            current_values.extend(RESERVE_WEATHER_CONDITIONS)
    list_values = ALL_WEATHER_CONDITIONS if show_all else AVAILABLE_WEATHER_CONDITIONS
    selected_indices = [i for i, condition in enumerate(list_values) if condition in current_values]
    window[WEATHER_LIST_KEY].update(values=list_values, set_to_index=selected_indices)


def handle_event(event: str, window, values: dict) -> None:
    if event == EXPERIMENTAL_OPTION_KEY:
        _update_weather_list(window, bool(values[event]))


def load_options(window, options: dict) -> None:
    """Restore both the experimental list contents and its selected values."""
    selected_conditions = options.get("allowed_weather_conditions", AVAILABLE_WEATHER_CONDITIONS)
    show_all = options.get(
        "experimental_show_all_weathers",
        any(condition in RESERVE_WEATHER_CONDITIONS for condition in selected_conditions),
    )
    window[EXPERIMENTAL_OPTION_KEY].update(show_all)
    _update_weather_list(window, show_all, selected_conditions)


def _reserve_base_condition(condition: str) -> str | None:
    """Return reserve_XX for a reserve-specific weather override."""
    parts = condition.split("_", 2)
    if len(parts) < 2:
        return None
    reserve_base = "_".join(parts[:2])
    return reserve_base if reserve_base in RESERVE_WEATHER_CONDITIONS else None

def process(options: dict) -> None:
    condition_nodes = _get_condition_nodes()
    allowed_weather_conditions = set(options['allowed_weather_conditions'])
    show_all = options.get("experimental_show_all_weathers", False)
    editable_conditions = set(ALL_WEATHER_CONDITIONS if show_all else AVAILABLE_WEATHER_CONDITIONS)
    not_allowed_weather_conditions = []
    condition_offsets = {
        node.prop_table[1].data.decode("utf-8"): node.prop_table[1].data_pos
        for node in condition_nodes
    }
    for node in condition_nodes:
        prop = node.prop_table[1]
        condition = prop.data.decode("utf-8")
        # Keep the condition node and hash valid, but point disabled conditions
        # at the existing base environment instead of corrupting their names.
        if (
            condition in editable_conditions
            and condition not in allowed_weather_conditions
        ):
            reserve_base = _reserve_base_condition(condition)
            fallback = reserve_base if reserve_base in allowed_weather_conditions else "base"
            not_allowed_weather_conditions.append((prop.pos + 4, condition_offsets[fallback]))
    if len(not_allowed_weather_conditions) > 0:
        mods.update_file_at_offsets_with_values(PRESETS_FILE, not_allowed_weather_conditions)

def handle_update(mod_key: str, mod_options: dict, version: str) -> tuple[str, dict]:
  """
  2.2.2
  - Prevent non-weather fullscreen effects from being disabled (night vision, healing/damage indicators)
  """
  saved_conditions = mod_options["allowed_weather_conditions"]
  show_all = mod_options.get(
    "experimental_show_all_weathers",
    any(weather in RESERVE_WEATHER_CONDITIONS for weather in saved_conditions),
  )
  valid_conditions = ALL_WEATHER_CONDITIONS if show_all else AVAILABLE_WEATHER_CONDITIONS
  allowed_weather_conditions = [weather for weather in saved_conditions if weather in valid_conditions]
  updated_mod_key = mod_key
  updated_mod_options = {
    "experimental_show_all_weathers": show_all,
    "allowed_weather_conditions": allowed_weather_conditions,
  }
  if "modify_weather" in mod_options:
    updated_mod_options["modify_weather"] = mod_options["modify_weather"]
  return updated_mod_key, updated_mod_options
