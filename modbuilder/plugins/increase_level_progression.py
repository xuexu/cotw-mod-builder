from typing import List
from modbuilder import mods2

DEBUG=False
NAME = "Increase Level Progression"
DESCRIPTION = "Grant both 1 Skill and 1 Perk point at lower levels. On a new character, this will provide enough points to fully unlock all trees by level 60. This mod will NOT modify an existing character's skill and perk points."
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
  points_every_level = options["grant_skill_and_perk_points_every_level"]
  if points_every_level:
    modifier_text = "every level"
  else:
    modifier_text = "early levels only"
  return f"Increase Level Progression ({modifier_text})"

# Total points required to unlock all Perks and Skills:
# Skills: 44 total
#  Stalker: 22
#  Ambusher: 22
# Perks: 44 total
#  Rifle: 11
#  Handgun: 11
#  Shotgun: 11
#  Archery: 11

# Levels 2-37 grant alternating Skill and Perk points. Odd = Skill, Even = Perk
# Every 3 levels after that grant one or the other for a total of 22 Skill and 22 Perk points by level 60

def process(options: dict) -> None:
  # Levels 3-41
  skill_point_cells = ["C4","C6","C8","C10","C12","C14","C16","C18","C20","C22","C24","C26","C28","C30","C32","C34","C36","C38","C39","C40","C41","C42"]
  # Levels 2-42
  perk_point_cells = ["D3","D5","D7","D9","D11","D13","D15","D17","D19","D21","D23","D25","D27","D29","D31","D33","D35","D37","D39","D40","D42","D43"]
  points_every_level = options["grant_skill_and_perk_points_every_level"]
  if points_every_level:
    extra_skill_points_cells = ["C43","C45","C46","C47","C48","C49","C51","C52","C53","C54","C55","C57","C58","C59","C60"]
    skill_point_cells.extend(extra_skill_points_cells)
    extra_perk_point_cells = ["D44","D45","D46","D48","D49","D50","D51","D52","D54","D55","D56","D57","D58","D60","D61"]
    perk_point_cells.extend(extra_perk_point_cells)
  cells_to_update = skill_point_cells + perk_point_cells
  #indices = [.556,.572,.596,.612,.636,652,676,692,716,732,756,772,796,812,836,852,876,892,916,932,956,972,996,1012,1036,1052,1076,1092,1116,1132,1156,1172,1196,1212,1236,1252,1276,1292,1332,1356,1396,1412,1452,1476]
  mods2.update_file_at_multiple_coordinates_with_value(FILE, "character_levels", cells_to_update, 1)