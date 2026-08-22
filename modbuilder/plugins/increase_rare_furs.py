from pathlib import Path

from deca.ff_rtpc import RtpcNode, RtpcProperty
from modbuilder import mods
from modbuilder.logging_config import get_logger

logger = get_logger(__name__)

DEBUG = False
NAME = "Increase Rare Furs"
DESCRIPTION = "Increase the chance of Rare and Very Rare fur variations. This mod affects existing animals and does not require deleting your population file."
WARNING = "This mod runs client-side and is incompatible with multiplayer and the Animal Population Scanner tool. However, Trophies WILL save and display properly in lodges, even after removing the mod."
FILE = "global/global_animal_types.blo"
OPTIONS = [
  {
   "name": "Rare Fur Increase",
   "min": 0.0,
   "max": 100.0,
   "default": 0.0,
   "initial": 0.0,
   "increment": 0.5,
   "note": "0% = default rarities. 100% = only Rare and Very Rare furs appear"
  },
  {
   "name": "Include Quest-Only Furs",
   "style": "boolean",
   "initial": False,
   "note": "Enable Rare and Very Rare furs that normally only appear through scripted events."
  }
]
PRESETS = [
  { "name": "Game Defaults", "options": [ {"name": "rare_fur_increase", "value": 0.0} ] },
  { "name": "Low", "options": [ {"name": "rare_fur_increase", "value": 10.0} ] },
  { "name": "Medium", "options": [ {"name": "rare_fur_increase", "value": 25.0} ] },
  { "name": "High", "options": [ {"name": "rare_fur_increase", "value": 50.0} ] },
  { "name": "All Rare Furs", "options": [ {"name": "rare_fur_increase", "value": 100.0} ] }
]

CLASS_HASH = 0x1473b179
FUR_GENDER_HASH = 0x69e88c57
FUR_GREAT_ONE_HASH = 0xeb13fcd3
FUR_NAME_HASH = 0xf336b29f
FUR_RARITY_HASH = 0xc82af7b4
FUR_WEIGHT_HASH = 0xd8a03db0
GENDER_BOTH = 0
GENDER_FEMALE = 2
GENDER_MALE = 1
VISUAL_VARIATION_CLASS = b"SAnimalTypeVisualVariation"
VISUAL_VARIATION_SETTINGS_CLASS = b"CAnimalTypeVisualVariationSettings"

def format_options(options: dict) -> str:
  quest_furs = ", including quest-only furs" if options.get("include_quest_only_furs", False) else ""
  return f"Increase Rare Furs ({options['rare_fur_increase']}%{quest_furs})"

def _is_class(node: RtpcNode, class_name: bytes) -> bool:
  class_property = node.prop_map.get(CLASS_HASH)
  return class_property is not None and class_property.data == class_name


def get_variations_table(animal: RtpcNode) -> RtpcNode | None:
  return next(
    (child for child in animal.child_table if _is_class(child, VISUAL_VARIATION_SETTINGS_CLASS)),
    None,
  )


def _required_property(node: RtpcNode, name_hash: int) -> RtpcProperty:
  prop = node.prop_map.get(name_hash)
  if prop is None:
    raise ValueError(
      f"Visual variation 0x{node.name_hash:08x} is missing property 0x{name_hash:08x}"
    )
  return prop

class Fur:
  def __init__(self, variant_node: RtpcNode) -> None:
   self.name = _required_property(variant_node, FUR_NAME_HASH).data.decode("utf-8", errors="replace")
   self.gender = _required_property(variant_node, FUR_GENDER_HASH).data
   great_one_property = variant_node.prop_map.get(FUR_GREAT_ONE_HASH)
   self.is_great_one = bool(
     (great_one_property and great_one_property.data == 1)
     or _is_great_one_name(self.name)
   )
   self.get_fur_weight(variant_node)
   self.get_fur_rarity(variant_node)

  def get_fur_weight(self, variant_node: RtpcNode) -> None:
    weight_property = _required_property(variant_node, FUR_WEIGHT_HASH)
    self.weight = weight_property.data
    self.weight_offset = weight_property.data_pos

  def get_fur_rarity(self, variant_node: RtpcNode) -> None:
    # 0 = common, 1 = uncommon, 2 = rare, 3 = veryrare
    rarity_property = _required_property(variant_node, FUR_RARITY_HASH)
    self.rarity = rarity_property.data
    self.rarity_offset = rarity_property.data_pos


def _is_great_one_name(name: str) -> bool:
  normalized_name = name.lower().removeprefix("animal_visual_variation_")
  return (
    "great_one" in normalized_name
    or normalized_name.startswith("go_")
    or (normalized_name.startswith("go") and normalized_name[2:].isdigit())
  )


def get_all_furs(variation_details: list[RtpcNode]) -> list[Fur]:
  return [
    Fur(variant_node)
    for variant_node in variation_details
    if _is_class(variant_node, VISUAL_VARIATION_CLASS)
  ]


def get_furs(variation_details: list[RtpcNode]) -> list[Fur]:
  # Great Ones use the same rarity field as ordinary furs and are normally excluded from scaling.
  return [fur for fur in get_all_furs(variation_details) if not fur.is_great_one]

def _rounded_weights(weights: list[float], total: int) -> list[int]:
  """Round proportional weights while preserving their combined integer total."""
  rounded = [int(weight) for weight in weights]
  remainder = total - sum(rounded)
  order = sorted(range(len(weights)), key=lambda i: weights[i] - rounded[i], reverse=True)
  for i in order[:remainder]:
    rounded[i] += 1
  return rounded


def calculate_fur_weights(furs: list[Fur], increase_percentage: float, include_quest_only_furs: bool = False) -> dict[int, int]:
  """Scale Rare/Very Rare probability from the original distribution toward an equal 100% split."""
  if not 0.0 <= increase_percentage <= 100.0:
    raise ValueError("Rare fur percentage must be between 0 and 100")
  if not furs or increase_percentage == 0.0:
    return {fur.weight_offset: fur.weight for fur in furs}

  def eligible_rare(fur: Fur) -> bool:
    return fur.rarity in (2, 3) and (include_quest_only_furs or fur.weight > 0)

  present_genders = {
    gender for gender in (GENDER_MALE, GENDER_FEMALE)
    if any(fur.gender in (GENDER_BOTH, gender) for fur in furs)
  }
  genders_with_rares = {
    gender for gender in present_genders
    if any(fur.gender in (GENDER_BOTH, gender) and eligible_rare(fur) for fur in furs)
  }

  # Zero-weight rares are scripted/quest variants. Also protect every fur used by a sex that has no rare replacement.
  protected_furs = [
    fur for fur in furs
    if (fur.weight == 0 and not include_quest_only_furs)
    or any(
      gender not in genders_with_rares
      for gender in present_genders
      if fur.gender in (GENDER_BOTH, gender)
    )
  ]
  scalable_furs = [fur for fur in furs if fur not in protected_furs]
  rare_furs = [fur for fur in scalable_furs if fur.rarity in (2, 3)]
  nonrare_furs = [fur for fur in scalable_furs if fur.rarity not in (2, 3)]
  rare_total = sum(fur.weight for fur in rare_furs)
  nonrare_total = sum(fur.weight for fur in nonrare_furs)
  total = rare_total + nonrare_total
  if not rare_furs or rare_total <= 0 or total <= 0:
    return {fur.weight_offset: fur.weight for fur in furs}

  progress = increase_percentage / 100.0
  # Transfer probability away from non-rares without changing their relative proportions.
  new_nonrare_total = round(nonrare_total * (1.0 - progress))
  new_rare_total = total - new_nonrare_total
  nonrare_weights = _rounded_weights(
    [fur.weight / nonrare_total * new_nonrare_total for fur in nonrare_furs],
    new_nonrare_total,
  ) if nonrare_total else []

  # Blend each rare fur's original share toward an equal share as the slider approaches 100%.
  equal_share = 1.0 / len(rare_furs)
  rare_weights = _rounded_weights([
    new_rare_total * ((1.0 - progress) * fur.weight / rare_total + progress * equal_share)
    for fur in rare_furs
  ], new_rare_total)

  updates = {fur.weight_offset: fur.weight for fur in protected_furs}
  for fur, weight in zip(nonrare_furs, nonrare_weights):
    updates[fur.weight_offset] = weight
  for fur, weight in zip(rare_furs, rare_weights):
    updates[fur.weight_offset] = weight
  return updates


def _whitetail_great_one_updates(
  all_furs: list[Fur],
  ordinary_updates: dict[int, int],
) -> dict[int, int]:
  """
  Balance the unique Great One Whitetail fur without affecting ordinary Whitetail scaling.

  Great One Whitetails share the standard male Tan, Brown, and Dark Brown variations with their Great One
  The Fabled Piebald uses a unique 'great_one_whitetail' variation whose default weight is only 38
   while each re-used common fur has an initial weight of 25,000
  Every other species has a separate pool of Great One-only furs that this plugin doesn't need to touch
  For Whitetail only, transfer removed common-fur weight into Fabled Piebald in the same manner as non-GO furs
  This ensures consist behavior for Great One Whitetails. A 50% slider produces approximately a 50% Piebald chance
  """
  whitetail_great_one_fur = "animal_visual_variation_great_one_whitetail"
  whitetail_great_one_common_furs = {
    "animal_visual_variation_tan",
    "animal_visual_variation_brown",
    "animal_visual_variation_dark_brown",
  }
  great_one = next((fur for fur in all_furs if fur.name == whitetail_great_one_fur), None)
  if great_one is None:
    return {}

  common_furs = [
    fur for fur in all_furs
    if fur.gender == GENDER_MALE and fur.name in whitetail_great_one_common_furs
  ]
  if len(common_furs) != len(whitetail_great_one_common_furs):
    raise ValueError("Unable to identify all Great One Whitetail common fur weights")

  removed_weight = sum(
    fur.weight - ordinary_updates.get(fur.weight_offset, fur.weight)
    for fur in common_furs
  )
  return {great_one.weight_offset: great_one.weight + removed_weight}

def process(options: dict) -> None:
  rare_fur_increase = float(options["rare_fur_increase"])
  if not 0.0 <= rare_fur_increase <= 100.0:
    raise ValueError("Rare fur percentage must be between 0 and 100")
  if rare_fur_increase == 0.0:
    return
  include_quest_only_furs = bool(options.get("include_quest_only_furs", False))

  updates = []
  global_animal_types_rtpc = mods.open_rtpc(mods.MOD_PATH / FILE)
  animals = global_animal_types_rtpc.child_table[0].child_table
  for animal in animals:
    variations_table = get_variations_table(animal)
    if variations_table is None:
      continue
    all_furs = get_all_furs(variations_table.child_table)
    furs = [fur for fur in all_furs if not fur.is_great_one]
    fur_updates = calculate_fur_weights(
      furs,
      rare_fur_increase,
      include_quest_only_furs,
    )
    fur_updates.update(_whitetail_great_one_updates(all_furs, fur_updates))
    updates.extend(
      {"offset": offset, "value": value}
      for offset, value in fur_updates.items()
    )
  if not updates:
    raise ValueError("No animal fur variations were found")
  logger.debug("Updating %s animal fur weights", len(updates))
  mods.apply_updates_to_file(Path(FILE), updates)


def handle_update(mod_key: str, mod_options: dict, version: str) -> tuple[str, dict]:
  """Convert saves from the old 1.5-100 Rare Fur Percentage slider to the new 0-100 increase scale."""
  if "rare_fur_percentage" not in mod_options:
    if "include_quest_only_furs" in mod_options:
      return mod_key, mod_options
    return mod_key, {**mod_options, "include_quest_only_furs": False}

  old_value = float(mod_options["rare_fur_percentage"])
  old_value = min(100.0, max(1.5, old_value))
  converted_value = (old_value - 1.5) / (100.0 - 1.5) * 100.0
  # The new slider moves in half-percent increments.
  converted_value = round(converted_value * 2.0) / 2.0
  return mod_key, {
    "rare_fur_increase": converted_value,
    "include_quest_only_furs": False,
  }
