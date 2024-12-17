from modbuilder import mods

DEBUG = False
NAME = "Increase Weapon FOV"
DESCRIPTION = 'Increase the first-person field of view when holding a weapon, effectively "zooming out" the camera so you can see more of your weapon skin. This is separate from the FOV setting in-game.'
WARNING = "The first-person camera only renders the player's arms and weapon. Settings higher than ~60 may show \"floating\" arms with no body when holding some weapons."
OPTIONS = [
  {
    "name": "First-Person Weapon FOV",
    "min": 33,
    "max": 90,
    "default": 33,
    "initial": 33,
    "increment": 1
  }
]

FIRST_PERSON_FOV_FILE = "editor/entities/cameras/default_first_person.ctunec"
PRONE_FOV_FILE = "editor/entities/cameras/prone_first_person.ctunec"

def format(options: dict) -> str:
  weapon_fov = options["first-person_weapon_fov"]
  return f"Increase Weapon FOV ({int(weapon_fov)})"

def get_files(options: dict) -> list[str]:
  fov_files = [FIRST_PERSON_FOV_FILE, PRONE_FOV_FILE]
  return fov_files

def process(options: dict) -> None:
  weapon_fov = options["first-person_weapon_fov"]
  mods.update_file_at_offset(FIRST_PERSON_FOV_FILE, 248, weapon_fov)
  mods.update_file_at_offset(PRONE_FOV_FILE, 248, weapon_fov)
