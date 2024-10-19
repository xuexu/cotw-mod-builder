from modbuilder import mods
from pathlib import Path
import os

DEBUG = False
NAME = "Clean Scope Lenses"
DESCRIPTION = "Replace the dirty, tinted scope lenses with clean, clear glass."
WARNING = "Currently incompatible with Reflex and Red Dot sights."
OPTIONS = [
  { "title": "There are no options. Just add the modification." }
]

class Scope:
  def __init__(self, lens_files: list[Path], bundle_file: Path, name: str) -> None:
    self.file = bundle_file
    self.bundle_file = bundle_file
    self.name = name
    self.lens_files = lens_files

  def __repr__(self) -> str:
    return f"{self.name}, {self.file}, {self.bundle_file}"

def load_scopes() -> list[Scope]:
  scopes = []
  dot_scopes = [
    {"name": "Red Raptor", "folder": "rifle_red_dot_01", "ee": "equipment_sight_rifle_red_dot_01.ee",
     "lenses": [
      "lens_red_dot_01_alpha_dif.ddsc",
      "lens_red_dot_01_alpha_dif.hmddsc",
      "lens_red_dot_02_alpha_dif.ddsc",
      "lens_red_dot_02_alpha_dif.hmddsc",
      "lens_04_mpm.ddsc",
      "lens_04_mpm.hmddsc",
    ]},
    {"name": "Marksman Exakt Reflex", "folder": "sight_reflex_01", "ee": "equipment_sight_reflex_01.ee",
     "lenses": [
      "lens_reflex_01_alpha_dif.ddsc",
      "lens_reflex_01_alpha_dif.hmddsc",
      "lens_reflex_01_mpm.ddsc",
      "lens_reflex_01_mpm.hmddsc"
    ]},
    {"name": "Davani 10mm Reflex", "folder": "sight_reflex_01", "ee": "equipment_sight_reflex_02.ee",
     "lenses": [
      "lens_reflex_01_alpha_dif.ddsc",
      "lens_reflex_01_alpha_dif.hmddsc",
      "lens_reflex_01_mpm.ddsc",
      "lens_reflex_01_mpm.hmddsc"
    ]},
  ]
  base_path = mods.APP_DIR_PATH / "org/editor/entities/hp_weapons/sights"
  for folder in os.listdir(base_path):
    for scope in dot_scopes:
      if folder == scope["folder"]:
        ee_file = base_path / folder / scope["ee"]
        lens_files = scope["lenses"]
        bundle_file = os.path.relpath(ee_file, mods.APP_DIR_PATH / "org")
        from pprint import pprint
        pprint(lens_files)
        scopes.append(Scope(lens_files, bundle_file, scope["name"]))
  return sorted(scopes, key=lambda x: x.name)

def format(options: dict) -> str:
  return "Clean Scope Lenses"

def get_files(options: dict) -> list[str]:
  return []

def merge_files(files: list[str], options: dict) -> None:
  base_path = "models/hp_sights/lenses/textures"
  modded_path = "modded/scope_lenses"
  for file in os.listdir(mods.APP_DIR_PATH / "org" / modded_path):
    src = mods.APP_DIR_PATH / "org" / modded_path / file
    dest = mods.APP_DIR_PATH / "mod/dropzone" / base_path / file
    mods.copy_file(src, dest)
  # scopes = load_scopes()
  # for scope in scopes:
  #   files_to_merge = []
  #   for lens in scope.lens_files:
  #     src = f"{modded_base_path}/{lens}"
  #     dest = f"{base_path}/{lens}"
  #     print(f'{src} to {dest}')
  #     mods.copy_file(mods.APP_DIR_PATH / "org" / src, mods.APP_DIR_PATH / "mod/dropzone" / dest)
  #     #mods.merge_into_archive(lens_file.replace("\\", "/"), scope.bundle_file, lookup)
  #     files_to_merge.append(dest)
  #   print(files_to_merge)
  #   mods.recreate_archive(files_to_merge, scope.bundle_file)

def update_values_at_offset(options: dict) -> list[dict]:
  return []
