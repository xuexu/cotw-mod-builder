from modbuilder import mods
from deca.ff_rtpc import rtpc_from_binary, RtpcNode, RtpcProperty
import json, os
from pathlib import Path

DEBUG=False
NAME = "Modify Lures"
DESCRIPTION = 'Increase the range and duration of different animal lure types. Pair with the "Increase Render Distance" mod to support ranges over 400m.'
FILE = "settings/hp_settings/animal_interest.bin"
OPTIONS = [
    {"name": "Remote Caller Range", "min": 200.0, "max": 990.0, "default": 200.0,  "increment": 10},
    {"name": "Handheld Caller Range", "min": 150.0, "max": 990.0, "default": 150.0,  "increment": 10, "note": "Default range varies from 150-500 meters depending on the caller"},
    {"name": "Scent Range", "min": 200.0, "max": 990.0, "default": 200.0,  "increment": 10, "note": "Wind direction and strength impact effective range"},
    {"name": "Decoy Range", "min": 500.0, "max": 990.0, "default": 500.0,  "increment": 10,},
]

def format(options: dict) -> str:
  remote_caller_range = options["remote_caller_range"]
  handheld_caller_range = options["handheld_caller_range"]
  scent_range = options["scent_range"]
  decoy_range = options["decoy_range"]
  return f"Modify Lures ({remote_caller_range}m, {handheld_caller_range}m, {scent_range}m, {decoy_range}m)"

class Lure:
  __slots__ = (
    'name_hash', 'name', 'pretty_name', 'type', 'range', 'range_offset'
  )

  def __init__(self, equipment: RtpcNode, name_hash: int, name: str) -> None:
    self.name_hash = name_hash
    self.name = name
    self.map_pretty_name()
    self.parse_type()
    self.parse_range(equipment.prop_table)

  def __repr__(self) -> str:
    return f' Name: {self.pretty_name} [{self.name_hash} : {self.name}]  Type: {self.type}  Range: {self.range} @ {self.range_offset}'

  def map_pretty_name(self) -> None:
    self.pretty_name = self.name

  def parse_type(self) -> None:
    if self.name.startswith("equipment_prc_caller"):
      self.type = "remote_caller"
    elif self.name.startswith("equipment_lure_caller"):
      self.type = "handheld_caller"
    elif self.name.startswith("equipment_lure_scent"):
      self.type = "scent"
    elif self.name.startswith("equipment_lure_decoy"):
      self.type = "decoy"
    else:
      raise KeyError(f"Unable to parse equipment type for {self.name} (hash {self.name_hash})")

  def parse_range(self, properties: list[RtpcProperty]) -> None:
    if self.name in [
      "equipment_prc_caller_eastern_wild_turkey_01",
      "equipment_prc_caller_wild_turkey_01",
      "equipment_prc_caller_rio_grande_turkey_01"
    ]:  # these callers have a different range index
      i = 6
    elif self.type in ["remote_caller", "handheld_caller", "decoy"]:
      i = 2
    elif self.type == "scent":
      i = 3
    self.range = properties[i].data
    self.range_offset = properties[i].data_pos

def open_file(filename: Path) -> tuple[RtpcNode, bytearray]:
  with(filename.open("rb")) as f:
    data = rtpc_from_binary(f)
  f_bytes = bytearray(filename.read_bytes())
  return (data.root_node, f_bytes)

def load_lures() -> list[Lure]:
  root, _ext = os.path.splitext(FILE)
  equipment_name_hashes = json.load((mods.LOOKUP_PATH / f"{root}.json").open())["equipment_name_hash"]
  rtpc_root, _data = open_file(mods.get_org_file(FILE))

  lures = []
  for equipment_node in rtpc_root.child_table:
    name = equipment_name_hashes[str(equipment_node.name_hash)]
    if name:
      lures.append(Lure(equipment_node, equipment_node.name_hash, name))
  return lures

def format_range_updates(lures: list[Lure], new_ranges: dict) -> list[tuple[int, float]]:
  offsets_and_values = []
  for lure in lures:
    range = new_ranges[lure.type]
    offsets_and_values.append((lure.range_offset, range))
  return offsets_and_values

def process(options: dict) -> None:
  remote_caller_range = options["remote_caller_range"]
  handheld_caller_range = options["handheld_caller_range"]
  scent_range = options["scent_range"]
  decoy_range = options["decoy_range"]

  new_ranges = {
    "remote_caller": remote_caller_range,
    "handheld_caller": handheld_caller_range,
    "scent": scent_range,
    "decoy": decoy_range
  }

  lures = load_lures()
  offsets_and_new_values = format_range_updates(lures, new_ranges)
  mods.update_file_at_offsets_with_values(FILE, offsets_and_new_values)
