from modbuilder import mods
from pathlib import Path
from deca.ff_rtpc import rtpc_from_binary, RtpcNode

DEBUG = False
NAME = "Increase Diamond Spawns"
DESCRIPTION = "Increase the chance for each new animal to spawn as a diamond due to the increased weight of the animal. Recommended to start with a fresh population (delete old population file)."
FILE = "global/global_animal_types.blo"
OPTIONS = [
  {
   "name": "Weight Bias",
   "min": 0.0,
   "max": 0.5,
   "default": 0.0,
   "initial": 0.0,
   "increment": 0.005,
   "note": "Spawned animals will be biased towards higher end of their weight range. Heavier animals = higher score."
  }
]
PRESETS = [
  { "name": "Game Defaults", "options": [ {"name": "weight_bias", "value": 0.0} ] },
  { "name": "Very Low", "options": [ {"name": "weight_bias", "value": 0.005} ]},
  { "name": "Low", "options": [ {"name": "weight_bias", "value": 0.025} ] },
  { "name": "Medium", "options": [ {"name": "weight_bias", "value": 0.05} ] },
  { "name": "High", "options": [ {"name": "weight_bias", "value": 0.1} ] },
  { "name": "Very High", "options": [ {"name": "weight_bias", "value": 0.2} ] },
  { "name": "Extreme", "options": [ {"name": "weight_bias", "value": 0.5} ] }
]

def format(options: dict) -> str:
  return f"Increase Diamond Spawns ({options['weight_bias']} weight bias)"

def open_rtpc(filename: Path) -> list[RtpcNode]:
  with filename.open("rb") as f:
    data = rtpc_from_binary(f)
  root = data.root_node
  return root.child_table[0].child_table

def get_animal_scoring_table_index(animal: RtpcNode) -> int:
  for i in range(len(animal.child_table)):
    table_type = animal.child_table[i].prop_table[0].data
    if type(table_type) == bytes and table_type.decode("utf-8") == 'CAnimalTypeScoringSettings':
      return i
  return None

def process(options: dict) -> None:
  weight_bias = options['weight_bias']
  offsets_and_values = []

  animals = open_rtpc(mods.APP_DIR_PATH / "mod/dropzone" / FILE)
  for animal in animals:
    scoring_table_index = get_animal_scoring_table_index(animal)
    if scoring_table_index is None:
      continue

    score_details = animal.child_table[scoring_table_index].child_table
    for score_node in score_details:
      score_type = score_node.prop_table[1].data
      if type(score_type) == bytes and score_type.decode("utf-8") == "SAnimalTypeScoringDistributionSettings":
        score_high = score_node.prop_table[-3].data
        if score_high > 0:
          score_max_weight = score_node.prop_table[2].data
          score_weight_bias_offset = score_node.prop_table[-2].data_pos
          max_weight_bias = round(score_max_weight * weight_bias, 2)
          offsets_and_values.append((score_weight_bias_offset, max_weight_bias))
  mods.update_file_at_offsets_with_values(Path(FILE), offsets_and_values)
