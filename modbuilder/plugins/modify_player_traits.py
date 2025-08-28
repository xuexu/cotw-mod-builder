from modbuilder import mods2
try:  # running normally (source)
    from modbuilder.plugins import modify_skills
except ModuleNotFoundError:  # running as an exe (PyInstaller)
    from plugins import modify_skills


DEBUG = False
NAME = "Modify Player Traits"
DESCRIPTION = "Change the character's default attributes. These settings can enable abilities from Perks and Skills trees without needing to spend points."
WARNING = 'If you are also using "Modify Skills" then move this mod higher on the build list to ensure changes are not overridden.'
FILE = "settings/hp_settings/player_skills.bin"
OPTIONS = [
  { "name": "Base Health", "min": 10, "max": 10000, "default": 1000, "initial": 1000, "increment": 10, "note": '"Hardened" skill' },
  { "name": "Fall Damage Reduction Percent", "min": 0, "max": 100, "default": 0, "initial": 0, "increment": 1, "note": '"Impact Resistance" skill' },
  { "name": "Carry Capacity", "min": 1, "max": 1000, "default": 20, "initial": 20, "increment": 1, "note": '"Pack Mule" skill. Capped at 999.9 in-game.' },
  { "name": "Footstep Noise Reduction Percent", "min": 0, "max": 100, "default": 0, "initial": 0, "increment": 1, "note": '"Soft Feet" skill tier 1' },
  { "name": "Vegetation Noise Reduction Percent", "min": 0, "max": 100, "default": 0, "initial": 0, "increment": 1, "note": '"Soft Feet" skill tier 2' },
  { "name": "Reduce Recoil Percent", "min": 0, "max": 100, "default": 0, "initial": 0, "increment": 1, "note": '"Recoil Management" shotgun perk' },
  { "name": "Recoil Recovery Speed", "min": 0.1, "max": 9.9, "default": 1.0, "initial": 1.0, "increment": 0.1, "note": '"Recoil Management" shotgun perk' },
  { "name": "Raise Weapon Speed", "min": 0.05, "max": 10.0, "default": 0.75, "initial": 0.75, "increment": 0.05, "note": '"Fast Shouldering" shotgun perk' },
  { "name": "Clue Detection Range", "min": 1, "max": 100, "default": 20, "initial": 20, "increment": 1, "note": '"Locate Tracks" skill' },
  { "name": "Clue Direction Angle", "min": 1, "max": 90, "default": 90, "initial": 90, "increment": 1, "note": 'Locate Tracks" skill. Smaller size = more accurate indicator.' },
  { "name": "Show Clue Trails on Map", "style": "boolean", "default": False, "initial": False, "note": '"Connect The Dots" skill' },
  { "name": "Spot Duration", "min": 1, "max": 999, "default": 1, "initial": 1, "increment": 1, "note": '"Tag" skill' },
  { "name": "Multiple Spot Count", "min": 1, "max": 99, "default": 1, "initial": 1, "increment": 1, "note": '"Tag" skill' },
  { "name": "Spot Animals With Scope", "style": "boolean", "default": False, "initial": False, "note": '"Sight Spotting" skill' },
  { "name": "Reload While Running", "style": "boolean", "default": False, "initial": False, "note": '"Sprint & Load" handgun perk' },
  { "name": "Reload While Aiming", "style": "boolean", "default": False, "initial": False, "note": '"Muscle Memory" rifle perk tier 1' },
  { "name": "Shop Discount Percent", "min": 0, "max": 100, "default": 0, "initial": 0, "increment": 1, "note": '"Haggle" skill' },
]

def format_options(options: dict) -> str:
  trait_details = []

  base_health = int(options.get("base_health", 1000))
  if base_health != 1000:
    trait_details.append(f"{base_health} HP")

  fall_damage_reduction = int(options.get("fall_damage_reduction_percent", 0))
  if fall_damage_reduction:
    trait_details.append(f"-{fall_damage_reduction}% fall damage")

  carry_capacity = int(options.get("carry_capacity", 20))
  if carry_capacity != 20:
    trait_details.append(f"{carry_capacity}kg")

  footstep_noise_reduction = int(options.get("footstep_noise_reduction_percent", 0))
  if footstep_noise_reduction:
    trait_details.append(f"-{footstep_noise_reduction}% footstep noise")
  vegetation_noise_reduction = int(options.get("vegetation_noise_reduction_percent", 0))
  if vegetation_noise_reduction:
    trait_details.append(f"-{vegetation_noise_reduction}% vegetation noise")

  recoil_percent = int(options.get("reduce_recoil_percent", 0))
  recoil_speed = options.get("recoil_recovery_speed", 1.0)
  if recoil_percent > 0 or recoil_speed > 1:
    trait_details.append(f"-{recoil_percent}% + {recoil_speed} recoil")

  raise_weapon_speed = options.get("raise_weapon_speed", 0.75)
  if raise_weapon_speed != 0.75:
    trait_details.append(f"{raise_weapon_speed}x shouldering")

  clue_range = int(options.get("clue_detection_range", 20))
  clue_direction_indicator_size = int(options.get("clue_direction_angle", 90))
  if clue_range != 20 or clue_direction_indicator_size < 90:
    trait_details.append(f"{clue_range}m + {clue_direction_indicator_size}° clues")

  if options.get("show_clue_trails_on_map", False):
    trait_details.append("clue trail")

  spot_duration = int(options.get("spot_duration", 1))
  spot_count = int(options.get("multiple_spot_count", 1))
  if spot_duration != 1 or spot_count != 1:
    trait_details.append(f"{spot_duration}s + {spot_count} spots")

  if options["spot_animals_with_scope"]:
    trait_details.append(f"scope spot")

  if options["reload_while_running"]:
    trait_details.append(f"run reload")

  if options["reload_while_aiming"]:
    trait_details.append(f"aim reload")

  shop_discount = int(options.get("shop_discount_percent", 0))
  if shop_discount:
    trait_details.append(f"-{shop_discount}% discount")

  if not trait_details:
    trait_details.append("No changes")
  return f"Modify Player Traits ({", ".join(trait_details)})"

def process(options: dict) -> None:
  updates = []

  # Max Health is capped at 9999.9. We let the slider go to 10K for ease of use
  base_health = min(options.get('base_health', 1000), 9999.9)
  updates.append({"coordinates": "B47", "value": f"({base_health})"})
  # Hardened increases max health by 15%
  hardened_health = round(options['base_health'] * 1.15, 1)
  updates.extend(modify_skills.process_hardened({"health": hardened_health}))

  # Fall Damage Reduction = Impact Resistance skill
  if (fall_damage_reduction := options.get("fall_damage_reduction_percent")):
    fall_damage_value = round(1.0 - fall_damage_reduction / 100, 1)
    updates.append({"coordinates": "B48", "value": f"({fall_damage_value})"})
    # Impact Resistance reduces fall damage by 20%
    impact_resistance_damage_reduction = min(fall_damage_reduction + 20, 100)
    updates.extend(modify_skills.process_impact_resistance({"fall_damage_reduction_percent": impact_resistance_damage_reduction}))

  # Carry capacity is capped at 999. We let the slider go to 1000 for ease of use
  base_carry_weight = min(options.get('carry_capacity', 20), 999)
  updates.append({"coordinates": "B44", "value": f"({base_carry_weight})"})
  # Pack Mule increases carry weight by 15%
  pack_mule_weight = round(options['carry_capacity'] * 1.15, 1)
  updates.extend(modify_skills.process_pack_mule({"weight": pack_mule_weight}))

  # Footstep/Vegetation noise reduction = Soft Feet skill
  footstep_noise_reduction = int(options.get("footstep_noise_reduction_percent", 0))
  vegetation_noise_reduction = int(options.get("vegetation_noise_reduction_percent", 0))
  if footstep_noise_reduction or vegetation_noise_reduction:
    footstep_noise_value = round(1.0 - footstep_noise_reduction / 100, 1)
    updates.append({"coordinates": "B33", "value": f"({footstep_noise_value})"})
    vegetation_noise_value = round(1.0 - vegetation_noise_reduction / 100, 1)
    updates.append({"coordinates": "B34", "value": f"({vegetation_noise_value})"})
    # Soft Feet is a flat 20% buff to noise reduction. Only applies footstep noise at tier 1 and applies both at tier 2
    soft_feet_buffs = {
      "footstep_noise_reduction": min(footstep_noise_reduction + 20, 100),
      "vegetation_noise_reduction": min(vegetation_noise_reduction + 20, 100),
    }
    updates.extend(modify_skills.process_soft_feet(soft_feet_buffs))

  # Recoil Management shotgun perk
  recoil_percent = 1 - ( options.get("reduce_recoil_percent", 0) / 100 )
  recoil_speed = options.get("recoil_recovery_speed", 1.0)
  if recoil_percent or recoil_speed != 1.0:
    updates.append({"coordinates": "B30", "value": f"({recoil_percent}, {recoil_speed})"})
    # Recoil Management has 3 tiers. Each tier is a flat 20% buff to recoil percent and speed
    # Subtract for recoil since it starts at 0. Multiply for speed since it starts at 1
    recoil_buffs = {
      "recoil": max(recoil_percent - 0.2, 0),
      "speed": min(recoil_speed * 1.2, 9.9),
      "recoil_2": max(recoil_percent - 0.4, 0),
      "speed_2": min(recoil_speed * 1.4, 9.9),
      "recoil_3": max(recoil_percent - 0.6, 0),
      "speed_3": min(recoil_speed * 1.6, 9.9),
    }
    updates.extend(modify_skills.process_recoil_management(recoil_buffs))

  # Fast Shouldering shotgun perk
  if (speed_multiplier := options.get("raise_weapon_speed")):
    speed_multiplier_text = f"(weapon_category_handguns, {speed_multiplier}\n,weapon_category_rifles, {speed_multiplier}\n,weapon_category_bows, {speed_multiplier}\n,weapon_category_shotguns, {speed_multiplier})"
    updates.append({"coordinates": "B51", "value": speed_multiplier_text})
    # Fast Shouldering has 2 tiers. Each tier is a 33% buff to weapon in/out aim speed
    speed_buffs = {
      "speed_multiplier": min(speed_multiplier * 4/3, 10.0),
      "speed_multiplier_2": min(speed_multiplier * 5/3, 10.0),
    }
    updates.extend(modify_skills.process_fast_shouldering(speed_buffs))

  # Locate Tracks skill
  clue_spawn_distance = min(options.get("clue_detection_range", 20.0), 99.9)  # capped at 99.9
  clue_despawn_distance = min(clue_spawn_distance + 5, 99.9)  # despawn range longer to prevent flickering, capped at 99
  clue_range = f"({clue_spawn_distance}, {clue_despawn_distance})"
  updates.append({"coordinates": "B8", "value": clue_range})
  clue_angle = mods2.least_sigfig(options["clue_direction_angle"])
  clue_cone = "WIDE" if clue_angle >= 90 else "MEDIUM" if 45 < clue_angle < 90 else "NARROW"
  clue_indicator = f"({clue_cone}, {clue_angle})"
  updates.append({"coordinates": "B7", "value": clue_indicator})
  # Locate Tracks has 3 tiers
  # Tier 1+3 are a 25% and 50% buff to cone size
  # Tier 2+3 are a 10m buff to distance with a max of 99
  clue_buffs = {
    "angle": max(round(clue_angle * 0.75, 1), 1),
    "angle_2": round(clue_angle * 0.5, 1),
    "spawn_distance": clue_spawn_distance + 10,
    "despawn_distance": clue_despawn_distance + 10,
    "spawn_distance_2": clue_spawn_distance + 20,
    "despawn_distance_2": clue_despawn_distance + 20,
  }
  updates.extend(modify_skills.process_locate_tracks(clue_buffs))

  if options.get("show_clue_trails_on_map"):
    updates.append({"coordinates": "B26", "value": "(true)"})

  # Tag skill
  spot_duration = options.get("spot_duration", 1)
  spot_count = int(options["multiple_spot_count"])
  updates.append({"coordinates": "B23", "value": f"({spot_duration}, {spot_count})"})
  # Each level of Tag is a .5s increase to spot duration. 1s > 1.5s > 2s
  tag_buffs = {
    "duration": spot_duration * 1.5,
    "duration_2": spot_duration * 2,
    "spottable": spot_count,
    "spottable_2": spot_count * 3,
    "extra_spots_at_level_1": bool(spot_count > 1)  # Tag level 1 doesn't include multiple spots by default
  }
  updates.extend(modify_skills.process_tag(tag_buffs))

  if options["spot_animals_with_scope"]:
    updates.append({"coordinates": "B29", "value": "(true)"})  # "more_than_binocular_spotting"

  if options["reload_while_running"]:
    updates.append({"coordinates": "B70", "value": "(true)"})

  if options["reload_while_aiming"]:
    updates.append({"coordinates": "B22", "value": "(1.0)"})

  # Shop Discount = Haggle Skill
  if (shop_discount := options.get("shop_discount_percent")):
    updates.append({"coordinates": "B28", "value": f"({shop_discount:.1f})"})  # will crash if not formatted with a decimal
    # Haggle reduces all shop costs by 5%
    haggle_discount = min(shop_discount + 5, 100)
    updates.extend(modify_skills.process_haggle({"haggle_percent": haggle_discount}))

  for update in updates:
    update["sheet"] = "skill_component_descriptions" if "sheet" not in update else update["sheet"]
    update["allow_new_data"] = True
  mods2.apply_coordinate_updates_to_file(FILE, updates)
