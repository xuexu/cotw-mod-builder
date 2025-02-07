from typing import List
from modbuilder import mods2

DEBUG=False
NAME = "Increase Level Progression"
DESCRIPTION = "Grant 1 Skill and 1 Perk point per level at lower levels. On a new character, this will provide enough points to fully unlock all trees by level 60. This mod will NOT modify an existing character's skill and perk points."
FILE = "settings/hp_settings/player_rewards.bin"
OPTIONS = [
  {
    "name": "Grant skill and perk points every level",
    "style": "boolean",
    "default": False,
    "initial": False,
    "note": (
      "NOTE: This extra setting is optional and may result in extra, unusable Skill and Perk points.\n"
      "Grant 1 Skill and 1 Perk point every level up to 60. Useful for existing characters below 60.\n"
      "New characters will have enough Skill and Perk points to unlock all trees by level 45.\n"
    )
  },
]

def format(options: dict) -> str:
  points_every_level = options.get("grant_skill_and_perk_points_every_level")
  if points_every_level:
    modifier_text = "every level"
  else:
    modifier_text = "early levels only"
  return f"Increase Level Progression ({modifier_text})"

def process(options: dict) -> None:
  # 44 Skill + 44 Perk points required to unlock all trees
  skill_point_cells = mods2.range_to_coordinates_list("C", 3, 42)
  perk_point_cells = mods2.range_to_coordinates_list("D", 3, 43)
  points_every_level = options.get("grant_skill_and_perk_points_every_level")
  if points_every_level:
    skill_point_cells.extend(mods2.range_to_coordinates_list("C", 43, 61))
    perk_point_cells.extend(mods2.range_to_coordinates_list("D", 44, 61))
  cells_to_update = skill_point_cells + perk_point_cells
  mods2.update_file_at_multiple_coordinates_with_value(FILE, "character_levels", cells_to_update, 1)
