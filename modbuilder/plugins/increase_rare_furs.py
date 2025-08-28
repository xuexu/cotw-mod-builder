from modbuilder import mods
from pathlib import Path
from deca.ff_rtpc import rtpc_from_binary, RtpcNode

DEBUG = False
NAME = "Increase Rare Furs"
DESCRIPTION = "Increase the percentage of animals with rare fur variations. Default rare fur chance is ~1.5%. This mod affects existing animals and does not require deleting your population file."
WARNING = "This mod runs client-side and is incompatible with multiplayer and the Animal Population Scanner tool. However, Trophies WILL save and display properly in lodges, even after removing the mod."
FILE = "global/global_animal_types.blo"
OPTIONS = [
  {
   "name": "Rare Fur Percentage",
   "min": 1.5,
   "max": 100.0,
   "default": 1.5,
   "initial": 1.5,
   "increment": 0.5,
   "note": "50% = Equal chance for common and rare fur variants."
  }
]
PRESETS = [
  { "name": "Game Defaults", "options": [ {"name": "rare_fur_percentage", "value": 1.5} ] },
  { "name": "Low", "options": [ {"name": "rare_fur_percentage", "value": 10.0} ] },
  { "name": "Medium", "options": [ {"name": "rare_fur_percentage", "value": 25.0} ] },
  { "name": "High", "options": [ {"name": "rare_fur_percentage", "value": 50.0} ] },
  { "name": "All Rare Furs", "options": [ {"name": "rare_fur_percentage", "value": 100.0} ] }
]

def format_options(options: dict) -> str:
  return f"Increase Rare Furs ({options['rare_fur_percentage']}%)"

def get_name(animal: RtpcNode) -> str:
  if type(animal.prop_table[-11].data) == bytes:
    return animal.prop_table[-11].data.decode('utf-8')
  else:
    return animal.prop_table[-12].data.decode('utf-8')

def get_varitions_table_index(animal: RtpcNode) -> int:
  for i in range(len(animal.child_table)):
      table_type = animal.child_table[i].prop_table[0].data
      if type(table_type) == bytes and table_type.decode("utf-8") == 'CAnimalTypeVisualVariationSettings':
        return i
  return None

class Fur:
  def __init__(self, variant_node: RtpcNode) -> None:
   self.name = variant_node.prop_table[-1].data.decode("utf-8")
   self.get_fur_weight(variant_node)
   self.get_fur_rarity(variant_node)

  def get_fur_weight(self, variant_node: RtpcNode) -> None:
    if type(variant_node.prop_table[-3].data) == int:
      i = -3
    else:
      i = -4
    self.weight = variant_node.prop_table[i].data
    self.weight_offset = variant_node.prop_table[i].data_pos

  def get_fur_rarity(self, variant_node: RtpcNode) -> None:
    # 0 = common, 1 = uncommon, 2 = rare, 3 = veryrare
    if type(variant_node.prop_table[6].data) == int:
      i = 6
    else:
      i = 7
    self.rarity = variant_node.prop_table[i].data
    self.rarity_offset = variant_node.prop_table[i].data_pos

def get_furs(variation_details: RtpcNode) -> list[Fur]:
  furs = []
  for variant_node in variation_details:
    variant_type = variant_node.prop_table[0].data
    if type(variant_type) == bytes and variant_type.decode("utf-8") == "SAnimalTypeVisualVariation":
      fur = Fur(variant_node)
      if "great_one" not in fur.name:  # Do not modify Great Ones
        furs.append(fur)
  return furs

def calculate_rarity_weights(furs: list[Fur], rare_fur_percentage: float) -> dict:
  rarity_weights = {}
  for fur in furs:
    if fur.rarity not in rarity_weights:
      rarity_weights[fur.rarity] = fur.weight
  max_weight = max(rarity_weights.values())
  for rarity, weight in rarity_weights.items():
    if rare_fur_percentage <= 50.0:
      # 35% increase to rares = 70% increase to non-common weights + no change to common weight
      # Increase uncommon, rare, and veryrare weights toward the maximum. Leave common alone.
      if rarity != 0:
        weight_diff = max_weight - weight
        weight_increase = (rare_fur_percentage * 2) / 100 * weight_diff
        new_weight = weight + weight_increase
        rarity_weights[rarity] = int(new_weight)
    elif rare_fur_percentage > 50.0:
      # 65% increased rares = max non-common weights + 30% reduction to common weight
      # Increase uncommon, rare, and veryrare weights to the maximum
      if rarity != 0:
        rarity_weights[rarity] = max_weight
      # Decrease common weight
      if rarity == 0:
        weight_multiplier = (50 - (rare_fur_percentage - 50)) / 50
        new_weight = weight * weight_multiplier
        rarity_weights[rarity] = int(new_weight)
  return rarity_weights

def process(options: dict) -> None:
  rare_fur_percentage = options['rare_fur_percentage']
  if rare_fur_percentage == 1.5:
    return

  offsets_and_values = []
  global_animal_types_rtpc = mods.open_rtpc(mods.APP_DIR_PATH / "mod/dropzone" / FILE)
  animals = global_animal_types_rtpc.child_table[0].child_table
  for animal in animals:
    variations_table_index = get_varitions_table_index(animal)
    if variations_table_index is None:
      continue
    variations_table = animal.child_table[variations_table_index].child_table
    furs = get_furs(variations_table)
    rarity_weights = calculate_rarity_weights(furs, rare_fur_percentage)
    for fur in furs:
      offsets_and_values.append((fur.weight_offset, rarity_weights[fur.rarity]))
  mods.update_file_at_offsets_with_values(Path(FILE), offsets_and_values)