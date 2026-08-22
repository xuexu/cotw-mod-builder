import re
from dataclasses import dataclass
from pathlib import Path

import FreeSimpleGUI as sg

from deca.ff_rtpc import RtpcNode, RtpcProperty
from modbuilder import mods

DEBUG = False
NAME = "Modify Animal Population"
DESCRIPTION = (
  "Modify the male/female population targets for one species on a reserve."
  "\nThe game uses these values when generating a new population file. This plugin attempts to preserves the species' default solo/group structure."
  "\nUse the Advanced editor for exact control over values like solo animal counts and group compositions."
)
WARNING = (
  "Existing population save files must be deleted for this mod to work. Click the link above for instructions."
  "\nDo not combine this with multipliers from Increase Reserve Population. A reserve population of 20,000 or more may cause crashes."
)
LINKS = [{
  "label": "How to delete population files",
  "url": "https://www.nexusmods.com/thehuntercallofthewild/articles/101",
}]

RESERVE_FILE = "settings/hp_settings/reserve_{reserve_id}.bin"
RESERVE_FILENAME_PATTERN = re.compile(r"^reserve_(\d+)\.bin$")
ANIMAL_TYPES_FILE = "global/global_animal_types.blo"
TROPHY_LODGE_IDS = {
  5,  # Spring Creek Manor
  7,  # Saseka Safari Lodge
  15,  # Layton Lakes Trophy Cabin
}
MAX_SPECIES_POPULATION = 20_000
RESERVE_DISPLAY_NAMES = {
  0: "Hirschfelden Hunting Reserve",
  1: "Layton Lake District",
  2: "Medved-Taiga National Park",
  3: "Vurhonga Savanna",
  4: "Parque Fernando",
  6: "Yukon Valley Nature Reserve",
  8: "Cuatro Colinas Game Reserve",
  9: "Silver Ridge Peaks",
  10: "Te Awaroa National Park",
  11: "Rancho del Arroyo",
  12: "Mississippi Acres Preserve",
  13: "Revontuli Coast",
  14: "New England Mountains",
  16: "Emerald Coast",
  17: "Sundarpatan Nepal Hunting Reserve",
  18: "Salzwiesen Park",
  19: "Askiy Ridge Hunting Preserve",
  20: "Tórr nan Sìthean Hunting Reserve",
  21: "Intisuyu Peru Hunting Reserve",
}

# Shared hashes in reserve_X.bin and global_animal_types.blo.
HASH_NAME = 0xD31AB684
HASH_SPECIES_ID = 0x19B8918C
HASH_POPULATION_TABLE = 0x1DB9A1B5

# Population values. Counts are desired generator inputs; the generated count
# can be slightly lower when the game cannot fit the final valid group.
HASH_SOLO_FEMALES = 0x0C99856C
HASH_SOLO_MALES = 0x63F5F198
HASH_GROUP_MALES = 0x2A439C8A
HASH_GROUP_FEMALES = 0x9A76518B

# Per-template group composition constraints.
HASH_MAX_GROUP_SIZE = 0x37989072
HASH_MAX_MALES = 0xFEE196FE
HASH_MIN_FEMALES = 0xD58B7732
HASH_MIN_MALES = 0x58B443A8
HASH_MAX_FEMALES = 0x34CCA914

@dataclass
class GroupTemplate:
  male_population: RtpcProperty
  female_population: RtpcProperty
  min_males: RtpcProperty | None
  max_males: RtpcProperty | None
  min_females: RtpcProperty | None
  max_females: RtpcProperty | None
  max_group_size: RtpcProperty | None


@dataclass
class AnimalPopulation:
  species_id: int
  name: str
  display_name: str
  solo_males: RtpcProperty | None
  solo_females: RtpcProperty | None
  group_templates: list[GroupTemplate]

  @property
  def male_population(self) -> int:
    return sum(prop.data for prop in self._male_components())

  @property
  def female_population(self) -> int:
    return sum(prop.data for prop in self._female_components())

  @property
  def total_population(self) -> int:
    return self.male_population + self.female_population

  def _male_components(self) -> list[RtpcProperty]:
    values = [self.solo_males] if self.solo_males else []
    return values + [template.male_population for template in self.group_templates]

  def _female_components(self) -> list[RtpcProperty]:
    values = [self.solo_females] if self.solo_females else []
    return values + [template.female_population for template in self.group_templates]


@dataclass
class ReservePopulation:
  reserve_id: int
  name: str
  display_name: str
  file: str
  animals: list[AnimalPopulation]


def _decode_string(value: bytes | str) -> str:
  return value.decode("utf-8") if isinstance(value, bytes) else str(value)


def _display_name(name: str) -> str:
  return " ".join(part.capitalize() for part in name.split("_"))


def _load_species_names() -> dict[int, str]:
  root = mods.open_rtpc(mods.get_org_file(ANIMAL_TYPES_FILE))
  names = {}
  for animal in root.child_table[0].child_table:
    species_prop = animal.prop_map.get(HASH_SPECIES_ID)
    name_prop = animal.prop_map.get(HASH_NAME)
    if species_prop and name_prop:
      names[species_prop.data] = _decode_string(name_prop.data)
  return names


def _population_nodes(root: RtpcNode) -> list[RtpcNode]:
  population_table = next(
    (node for node in root.child_table if node.name_hash == HASH_POPULATION_TABLE),
    None,
  )
  if population_table is None:
    return []
  return population_table.child_table


def _find_properties(node: RtpcNode, name_hash: int) -> list[RtpcProperty]:
  properties = [prop for prop in node.prop_table if prop.name_hash == name_hash]
  for child in node.child_table:
    properties.extend(_find_properties(child, name_hash))
  return properties


def _find_property(node: RtpcNode, name_hash: int) -> RtpcProperty | None:
  properties = _find_properties(node, name_hash)
  return properties[0] if properties else None


def _parse_group_template(node: RtpcNode) -> GroupTemplate | None:
  male_population = node.prop_map.get(HASH_GROUP_MALES)
  female_population = node.prop_map.get(HASH_GROUP_FEMALES)
  if not male_population or not female_population:
    return None
  return GroupTemplate(
    male_population=male_population,
    female_population=female_population,
    min_males=node.prop_map.get(HASH_MIN_MALES),
    max_males=node.prop_map.get(HASH_MAX_MALES),
    min_females=node.prop_map.get(HASH_MIN_FEMALES),
    max_females=node.prop_map.get(HASH_MAX_FEMALES),
    max_group_size=node.prop_map.get(HASH_MAX_GROUP_SIZE),
  )


def _find_group_templates(node: RtpcNode) -> list[GroupTemplate]:
  templates = []
  template = _parse_group_template(node)
  if template:
    templates.append(template)
  for child in node.child_table:
    templates.extend(_find_group_templates(child))
  return templates


def _parse_animal(node: RtpcNode, species_names: dict[int, str]) -> AnimalPopulation:
  species_prop = node.prop_map.get(HASH_SPECIES_ID)
  if species_prop is None:
    raise ValueError(f"Population node 0x{node.name_hash:08x} has no species ID")
  species_id = species_prop.data
  name = species_names.get(species_id, f"species_{species_id}")
  return AnimalPopulation(
    species_id=species_id,
    name=name,
    display_name=_display_name(name),
    solo_males=_find_property(node, HASH_SOLO_MALES),
    solo_females=_find_property(node, HASH_SOLO_FEMALES),
    group_templates=_find_group_templates(node),
  )


def _load_reserve(file: Path, species_names: dict[int, str]) -> ReservePopulation:
  reserve_id = int(file.stem.rsplit("_", 1)[-1])
  root = mods.open_rtpc(file)
  name_prop = root.prop_map.get(HASH_NAME)
  name = _decode_string(name_prop.data) if name_prop else f"reserve_{reserve_id}"
  animals = [_parse_animal(node, species_names) for node in _population_nodes(root)]
  # Some reserves contain disabled placeholder species with every population input set to zero
  # There is no established template to scale for those.
  # Skip for now. This plugin is not currently built to add new data to RTPC files
  animals = [animal for animal in animals if animal.total_population > 0]
  animals.sort(key=lambda animal: animal.display_name)
  return ReservePopulation(
    reserve_id=reserve_id,
    name=name,
    display_name=f"{reserve_id}: {RESERVE_DISPLAY_NAMES.get(reserve_id, name)}",
    file=RESERVE_FILE.format(reserve_id=reserve_id),
    animals=animals,
  )


def load_reserves(species_names: dict[int, str]) -> list[ReservePopulation]:
  reserves = []
  for file in mods.get_org_file("settings/hp_settings").glob("reserve_*.bin"):
    match = RESERVE_FILENAME_PATTERN.fullmatch(file.name)
    if match is None:
      continue
    reserve_id = int(match.group(1))
    if reserve_id not in TROPHY_LODGE_IDS:
      reserve = _load_reserve(file, species_names)
      if reserve.animals:
        reserves.append(reserve)
  return sorted(reserves, key=lambda reserve: reserve.reserve_id)


def _get_reserve(reserve_id: int) -> ReservePopulation | None:
  return next((reserve for reserve in ALL_RESERVES if reserve.reserve_id == reserve_id), None)


def _get_animal(reserve: ReservePopulation, species_id: int) -> AnimalPopulation | None:
  return next((animal for animal in reserve.animals if animal.species_id == species_id), None)


def _selected_reserve(values: dict) -> ReservePopulation | None:
  selection = values.get("animal_population_reserve")
  if selection is None:
    return None
  try:
    # Reserve names are presentation only. The stable numeric prefix is the selection identity.
    reserve_id = int(str(selection).split(":", 1)[0])
  except (TypeError, ValueError):
    return None
  return _get_reserve(reserve_id)


def _selected_animal(reserve: ReservePopulation | None, values: dict) -> AnimalPopulation | None:
  if reserve is None:
    return None
  display_name = values.get("animal_population_species")
  return next((animal for animal in reserve.animals if animal.display_name == display_name), None)


def _template_key(index: int, field: str) -> str:
  return f"animal_population_template_{index}_{field}"


def _max_group_templates() -> int:
  return max(
    (len(animal.group_templates) for reserve in ALL_RESERVES for animal in reserve.animals),
    default=0,
  )


def _set_advanced_visibility(window: sg.Window, enabled: bool) -> None:
  window["animal_population_males"].update(disabled=enabled)
  window["animal_population_females"].update(disabled=enabled)
  window["animal_population_advanced_column"].update(visible=enabled)
  window.visibility_changed()
  window["options"].contents_changed()


def _update_details_text(window: sg.Window, text: str) -> None:
  """Update the population summary and fit its height to the displayed lines."""
  details = window["animal_population_details"]
  details.update(text)
  height = max(3, min(16, text.count("\n") + 1))
  widget = getattr(details, "Widget", None)
  if widget is None:
    widget = getattr(details, "TKText", None)
  if widget is not None:
    widget.configure(height=height)
  window.visibility_changed()
  window["options"].contents_changed()


def _group_template_elements(index: int) -> sg.Frame:
  return sg.Frame(
    f"Group template {index + 1}",
    [
      [
        sg.T("Group males:"),
        sg.Input(
          "",
          key=_template_key(index, "males"),
          size=(8, 1),
          enable_events=True,
          pad=((0, 20), (0, 0)),
        ),
        sg.T("Group females:"),
        sg.Input(
          "",
          key=_template_key(index, "females"),
          size=(8, 1),
          enable_events=True,
          pad=((0, 20), (0, 0)),
        ),
        sg.T("Maximum total size:"),
        sg.Input("", key=_template_key(index, "max_size"), size=(6, 1), enable_events=True),
      ],
      [
        sg.T("Males per group min/max:"),
        sg.Input(
          "",
          key=_template_key(index, "min_males"),
          size=(6, 1),
          enable_events=True,
          pad=((0, 5), (0, 0)),
        ),
        sg.Input(
          "",
          key=_template_key(index, "max_males"),
          size=(6, 1),
          enable_events=True,
          pad=((0, 20), (0, 0)),
        ),
        sg.T("Females per group min/max:"),
        sg.Input(
          "",
          key=_template_key(index, "min_females"),
          size=(6, 1),
          enable_events=True,
          pad=((0, 5), (0, 0)),
        ),
        sg.Input("", key=_template_key(index, "max_females"), size=(6, 1), enable_events=True),
      ],
    ],
    key=_template_key(index, "frame"),
    visible=False,
  )


def get_option_elements() -> sg.Column:
  layout = [
    [
      sg.T("Reserve:", size=(12, 1)),
      sg.Combo(
        [reserve.display_name for reserve in ALL_RESERVES],
        key="animal_population_reserve",
        readonly=True,
        enable_events=True,
        size=(42, 1),
      ),
    ],
    [
      sg.T("Species:", size=(12, 1)),
      sg.Combo(
        [],
        key="animal_population_species",
        readonly=True,
        disabled=True,
        enable_events=True,
        size=(42, 1),
      ),
    ],
    [
      sg.T("Male target:", size=(12, 1)),
      sg.Input("", key="animal_population_males", size=(10, 1), enable_events=True),
      sg.T("Female target:", pad=((25, 5), (0, 0))),
      sg.Input("", key="animal_population_females", size=(10, 1), enable_events=True),
    ],
    [
      sg.Multiline(
        "Select a reserve and species to load population details.",
        key="animal_population_details",
        size=(110, 3),
        disabled=True,
        expand_x=True,
      ),
    ],
    [
      sg.Checkbox(
        "Advanced Editor: solo counts and group templates",
        key="animal_population_advanced",
        enable_events=True,
      ),
    ],
    [
      sg.pin(sg.Column(
        [
          [
            sg.T("Solo males:"),
            sg.Input(
              "",
              key="animal_population_solo_males",
              size=(8, 1),
              enable_events=True,
              pad=((0, 20), (0, 0)),
            ),
            sg.T("Solo females:"),
            sg.Input(
              "",
              key="animal_population_solo_females",
              size=(8, 1),
              enable_events=True,
              pad=((0, 20), (0, 0)),
            ),
          ],
          *[[_group_template_elements(index)] for index in range(_max_group_templates())],
        ],
        key="animal_population_advanced_column",
        visible=False,
        expand_x=True,
      )),
    ],
  ]
  return sg.Column(layout)


def handle_event(event: str, window: sg.Window, values: dict) -> None:
  if event == "animal_population_advanced":
    _set_advanced_visibility(window, bool(values.get("animal_population_advanced")))

  if event == "animal_population_reserve":
    reserve = _selected_reserve(values)
    animal_names = [animal.display_name for animal in reserve.animals] if reserve else []
    window["animal_population_species"].update(values=animal_names, value="", disabled=not animal_names)
    window["animal_population_males"].update("")
    window["animal_population_females"].update("")
    window["animal_population_solo_males"].update("")
    window["animal_population_solo_females"].update("")
    for index in range(_max_group_templates()):
      window[_template_key(index, "frame")].update(visible=False)
    _update_details_text(window, "Select a species to load its default population targets.")
    window.visibility_changed()
    window["options"].contents_changed()

  if event == "animal_population_species":
    reserve = _selected_reserve(values)
    animal = _selected_animal(reserve, values)
    if animal:
      window["animal_population_males"].update(str(animal.male_population))
      window["animal_population_females"].update(str(animal.female_population))
      values["animal_population_males"] = str(animal.male_population)
      values["animal_population_females"] = str(animal.female_population)
      solo_males = animal.solo_males.data if animal.solo_males else 0
      solo_females = animal.solo_females.data if animal.solo_females else 0
      window["animal_population_solo_males"].update(
        str(solo_males),
        disabled=animal.solo_males is None,
      )
      window["animal_population_solo_females"].update(
        str(solo_females),
        disabled=animal.solo_females is None,
      )
      values["animal_population_solo_males"] = str(solo_males)
      values["animal_population_solo_females"] = str(solo_females)
      for index in range(_max_group_templates()):
        visible = index < len(animal.group_templates)
        window[_template_key(index, "frame")].update(visible=visible)
        if not visible:
          continue
        template = animal.group_templates[index]
        template_values = {
          "males": template.male_population.data,
          "females": template.female_population.data,
          "min_males": template.min_males.data,
          "max_males": template.max_males.data,
          "min_females": template.min_females.data,
          "max_females": template.max_females.data,
          "max_size": template.max_group_size.data,
        }
        for field, value in template_values.items():
          window[_template_key(index, field)].update(str(value))
          values[_template_key(index, field)] = str(value)
      _update_population_details(window, values, animal)
      window.visibility_changed()
      window["options"].contents_changed()

  if (
    event in {
      "animal_population_males",
      "animal_population_females",
      "animal_population_solo_males",
      "animal_population_solo_females",
      "animal_population_advanced",
    }
    or event.startswith("animal_population_template_")
  ):
    animal = _selected_animal(_selected_reserve(values), values)
    if animal:
      _update_population_details(window, values, animal)


def _non_negative_value(values: dict, key: str, label: str) -> tuple[int | None, str | None]:
  value = mods.coerce_int(values.get(key))
  if value is None or value < 0:
    return None, f"{label} must be a non-negative whole number"
  return value, None


def _population_limit_warning(males: int, females: int) -> str | None:
  if males + females >= MAX_SPECIES_POPULATION:
    return f"Reserve population of {MAX_SPECIES_POPULATION:,} or more may cause crashes."
  return None


def _advanced_options(animal: AnimalPopulation, values: dict) -> tuple[dict | None, str | None]:
  solo_males, error = _non_negative_value(
    values,
    "animal_population_solo_males",
    "Solo males",
  )
  if error:
    return None, error
  solo_females, error = _non_negative_value(
    values,
    "animal_population_solo_females",
    "Solo females",
  )
  if error:
    return None, error
  if animal.solo_males is None and solo_males:
    return None, "This species has no solo-male population field"
  if animal.solo_females is None and solo_females:
    return None, "This species has no solo-female population field"

  template_options = []
  labels = {
    "males": "grouped males",
    "females": "grouped females",
    "min_males": "minimum males per group",
    "max_males": "maximum males per group",
    "min_females": "minimum females per group",
    "max_females": "maximum females per group",
    "max_size": "maximum total group size",
  }
  for index, _template in enumerate(animal.group_templates):
    template_values = {}
    for field, label in labels.items():
      value, error = _non_negative_value(
        values,
        _template_key(index, field),
        f"Group template {index + 1} {label}",
      )
      if error:
        return None, error
      template_values[field] = value

    if template_values["min_males"] > template_values["max_males"]:
      return None, f"Template {index + 1} minimum males cannot exceed maximum males"
    if template_values["min_females"] > template_values["max_females"]:
      return None, f"Template {index + 1} minimum females cannot exceed maximum females"
    if template_values["min_males"] + template_values["min_females"] > template_values["max_size"]:
      return None, f"Template {index + 1} minimum composition exceeds its maximum total size"
    if max(template_values["max_males"], template_values["max_females"]) > template_values["max_size"]:
      return None, f"Template {index + 1} sex maximum exceeds its maximum total size"
    if template_values["males"] and template_values["max_males"] == 0:
      return None, f"Template {index + 1} has grouped males but permits no males per group"
    if template_values["females"] and template_values["max_females"] == 0:
      return None, f"Template {index + 1} has grouped females but permits no females per group"
    if not template_values["males"] and template_values["min_males"]:
      return None, f"Template {index + 1} requires males but its male pool is zero"
    if not template_values["females"] and template_values["min_females"]:
      return None, f"Template {index + 1} requires females but its female pool is zero"
    if template_values["males"] + template_values["females"] and template_values["max_size"] == 0:
      return None, f"Template {index + 1} has animals but its maximum size is zero"
    template_options.append(template_values)

  return {
    "solo_males": solo_males,
    "solo_females": solo_females,
    "group_templates": template_options,
  }, None


def _template_values(template: GroupTemplate) -> dict[str, int]:
  return {
    "males": template.male_population.data,
    "females": template.female_population.data,
    "min_males": template.min_males.data,
    "max_males": template.max_males.data,
    "min_females": template.min_females.data,
    "max_females": template.max_females.data,
    "max_size": template.max_group_size.data,
  }


def _ceil_div(value: int, divisor: int) -> int:
  return (value + divisor - 1) // divisor


def _estimate_template_groups(values: dict[str, int]) -> tuple[int, int, int]:
  males = values["males"]
  females = values["females"]
  if males + females == 0:
    return 0, 0, 0

  pools = [
    ("male", males, values["min_males"], values["max_males"]),
    ("female", females, values["min_females"], values["max_females"]),
  ]
  active_pools = [(name, target, minimum, maximum) for name, target, minimum, maximum in pools if target]
  for name, _target, _minimum, maximum in active_pools:
    if maximum == 0:
      raise ValueError(f"{name} pool cannot fit the template")

  # Fixed composition makes the stopping point deterministic. The last group
  # can overshoot a target when the pool is not divisible by its per-group
  # count, so use ceiling division.
  if all(minimum == maximum for _name, _target, minimum, maximum in active_pools):
    groups = min(
      _ceil_div(target, maximum)
      for _name, target, _minimum, maximum in active_pools
    )
    return groups, groups, groups

  # Flexible generation stops when the first sex pool reaches its target. Each
  # active pool therefore provides an earliest and latest possible stopping
  # point; the first exhausted pool controls the overall group count.
  minimum_groups = min(
    _ceil_div(target, maximum)
    for _name, target, _minimum, maximum in active_pools
  )
  finite_maximums = [
    _ceil_div(target, minimum)
    for _name, target, minimum, _maximum in active_pools
    if minimum
  ]
  if not finite_maximums:
    raise ValueError("group composition has no positive per-group minimum")
  maximum_groups = min(finite_maximums)
  estimates = [
    target / ((minimum + maximum) / 2)
    for _name, target, minimum, maximum in active_pools
    if minimum + maximum
  ]
  estimate = round(min(estimates))
  estimate = min(max(estimate, minimum_groups), maximum_groups)
  return estimate, minimum_groups, maximum_groups


def _population_summary(
  label: str,
  solo_males: int,
  solo_females: int,
  templates: list[dict[str, int]],
  show_templates: bool = True,
) -> str:
  grouped_males = sum(template["males"] for template in templates)
  grouped_females = sum(template["females"] for template in templates)
  males = solo_males + grouped_males
  females = solo_females + grouped_females
  solo_total = solo_males + solo_females
  template_estimates = [_estimate_template_groups(template) for template in templates]
  minimum_total = 0
  maximum_total = 0
  for _estimate, minimum, maximum in template_estimates:
    minimum_total += minimum
    maximum_total += maximum

  group_total_text = (
    str(minimum_total)
    if minimum_total == maximum_total
    else f"{minimum_total}-{maximum_total}"
  )
  animal_label = "total animals" if label == "Default" else "animals"
  lines = [
    f"{label}: {males + females} {animal_label} ({males} male, {females} female)  |  "
    f"{solo_total} solo ({solo_males} male, {solo_females} female)  |  {group_total_text} groups"
  ]

  if not show_templates:
    return "\n".join(lines)

  for index, (template, (_estimate, minimum, maximum)) in enumerate(
    zip(templates, template_estimates)
  ):
    group_text = str(minimum) if minimum == maximum else f"{minimum}-{maximum}"
    lines.append(
      f"  Template {index + 1}: {template['males'] + template['females']} animals in "
      f"{group_text} groups  |  {template['min_males'] + template['min_females']}-"
      f"{template['max_size']} per group ({template['min_males']}-{template['max_males']} male, "
      f"{template['min_females']}-{template['max_females']} female)"
    )
    if template["max_males"] + template["max_females"] > template["max_size"]:
      lines.append(
        f"    WARNING: max males + females per group is {template['max_males'] + template['max_females']} "
        f"but max group size is only {template['max_size']}; the game may not fully generate all desired animals "
        "if it fills too many groups with one sex, reaches the 'group' total for that sex, and cannot create any more valid groups."
      )

  return "\n".join(lines)


def _automatic_options(animal: AnimalPopulation, males: int, females: int) -> dict:
  allocations = _allocate_structural_population(animal, males, females)
  component_index = 0
  if animal.solo_males is not None or animal.solo_females is not None:
    solo_males, solo_females = allocations[0]
    component_index = 1
  else:
    solo_males, solo_females = 0, 0

  templates = []
  for template, (group_males, group_females) in zip(
    animal.group_templates,
    allocations[component_index:],
  ):
    constraints = _group_constraint_values(template, group_males, group_females)
    if not constraints:
      constraints = {
        HASH_MIN_MALES: template.min_males.data,
        HASH_MAX_MALES: template.max_males.data,
        HASH_MIN_FEMALES: template.min_females.data,
        HASH_MAX_FEMALES: template.max_females.data,
      }
    templates.append({
      "males": group_males,
      "females": group_females,
      "min_males": constraints[HASH_MIN_MALES],
      "max_males": constraints[HASH_MAX_MALES],
      "min_females": constraints[HASH_MIN_FEMALES],
      "max_females": constraints[HASH_MAX_FEMALES],
      "max_size": template.max_group_size.data,
    })
  return {
    "solo_males": solo_males,
    "solo_females": solo_females,
    "group_templates": templates,
  }


def _update_population_details(window: sg.Window, values: dict, animal: AnimalPopulation) -> None:
  advanced = bool(values.get("animal_population_advanced"))
  default_options = {
    "solo_males": animal.solo_males.data if animal.solo_males else 0,
    "solo_females": animal.solo_females.data if animal.solo_females else 0,
    "group_templates": [_template_values(template) for template in animal.group_templates],
  }
  sections = [
    _population_summary(
      "Default",
      default_options["solo_males"],
      default_options["solo_females"],
      default_options["group_templates"],
      show_templates=advanced,
    )
  ]

  try:
    if advanced:
      modified, error = _advanced_options(animal, values)
      if error:
        raise ValueError(error)
    else:
      males = mods.coerce_int(values.get("animal_population_males"))
      females = mods.coerce_int(values.get("animal_population_females"))
      if males is None or females is None or males < 0 or females < 0 or males + females == 0:
        raise ValueError("enter valid non-negative male and female targets")
      modified = _automatic_options(animal, males, females)
    warning = _population_limit_warning(
      modified["solo_males"] + sum(template["males"] for template in modified["group_templates"]),
      modified["solo_females"] + sum(template["females"] for template in modified["group_templates"]),
    )
    if warning:
      sections.append(f"WARNING: {warning}")
    sections.append(
      _population_summary(
        "Modified",
        modified["solo_males"],
        modified["solo_females"],
        modified["group_templates"],
        show_templates=advanced,
      )
    )
  except ValueError as error:
    sections.append(f"Modified: {error}.")

  _update_details_text(window, "\n\n".join(sections))


def add_mod(window: sg.Window, values: dict) -> dict:
  reserve = _selected_reserve(values)
  if reserve is None:
    return {"invalid": "Please select a reserve first"}
  animal = _selected_animal(reserve, values)
  if animal is None:
    return {"invalid": "Please select a species first"}

  advanced = bool(values.get("animal_population_advanced"))
  advanced_options = None
  if advanced:
    advanced_options, error = _advanced_options(animal, values)
    if error:
      return {"invalid": error}
    males = advanced_options["solo_males"] + sum(
      template["males"] for template in advanced_options["group_templates"]
    )
    females = advanced_options["solo_females"] + sum(
      template["females"] for template in advanced_options["group_templates"]
    )
  else:
    males = mods.coerce_int(values.get("animal_population_males"))
    females = mods.coerce_int(values.get("animal_population_females"))
    if males is None or males < 0:
      return {"invalid": "Male target must be a non-negative whole number"}
    if females is None or females < 0:
      return {"invalid": "Female target must be a non-negative whole number"}
  if males + females == 0:
    return {"invalid": "At least one male or female animal is required"}
  if males > 0 and animal.male_population == 0:
    return {"invalid": "This species has no default male population; introducing that sex is unsupported"}
  if females > 0 and animal.female_population == 0:
    return {"invalid": "This species has no default female population; introducing that sex is unsupported"}
  return {
    "key": f"modify_animal_population_{reserve.reserve_id}_{animal.name}",
    "invalid": None,
    "warning": _population_limit_warning(males, females),
    "options": {
      "reserve_id": reserve.reserve_id,
      "species_id": animal.species_id,
      "species_name": animal.name,
      "species_display_name": animal.display_name,
      "male_population": males,
      "female_population": females,
      "advanced": advanced,
      "advanced_options": advanced_options,
    },
  }


def load_options(window: sg.Window, options: dict) -> None:
  try:
    reserve_id = int(options["reserve_id"])
  except (KeyError, TypeError, ValueError):
    raise ValueError("The saved mod has no valid reserve ID")
  reserve = _get_reserve(reserve_id)
  if reserve is None:
    raise ValueError(f"Reserve {options.get('reserve_id')} is no longer available")
  animal = next((
    animal for animal in reserve.animals
    if animal.species_id == options.get("species_id") or animal.name == options.get("species_name")
  ), None)
  if animal is None:
    raise ValueError(f"Species '{options.get('species_name')}' is no longer available on {reserve.display_name}")

  advanced = bool(options.get("advanced", False))
  window["animal_population_reserve"].update(reserve.display_name)
  window["animal_population_species"].update(
    values=[candidate.display_name for candidate in reserve.animals],
    value=animal.display_name,
    disabled=False,
  )
  window["animal_population_males"].update(str(options["male_population"]))
  window["animal_population_females"].update(str(options["female_population"]))
  window["animal_population_advanced"].update(advanced)
  _set_advanced_visibility(window, advanced)

  loaded = options.get("advanced_options") if advanced else None
  if loaded is None:
    loaded = {
      "solo_males": animal.solo_males.data if animal.solo_males else 0,
      "solo_females": animal.solo_females.data if animal.solo_females else 0,
      "group_templates": [_template_values(template) for template in animal.group_templates],
    }
  window["animal_population_solo_males"].update(
    str(loaded["solo_males"]),
    disabled=animal.solo_males is None,
  )
  window["animal_population_solo_females"].update(
    str(loaded["solo_females"]),
    disabled=animal.solo_females is None,
  )

  values = {
    "animal_population_reserve": reserve.display_name,
    "animal_population_species": animal.display_name,
    "animal_population_males": str(options["male_population"]),
    "animal_population_females": str(options["female_population"]),
    "animal_population_advanced": advanced,
    "animal_population_solo_males": str(loaded["solo_males"]),
    "animal_population_solo_females": str(loaded["solo_females"]),
  }
  for index in range(_max_group_templates()):
    visible = index < len(animal.group_templates)
    window[_template_key(index, "frame")].update(visible=visible)
    if not visible:
      continue
    template_values = loaded["group_templates"][index]
    for field, value in template_values.items():
      key = _template_key(index, field)
      window[key].update(str(value))
      values[key] = str(value)
  _update_population_details(window, values, animal)
  window.visibility_changed()
  window["options"].contents_changed()


def _allocate_counts(target: int, weights: list[int]) -> list[int]:
  if not weights:
    return []
  total_weight = sum(weights)
  if total_weight == 0:
    if target:
      raise ValueError("Cannot allocate a population across empty templates")
    return [0] * len(weights)

  raw_values = [target * weight / total_weight for weight in weights]
  allocated = [int(value) for value in raw_values]
  remainder = target - sum(allocated)
  fractions = sorted(
    range(len(weights)),
    key=lambda index: (raw_values[index] - allocated[index], weights[index]),
    reverse=True,
  )
  for index in fractions[:remainder]:
    allocated[index] += 1
  return allocated


def _population_components(
  animal: AnimalPopulation,
) -> list[tuple[RtpcProperty | None, RtpcProperty | None]]:
  components = []
  if animal.solo_males is not None or animal.solo_females is not None:
    components.append((animal.solo_males, animal.solo_females))
  components.extend(
    (template.male_population, template.female_population)
    for template in animal.group_templates
  )
  return components


def _allocate_from_capacities(target: int, capacities: list[int]) -> list[int]:
  if target == 0:
    return [0] * len(capacities)
  if target > sum(capacities):
    raise ValueError("Population target exceeds the available template capacity")
  return _allocate_counts(target, capacities)


def _allocate_structural_population(
  animal: AnimalPopulation,
  males: int,
  females: int,
) -> list[tuple[int, int]]:
  """
  Allocate genders without changing each template's share of all animals.
  Preserves the total size of the solo pool and every group-template pool, then changes gender within those pools.
  """
  components = _population_components(animal)
  original = [
    (
      male.data if male is not None else 0,
      female.data if female is not None else 0,
    )
    for male, female in components
  ]
  component_totals = _allocate_counts(
    males + females,
    [male + female for male, female in original],
  )

  # Begin at each component's original sex ratio. This makes unchanged targets
  # byte-for-byte stable and preserves sex-specific herd types where possible.
  base_males = []
  minimum_males = []
  maximum_males = []
  for (male, female), total, (male_prop, female_prop) in zip(
    original,
    component_totals,
    components,
  ):
    original_total = male + female
    base = round(total * male / original_total) if original_total else 0
    minimum = total if female_prop is None else 0
    maximum = 0 if male_prop is None else total
    base_males.append(min(max(base, minimum), maximum))
    minimum_males.append(minimum)
    maximum_males.append(maximum)

  current_males = sum(base_males)
  if current_males < males:
    additions = _allocate_from_capacities(
      males - current_males,
      [maximum - value for maximum, value in zip(maximum_males, base_males)],
    )
    base_males = [value + addition for value, addition in zip(base_males, additions)]
  elif current_males > males:
    removals = _allocate_from_capacities(
      current_males - males,
      [value - minimum for value, minimum in zip(base_males, minimum_males)],
    )
    base_males = [value - removal for value, removal in zip(base_males, removals)]

  return [
    (component_males, total - component_males)
    for component_males, total in zip(base_males, component_totals)
  ]


def _group_constraint_values(template: GroupTemplate, males: int, females: int) -> dict[int, int]:
  total = males + females
  if total == 0:
    return {}

  original_males = template.male_population.data
  original_females = template.female_population.data
  original_total = original_males + original_females
  if males * original_total == original_males * total:
    return {
      HASH_MIN_MALES: template.min_males.data,
      HASH_MAX_MALES: template.max_males.data,
      HASH_MIN_FEMALES: template.min_females.data,
      HASH_MAX_FEMALES: template.max_females.data,
    }

  minimum_size = template.min_males.data + template.min_females.data
  maximum_size = template.max_group_size.data
  minimum_males = round(minimum_size * males / total)
  maximum_males = round(maximum_size * males / total)
  return {
    HASH_MIN_MALES: minimum_males,
    HASH_MAX_MALES: maximum_males,
    HASH_MIN_FEMALES: minimum_size - minimum_males,
    HASH_MAX_FEMALES: maximum_size - maximum_males,
  }


def _population_updates(animal: AnimalPopulation, males: int, females: int) -> list[dict]:
  updates = []
  allocations = _allocate_structural_population(animal, males, females)
  components = _population_components(animal)
  for (male_prop, female_prop), (component_males, component_females) in zip(
    components,
    allocations,
  ):
    if male_prop is not None:
      updates.append({"offset": male_prop.data_pos, "value": component_males})
    if female_prop is not None:
      updates.append({"offset": female_prop.data_pos, "value": component_females})

  group_allocations = allocations[-len(animal.group_templates):]
  for template, (group_males, group_females) in zip(animal.group_templates, group_allocations):
    constraint_values = _group_constraint_values(template, group_males, group_females)
    for prop in (
      template.min_males,
      template.max_males,
      template.min_females,
      template.max_females,
    ):
      if prop is not None:
        updates.append({"offset": prop.data_pos, "value": constraint_values[prop.name_hash]})
  return updates


def _advanced_population_updates(animal: AnimalPopulation, advanced_options: dict) -> list[dict]:
  updates = []
  if animal.solo_males is not None:
    updates.append({"offset": animal.solo_males.data_pos, "value": advanced_options["solo_males"]})
  if animal.solo_females is not None:
    updates.append({"offset": animal.solo_females.data_pos, "value": advanced_options["solo_females"]})

  for template, values in zip(animal.group_templates, advanced_options["group_templates"]):
    properties = {
      "males": template.male_population,
      "females": template.female_population,
      "min_males": template.min_males,
      "max_males": template.max_males,
      "min_females": template.min_females,
      "max_females": template.max_females,
      "max_size": template.max_group_size,
    }
    for field, prop in properties.items():
      updates.append({"offset": prop.data_pos, "value": values[field]})
  return updates


def format_options(options: dict) -> str:
  mode = ", advanced templates" if options.get("advanced") else ""
  reserve_id = int(options["reserve_id"])
  reserve = _get_reserve(reserve_id)
  reserve_label = reserve.display_name if reserve else f"Reserve {reserve_id}"
  return (
    f"Modify Animal Population: {reserve_label} / {options['species_display_name']} "
    f"({options['male_population']} male, {options['female_population']} female{mode})"
  )


def handle_key(mod_key: str) -> bool:
  return mod_key.startswith("modify_animal_population_")


def get_files(options: dict) -> list[str]:
  return [RESERVE_FILE.format(reserve_id=options["reserve_id"])]


def process(options: dict) -> None:
  reserve_id = int(options["reserve_id"])
  species_id = int(options["species_id"])
  file = RESERVE_FILE.format(reserve_id=reserve_id)
  reserve = _load_reserve(mods.get_modded_file(file), SPECIES_NAMES)
  animal = _get_animal(reserve, species_id)
  if animal is None:
    raise ValueError(f"Species {species_id} is not present on reserve {reserve_id}")
  if options.get("advanced"):
    advanced_options = options["advanced_options"]
    males = advanced_options["solo_males"] + sum(
      template["males"] for template in advanced_options["group_templates"]
    )
    females = advanced_options["solo_females"] + sum(
      template["females"] for template in advanced_options["group_templates"]
    )
    updates = _advanced_population_updates(animal, advanced_options)
  else:
    males = int(options["male_population"])
    females = int(options["female_population"])
    updates = _population_updates(
      animal,
      males,
      females,
    )
  mods.apply_updates_to_file(file, updates)


SPECIES_NAMES = _load_species_names()
ALL_RESERVES = load_reserves(SPECIES_NAMES)
