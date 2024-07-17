from typing import List

DEBUG=False
NAME = "Modify Resting Cost"
DESCRIPTION = "This mod allows you to the reduce the cost of resting. You will need to sleep once to see the changes take effect."
FILE = "settings/hp_settings/resting_data.bin"
OPTIONS = [
    { 
     "name": "Cost", 
     "style": "slider", 
     "min": 1.0, 
     "max": 300.0, 
     "initial": 250.0,
     "increment": 1.0,
     "note": "Base cost of resting without any multipliers"
    },
    { 
     "name": "Increase and Decrease Multiplier", 
     "style": "slider", 
     "min": 1.0, 
     "max": 5.0, 
     "initial": 2.0,
     "increment": 1.0,
     "note": "Increase in cost before cooldown; decrease in cost after cooldown"
    },   
    { 
     "name": "Max Increase Multiplier", 
     "style": "slider", 
     "min": 1.0, 
     "max": 15.0, 
     "initial": 10.0,
     "increment": 1.0,
     "note": "Max cost increase multiplier"
    },  
    { 
     "name": "Cooldown", 
     "style": "slider", 
     "min": 1.0, 
     "max": 7200.0, 
     "initial": 7200.0,
     "increment": 1.0,
     "note": "Amount of time in seconds before decrease multipler is applied"
    },
]
PRESETS = [
  {
   "name": "Game Defaults", 
   "options": [
     {"name": "cost", "value": 250.0}, 
     {"name": "increase_and_decrease_multiplier", "value": 2.0}, 
     {"name": "max_increase_multiplier", "value": 10.0},
     {"name": "cooldown", "value": 7200.0},
    ] 
  },  
  { 
   "name": "Cheap", 
   "options": [
     {"name": "cost", "value": 1.0}, 
     {"name": "increase_and_decrease_multiplier", "value": 1.0}, 
     {"name": "max_increase_multiplier", "value": 1.0},
     {"name": "cooldown", "value": 1.0},
    ] 
  },  
]

def format(options: dict) -> str:
  cost = int(options['cost'])
  increase_and_decrease_multiplier = int(options['increase_and_decrease_multiplier'])
  max_increase_multiplier = int(options['max_increase_multiplier'])
  cooldown = int(options['cooldown'])
  return f"Modify Resting Cost (${cost}, {increase_and_decrease_multiplier}x, {max_increase_multiplier}x, {cooldown}s)"

def update_values_at_coordinates(options: dict) -> List[dict]:
  cost = options["cost"]
  increase_and_decrease_multiplier = options["increase_and_decrease_multiplier"]
  max_increase_multiplier = options["max_increase_multiplier"]
  cooldown = options["cooldown"]
  
  return [
    {
      # base_cost
      "coordinates": "A2",
      "sheet": "Sheet1",
      "value": cost,
    },
    {
      # increase_multiplier
      "coordinates": "B2",
      "sheet": "Sheet1",
      "value": increase_and_decrease_multiplier,
    },
    {
      # decrease_multiplier
      "coordinates": "C2",
      "sheet": "Sheet1",
      "value": increase_and_decrease_multiplier,
    },
    {
      # max_cost_multiplier
      "coordinates": "D2",
      "sheet": "Sheet1",
      "value": max_increase_multiplier,
    },   
    {
      # time_to_elapse_for_reduction
      "coordinates": "E2",
      "sheet": "Sheet1",
      "value": cooldown,
    },
  ]