from pathlib import Path

from deca.ff_rtpc import RtpcNode, RtpcProperty
from modbuilder import mods
from modbuilder.logging_config import get_logger

logger = get_logger(__name__)

DEBUG = False
NAME = "Increase Diamond Spawns"
DESCRIPTION = (
  "Increase the chance for new animals to spawn as Diamonds by biasing animals toward the higher end of their weight range."
  "\nDelete old population files to force-respawn all animals."
)
LINKS = [{
  "label": "How to delete population files",
  "url": "https://www.nexusmods.com/thehuntercallofthewild/articles/101",
}]
FILE = "global/global_animal_types.blo"
OPTIONS = [
  {
    "name": "Weight Bias",
    "min": 0.0,
    "max": 0.5,
    "default": 0.0,
    "initial": 0.0,
    "increment": 0.001,
    "note": "Spawned animals will be biased towards higher end of their weight range. Heavier animals = higher score.",
  }
]
PRESETS = [
  {"name": "Game Defaults", "options": [{"name": "weight_bias", "value": 0.0}]},
  {"name": "Very Very Low", "options": [{"name": "weight_bias", "value": 0.001}]},
  {"name": "Very Low", "options": [{"name": "weight_bias", "value": 0.005}]},
  {"name": "Low", "options": [{"name": "weight_bias", "value": 0.025}]},
  {"name": "Medium", "options": [{"name": "weight_bias", "value": 0.05}]},
  {"name": "High", "options": [{"name": "weight_bias", "value": 0.1}]},
  {"name": "Very High", "options": [{"name": "weight_bias", "value": 0.2}]},
  {"name": "Extreme", "options": [{"name": "weight_bias", "value": 0.5}]},
]

HASH_CLASS = 0x1473B179
HASH_WEIGHT_HIGH = 0x29F241F4
HASH_SCORE_HIGH = 0xE3062A0E
HASH_WEIGHT_BIAS = 0xE9450249

SCORING_SETTINGS_CLASS = b"CAnimalTypeScoringSettings"
SCORING_DISTRIBUTION_CLASS = b"SAnimalTypeScoringDistributionSettings"


def format_options(options: dict) -> str:
  return f"Increase Diamond Spawns ({float(options['weight_bias']):g} weight bias)"


def _is_class(node: RtpcNode, class_name: bytes) -> bool:
  class_prop = node.prop_map.get(HASH_CLASS)
  return class_prop is not None and class_prop.data == class_name


def _scoring_distributions(root: RtpcNode) -> list[RtpcNode]:
  if not root.child_table:
    raise ValueError("Unable to parse the global animal types table")

  distributions = []
  for animal in root.child_table[0].child_table:
    scoring_settings = next(
      (child for child in animal.child_table if _is_class(child, SCORING_SETTINGS_CLASS)),
      None,
    )
    if scoring_settings is None:
      continue
    distributions.extend(
      child
      for child in scoring_settings.child_table
      if _is_class(child, SCORING_DISTRIBUTION_CLASS)
    )
  return distributions


def _required_property(node: RtpcNode, name_hash: int) -> RtpcProperty:
  prop = node.prop_map.get(name_hash)
  if prop is None:
    raise ValueError(
      f"Scoring distribution 0x{node.name_hash:08x} is missing property 0x{name_hash:08x}"
    )
  return prop


def _weight_bias_updates(root: RtpcNode, weight_bias: float) -> list[dict]:
  updates = []
  distributions = _scoring_distributions(root)
  if not distributions:
    raise ValueError("No animal scoring distributions were found")

  for node in distributions:
    score_high = _required_property(node, HASH_SCORE_HIGH)
    weight_high = _required_property(node, HASH_WEIGHT_HIGH)
    bias = _required_property(node, HASH_WEIGHT_BIAS)

    # A zero maximum score denotes a distribution that cannot produce a scored diamond.
    if score_high.data <= 0:
      continue
    updates.append({
      "offset": bias.data_pos,
      # Preserve the full float precision; small species otherwise lose low bias settings.
      "value": weight_high.data * weight_bias,
    })

  logger.debug(
    "Updating %s of %s animal scoring distributions",
    len(updates),
    len(distributions),
  )
  return updates


def process(options: dict) -> None:
  weight_bias = float(options["weight_bias"])
  if not 0.0 <= weight_bias <= 0.5:
    raise ValueError("Weight bias must be between 0.0 and 0.5")

  filename = mods.MOD_PATH / FILE
  root = mods.open_rtpc(filename)
  mods.apply_updates_to_file(Path(FILE), _weight_bias_updates(root, weight_bias))
