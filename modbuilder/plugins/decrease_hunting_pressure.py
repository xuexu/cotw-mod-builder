from typing import List

DEBUG = False
NAME = "Decrease Hunting Pressure"
DESCRIPTION = "Hunting pressure reduces animal activity in the area after a kill. Each pressure zone is shown as a purple circle on the map. Overlapping circles will show as brighter purple and have an increased negative effect on animal activity in the area."
FILE = "settings/hp_settings/global_simulation.bin"
OPTIONS = [
  {
    "name": "Decrease Pressure Radius",
    "min": 0,
    "max": 128,
    "default": 128,
    "increment": 1,
    "initial": 128,
    "note": "Radius of the pressure zone in meters"
  },
  {
    "name": "Decrease Pressure Amount Percent",
    "min": 0,
    "max": 100,
    "default": 0,
    "increment": 5,
    "initial": 0,
    "note": "100% = remove the effect of hunting pressure"
  }
]

def format(options: dict) -> str:
  decrease_pressure_radius = int(options['decrease_pressure_radius'])
  decrease_pressure_amount_percent = int(options['decrease_pressure_amount_percent'])
  return f"Decrease Hunting Pressure ({decrease_pressure_radius}m, {decrease_pressure_amount_percent}%)"

def update_values_at_coordinates(options: dict) -> List[dict]:
  decrease_pressure_radius = options['decrease_pressure_radius']
  decrease_pressure_amount_percent = 1.0 - options['decrease_pressure_amount_percent'] / 100
  return [
    {
      # radius
      "coordinates": "B2",
      "sheet": "simulation",
      "value": decrease_pressure_radius,
    },
    {
      # increase value
      "coordinates": "B3",
      "sheet": "simulation",
      "transform": "multiply",
      "value": decrease_pressure_amount_percent
    },
  ]