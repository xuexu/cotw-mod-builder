import re
from enum import Enum
from pathlib import Path

from deca.ff_rtpc import RtpcNode, RtpcProperty, rtpc_from_binary
from modbuilder import mods
from modbuilder.logging_config import get_logger

logger = get_logger(__name__)

DEBUG = False
NAME = "Increase Deployables"
DESCRIPTION = "Increases the number of deployable structures you can place on all reserves."
OPTIONS = [
  {"name": "Deployable Multiplier", "min": 0.1, "max": 20, "default": 1, "increment": 0.1}
]

HASH_MAX_COUNT = 0x8FFF70CE
HASH_WORLD_ITEMS_TABLE = 0xB5D669E4
RESERVE_DIRECTORY = "settings/hp_settings"
RESERVE_FILENAME_PATTERN = re.compile(r"^reserve_(\d+)\.bin$")
TROPHY_LODGE_IDS = {
  5,  # Spring Creek Manor
  7,  # Saseka Safari Lodge
  15,  # Layton Lakes Trophy Cabin
}
class Deployable(str, Enum):
  DECOY = "decoy"
  BAIT_FEEDER = "bait_feeder"
  GROUNDBLIND = "groundblind"
  LAYOUTBLIND = "layoutblind"
  TENT = "tent"
  TREESTAND = "treestand"
  TRIPOD = "tripodstand"
  WATERFOWLBLIND = "waterfowlblind"


def format_options(options: dict) -> str:
  return f"Increase Deployables ({float(options['deployable_multiplier']):g}x)"


def _is_deployable_name(value: str) -> bool:
  return any(deployable.value in value for deployable in Deployable)


def _is_deployable(node: RtpcNode) -> bool:
  return any(
    isinstance(prop.data, bytes)
    and _is_deployable_name(prop.data.decode("utf-8", errors="replace"))
    for prop in node.prop_table
  )


def _world_items(root: RtpcNode, reserve_id: int) -> list[RtpcNode]:
  table = next(
    (node for node in root.child_table if node.name_hash == HASH_WORLD_ITEMS_TABLE),
    None,
  )
  if table is None:
    raise ValueError(f"Unable to parse world items data table for reserve {reserve_id}")
  return table.child_table


def _deployable_max_counts(root: RtpcNode, reserve_id: int) -> list[RtpcProperty]:
  values = []
  for node in _world_items(root, reserve_id):
    if not _is_deployable(node):
      continue
    max_count = node.prop_map.get(HASH_MAX_COUNT)
    if max_count is None:
      raise ValueError(
        f"Deployable node 0x{node.name_hash:08x} on reserve {reserve_id} has no maximum count"
      )
    values.append(max_count)
  return values


def _deployable_updates(root: RtpcNode, multiply: float, reserve_id: int) -> list[dict]:
  values = _deployable_max_counts(root, reserve_id)
  logger.debug("reserve %s has %s deployable limits to update", reserve_id, len(values))
  return [
    {"offset": prop.data_pos, "value": round(prop.data * multiply)}
    for prop in values
  ]


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


def update_all_deployables(source: Path, multiply: float) -> None:
  for file, reserve_id in _reserve_files(source):
    if reserve_id in TROPHY_LODGE_IDS:
      continue
    updates = _deployable_updates(_open_reserve(file), multiply, reserve_id)
    relative_file = file.relative_to(mods.MOD_PATH).as_posix()
    mods.apply_updates_to_file(relative_file, updates)
    logger.debug("Updated all deployable limits in reserve %s", reserve_id)


def process(options: dict) -> None:
  multiply = float(options["deployable_multiplier"])
  if not 0.1 <= multiply <= 20:
    raise ValueError("Deployable multiplier must be between 0.1 and 20.0")
  update_all_deployables(mods.MOD_PATH / RESERVE_DIRECTORY, multiply)
