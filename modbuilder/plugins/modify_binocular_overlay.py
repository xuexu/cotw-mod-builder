from modbuilder import mods
import FreeSimpleGUI as sg

DEBUG = False
NAME = "Modify Binocular Overlay"
DESCRIPTION = "Modify the binocular overlay."
OVERLAYS_PATH = mods.APP_DIR_PATH / "org/modded/binocular_overlay"
OVERLAY_FILE_NAME = "hud_i4a3.ddsc"

def get_option_elements() -> sg.Column:
  return sg.Column([
    [sg.Column([
      [sg.T("Binoculars Overlay:", p=((10,0),(10,10))),
       sg.Combo(["Default", "Pill", "Wide"], k="binoculars_overlay", default_value="Default", enable_events=True, p=((10,0),(10,10))),
      ],
    ], vertical_alignment="top"),
     sg.Column([
      [sg.Image(filename=str(OVERLAYS_PATH/"default_preview.png"), k="binoculars_overlay_preview")],
    ], expand_x=True, element_justification="right", p=((150,0),(10,0)))],
  ], expand_x=True)

def handle_event(event: str, window: sg.Window, values: dict) -> None:
  if event == "binoculars_overlay":
    overlay_preview = str(OVERLAYS_PATH / f'{values["binoculars_overlay"].lower()}_preview.png')
    window["binoculars_overlay_preview"].update(overlay_preview)

def add_mod(window: sg.Window, values: dict) -> dict:
  return {
    "key": f"modify_binocular_overlay",
    "invalid": None,
    "options": {
      "binoculars_overlay": values["binoculars_overlay"].lower()
    }
  }

def format(options: dict) -> str:
  return f"Modify Binocular Overlay ({options['binoculars_overlay'].title()})"

def get_files(options: dict) -> list[str]:
  return []

def merge_files(files: list[str], options: dict) -> None:
  overlay = options['binoculars_overlay']
  try:
    mods.copy_file(OVERLAYS_PATH / f"{overlay}.ddsc", mods.MOD_PATH / "ui" / OVERLAY_FILE_NAME)
  except:
    print(f"Error: Could not copy {overlay}.ddsc")
    pass

def update_values_at_offset(options: dict) -> list[dict]:
  return []