import math
import re
from dataclasses import dataclass
from pathlib import Path

from deca.ff_rtpc import RtpcNode, RtpcProperty, rtpc_from_binary
from modbuilder import mods
from modbuilder.logging_config import get_logger

logger = get_logger(__name__)

DEBUG = False
NAME = "Increase Reserve Population"
DESCRIPTION = (
  "Increases the number of animals that get populated when loading a reserve for the first time. All species on all reserves are increased by the multiplier."
  "\nUse Modify Animal Population instead for precise control of male/female ratios and total animal counts per-species."
)
WARNING = (
  "Existing population save files must be deleted for this mod to work. Click the link above for instructions."
  "\nLarge population sizes can cause crashes, especially when using Increase Render Distance. Recommended max multiplier is 3.0."
  "\nDo not combine this with custom populations from Modify Animal Population."
)
LINKS = [{
  "label": "How to delete population files",
  "url": "https://www.nexusmods.com/thehuntercallofthewild/articles/101",
}]
OPTIONS = [
  {"name": "Population Multiplier", "min": 0.1, "max": 8, "default": 1, "increment": 0.1}
]

HASH_GROUP_FEMALES = 0x9A76518B
HASH_GROUP_MALES = 0x2A439C8A
HASH_POPULATION_TABLE = 0x1DB9A1B5
HASH_SOLO_FEMALES = 0x0C99856C
HASH_SOLO_MALES = 0x63F5F198
HASH_SPECIES_ID = 0x19B8918C
FEMALE_POPULATION_HASHES = {HASH_SOLO_FEMALES, HASH_GROUP_FEMALES}
MALE_POPULATION_HASHES = {HASH_SOLO_MALES, HASH_GROUP_MALES}
POPULATION_HASHES = MALE_POPULATION_HASHES | FEMALE_POPULATION_HASHES
RESERVE_DIRECTORY = "settings/hp_settings"
RESERVE_FILENAME_PATTERN = re.compile(r"^reserve_(\d+)\.bin$")
TROPHY_LODGE_IDS = {
  5,  # Spring Creek Manor
  7,  # Saseka Safari Lodge
  15,  # Layton Lakes Trophy Cabin
}
@dataclass
class AnimalPopulationProperties:
  species_id: int
  values: list[RtpcProperty]


def format_options(options: dict) -> str:
  multiply = options["population_multiplier"]
  return f"Increase Reserve Population ({multiply}x)"


def _population_nodes(root: RtpcNode) -> list[RtpcNode]:
  table = next(
    (node for node in root.child_table if node.name_hash == HASH_POPULATION_TABLE),
    None,
  )
  return table.child_table if table is not None else []


def _find_population_values(node: RtpcNode) -> list[RtpcProperty]:
  values = [prop for prop in node.prop_table if prop.name_hash in POPULATION_HASHES]
  for child in node.child_table:
    values.extend(_find_population_values(child))
  return values


def _animal_populations(root: RtpcNode, reserve_id: int) -> list[AnimalPopulationProperties]:
  animal_nodes = _population_nodes(root)
  if not animal_nodes:
    raise ValueError(f"Unable to parse animal data table for reserve {reserve_id}")

  animals = []
  for index, node in enumerate(animal_nodes):
    species = node.prop_map.get(HASH_SPECIES_ID)
    if species is None:
      raise ValueError(f"Animal {index} on reserve {reserve_id} has no species ID")
    values = _find_population_values(node)
    if not values:
      raise ValueError(
        f"Unable to parse population values for species {species.data} on reserve {reserve_id}"
      )
    animals.append(AnimalPopulationProperties(species.data, values))
  return animals


def _allocate_scaled_values(values: list[RtpcProperty], multiply: float) -> list[int]:
  """Scale one sex's pools while making their sum match the rounded target."""
  if not values:
    return []

  scaled = [prop.data * multiply for prop in values]
  allocated = [math.floor(value) for value in scaled]
  target = round(sum(prop.data for prop in values) * multiply)
  remainder = target - sum(allocated)
  order = sorted(
    range(len(values)),
    key=lambda index: (scaled[index] - allocated[index], values[index].data),
    reverse=True,
  )
  for index in order[:remainder]:
    allocated[index] += 1
  return allocated


def _population_updates(root: RtpcNode, multiply: float, reserve_id: int) -> list[dict]:
  updates = []
  for animal in _animal_populations(root, reserve_id):
    logger.debug(
      "species %s has %s population values to update",
      animal.species_id,
      len(animal.values),
    )
    for hashes in (MALE_POPULATION_HASHES, FEMALE_POPULATION_HASHES):
      values = [prop for prop in animal.values if prop.name_hash in hashes]
      scaled_values = _allocate_scaled_values(values, multiply)
      updates.extend(
        {"offset": prop.data_pos, "value": value}
        for prop, value in zip(values, scaled_values)
      )
  return updates


def _open_reserve(filename: Path) -> RtpcNode:
  with filename.open("rb") as file:
    return rtpc_from_binary(file).root_node


def _reserve_files(source: Path):
  for file in source.glob("reserve_*.bin"):
    match = RESERVE_FILENAME_PATTERN.fullmatch(file.name)
    if match is None:
      logger.warning("Ignoring invalid reserve filename: %s", file.name)
      continue
    yield file, int(match.group(1))


def get_files(options: dict) -> list[str]:
  source = mods.get_org_file(RESERVE_DIRECTORY)
  return [
    file.relative_to(mods.ORG_DIR_PATH).as_posix()
    for file, reserve_id in _reserve_files(source)
    if reserve_id not in TROPHY_LODGE_IDS
  ]


def update_all_populations(source: Path, multiply: float) -> None:
  for file, reserve_id in _reserve_files(source):
    if reserve_id in TROPHY_LODGE_IDS:
      continue
    updates = _population_updates(_open_reserve(file), multiply, reserve_id)
    relative_file = file.relative_to(mods.MOD_PATH).as_posix()
    mods.apply_updates_to_file(relative_file, updates)
    logger.debug("Updated all population values in reserve %s", reserve_id)


def process(options: dict) -> None:
  multiply = float(options["population_multiplier"])
  if not 0.1 <= multiply <= 8:
    raise ValueError("Population multiplier must be between 0.1 and 8.0")
  update_all_populations(mods.MOD_PATH / RESERVE_DIRECTORY, multiply)
