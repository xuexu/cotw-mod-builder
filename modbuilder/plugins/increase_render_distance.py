from modbuilder import mods
from deca.ff_rtpc import RtpcNode, RtpcProperty
from pathlib import Path

DEBUG = False
NAME = "Increase Render Distance"
DESCRIPTION = "Increase the render distance of animals. There are two settings: when the animals spawn (get closer) or desapwn (moving away)."
FILE = "global/global_animal_types.blo"
WARNING = "Increasing the render distance too much can cause the game to crash or behave strangely. I personally do not go beyond 750m."
OPTIONS = [
  { "name": "Spawn Distance", "min": 1, "max": 1000, "default": 384, "increment": 1, "initial": 384 },
  { "name": "Despawn Distance", "min": 1, "max": 1000, "default": 416, "increment": 1, "initial": 416 },
  { "name": "Bird Spawn Distance", "min": 1, "max": 1000, "default": 470, "increment": 1, "initial": 470 },
  { "name": "Bird Despawn Distance", "min": 1, "max": 1000, "default": 500, "increment": 1, "initial": 500 }
]
PRESETS = [
  {
    "name": "Game Defaults",
    "options": [
      {"name": "spawn_distance", "value": 384},
      {"name": "despawn_distance", "value": 416},
      {"name": "bird_spawn_distance", "value": 470},
      {"name": "bird_despawn_distance", "value": 500}
    ]
  },
  {
    "name": "Recommended",
    "options": [
      {"name": "spawn_distance", "value": 750},
      {"name": "despawn_distance", "value": 750},
      {"name": "bird_spawn_distance", "value": 750},
      {"name": "bird_despawn_distance", "value": 750}
    ]
  }
]

def format_options(options: dict) -> str:
  spawn_distance = int(options['spawn_distance'])
  despawn_distance = int(options['despawn_distance'])
  return f"Increase Render Distance ({spawn_distance}m, {despawn_distance}m)"

def find_prop_offset(value: float, props: list[RtpcProperty]) -> int:
  for prop in props:
    if prop.data == value:
      return prop.data_pos
  return None

def get_animal_props(animal_list: RtpcNode) -> RtpcNode:
  animal_props = []
  for animal in animal_list.child_table:
    animal_props.append(animal.prop_table)
  return animal_props

def process(options: dict) -> None:
  spawn_distance = options['spawn_distance']
  bird_spawn_distance = options['bird_spawn_distance']
  despawn_distance = options['despawn_distance']
  bird_despawn_distance = options['bird_despawn_distance']
  global_animal_types_rtpc = mods.open_rtpc(mods.APP_DIR_PATH / "mod/dropzone" / FILE)
  animal_list = global_animal_types_rtpc.child_table[0]
  animal_props = get_animal_props(animal_list)
  spawn_offsets = []
  bird_spawn_offsets = []
  despawn_offsets = []
  bird_despawn_offsets = []
  for animal in animal_props:
    bird_spawn_offset = None
    bird_despawn_offset = None

    spawn_offset = find_prop_offset(384.0, animal)
    if not spawn_offset:
      bird_spawn_offset = find_prop_offset(470.0, animal)
    despawn_offset = find_prop_offset(416.0, animal)
    if not despawn_offset:
      bird_despawn_offset = find_prop_offset(500.0, animal)

    if spawn_offset:
      spawn_offsets.append(spawn_offset)
    if bird_spawn_offset:
      bird_spawn_offsets.append(bird_spawn_offset)
    if despawn_offset:
      despawn_offsets.append(despawn_offset)
    if bird_despawn_offset:
      bird_despawn_offsets.append(bird_despawn_offset)

  mods.update_file_at_offsets(Path(FILE), spawn_offsets, spawn_distance)
  mods.update_file_at_offsets(Path(FILE), bird_spawn_offsets, bird_spawn_distance)
  mods.update_file_at_offsets(Path(FILE), despawn_offsets, despawn_distance)
  mods.update_file_at_offsets(Path(FILE), bird_despawn_offsets, bird_despawn_distance)