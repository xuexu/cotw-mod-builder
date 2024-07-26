from deca.ff_adf import Adf
from deca.file import ArchiveFile
from modbuilder.xlsx_cell import XlsxCell
from modbuilder import mods

def deserialize_adf(filename: str) -> dict:
  modded_file = mods.get_modded_file(filename)
  adf = Adf()
  with ArchiveFile(open(modded_file, 'rb')) as f:
    adf.deserialize(f)
  return adf.table_instance_full_values[0].value


def parse_cells_from_adf(extracted_adf: dict) -> list[XlsxCell]:
  cells = []
  for sheet in extracted_adf["Sheet"].value:
    for i in range(len(sheet.value["CellIndex"].value)):
        cells.append(XlsxCell(extracted_adf, sheet.value, index=i))
  return cells


def get_cell_by_coordinates(coordinates: str, sheet_name: str, cells: list[XlsxCell]) -> XlsxCell:
  matching_cell = None
  for cell in cells:
    if cell.sheet_name == sheet_name and cell.coordinates == coordinates:
      matching_cell = cell
      break
  return matching_cell


def format_desired_data(cell: XlsxCell, value: any, transform: str = None) -> dict:
  desired = {}  
  if transform == "multiply":
    desired["value"] = cell.data_value * value
  elif transform == "add":
    desired["value"] = cell.data_value + value
  else:
    desired["value"] = value
  if isinstance(desired["value"], bool):
    desired["data_type"] = 0
  if isinstance(desired["value"], str):
    desired["data_type"] = 1
  if isinstance(desired["value"], float) or isinstance(desired["value"], int):
    desired["value"] = float(desired["value"])
    desired["data_type"] = 2
  return desired


def update_file_at_coordinates(src_filename: str, sheet_name: str, coordinates: str, value: any, transform: str = None) -> None:
  extracted_adf = deserialize_adf(src_filename)
  cells = parse_cells_from_adf(extracted_adf)
  cell = get_cell_by_coordinates(coordinates, sheet_name, cells)
  if cell is None:
    raise ValueError(f'Unable to find cell "{coordinates}" on sheet "{sheet_name}" in file "{src_filename}"')
  other_cells = [c for c in cells if c != cell]
  desired_data = format_desired_data(cell, value, transform if transform else None)    
  offsets_and_values = find_best_offsets_and_values_for_cell_update(cell, other_cells, desired_data, extracted_adf)
  mods.update_file_at_offsets_with_values(src_filename, offsets_and_values)


def update_file_at_multiple_coordinates_with_value(src_filename: str, sheet_name: str, coordinates_list: list[str], value: any, transform: str = None) -> None:
  for coordinates in coordinates_list:
    update_file_at_coordinates(src_filename, sheet_name, coordinates, value, transform)


def get_sheet(sheet_name: str, extracted: dict) -> dict:
  for sheet in extracted["Sheet"].value:
    if sheet.value["Name"].value.decode("utf-8") == sheet_name:
      matching_sheet = sheet
      break
  if matching_sheet:
    return matching_sheet.value
  else:
    raise ValueError("Unable to find sheet by name", sheet_name)

def get_data_array_for_data_type(extracted_adf: dict, data_type: int) -> tuple[list, int]:
  if data_type == 0:
    return extracted_adf["BoolData"].value, extracted_adf["BoolData"].data_offset
  if data_type == 1:
    return extracted_adf["StringData"].value, extracted_adf["StringData"].data_offset 
  if data_type == 2:
    return extracted_adf["ValueData"].value, extracted_adf["ValueData"].data_offset


def find_best_offsets_and_values_for_cell_update(
    cell: XlsxCell,
    other_cells: list[XlsxCell],
    desired: dict,
    extracted_adf: dict
  ) -> list[tuple]:
  unused_cell_definitions = get_unused_cell_definitions(extracted_adf, [cell] + other_cells)
  unused_value_data_items = get_unused_value_data_indicies_and_offsets(extracted_adf, [cell] + other_cells)
  data_array, data_array_offset = get_data_array_for_data_type(extracted_adf, desired["data_type"])
  # print()
  # print(f'Cell = Coordinates: {cell.coordinates}   Sheet: {cell.sheet_name}   Definition: {cell.definition_index}   Value: {cell.data_value}   Data Type: {cell.data_type}   Value Index: {cell.data_index})')
  # print(f'Desired = Value: {desired["value"]}   Data Type: {desired["data_type"]}')

  # 0. If current cell already has desired value and is the correct type, don't change anything
  if cell.data_value == desired["value"] and cell.data_type == desired["data_type"]:
    # print('0. Current value and data type match. No changes to apply')
    return []

  # 1. StringData values can be directly overwritten in the StringData array
  #    This does not handle writing StringData to a non-StringData cell. That should error out for now.
  if cell.data_type == desired["data_type"] == 1:
    # print(f'1. Overwriting StringData index {cell.data_index} with value {desired["value"]}')
    update = (cell.data_offset, desired["value"])
    return [update]
  elif cell.data_type == 1 or desired["data_type"] == 1:
    raise NotImplementedError(f'Unable to update cell {cell.coordinates} with type {cell.data_type} to the desired value {desired["value"]} with type {desired["data_type"]}.')
  
  # BoolData and ValueData cells need to be handled with more care
  # Try to find a safe way to overwrite data or repoint cell definitions to preferred values
  cell_with_desired_value = find_cell(other_cells, desired["data_type"], value=desired["value"])
  cell_with_same_definition = find_cell(other_cells, cell.data_type,  definition_index=cell.definition_index)
  cell_with_same_data_index = find_cell(other_cells, cell.data_type, data_index=cell.data_index)
  
  # 2. Check if the desired value already exists in the data array
  if desired["value"] in data_array:
    # print(f'2. Desired value {desired["value"]} is in data array')
    desired["data_index"] = data_array.index(desired["value"])
    # 2a. Point current cell at a different definition that references the desired value
    if cell_with_desired_value:
      # print(f'2a. Cell {cell_with_desired_value.coordinates} contains desired value. Copying defintion {cell_with_desired_value.definition_index}')
      update = (cell.offset, cell_with_desired_value.definition_index)
      return [update]
    # 2b. Point current cell definition at desired value if we do not share a definition with other cells
    if cell_with_same_definition is None:
      # print(f'2b. No other cells share the same definition. Repointing definition at data index {desired["data_index"]}')
      update = (cell.definition_data_offset, desired["data_index"])
      return [update]
    # 2c. Overwrite an unused cell definition (if one exists) to point it at the desired value in the data array
    #     Then point our cell at the customized cell definition
    if unused_cell_definitions:
      unused_cell_definition = unused_cell_definitions.pop(0)
      # print(f'2c. Overwriting unused cell definition {unused_cell_definition["definition_index"]} to point at data index {desired["data_index"]}')
      # Point unused cell definition at the desired value
      update = (unused_cell_definition["definition_data_offset"], desired["data_index"])
      # Point our cell at the updated definition
      update2 = (cell.offset, cell.unused_cell_definition["definition_index"])
      return [update, update2]

  # 3. Desired value does not exist in the data array
  else:
    # print(f'3. Desired value {desired["value"]} is not in the data array')
    # 3a. Overwrite our current value in the ValueData array if no other cells point at the same value
    if cell_with_same_data_index is None:
      # print(f'3a. Overwriting data array value at index {cell.data_index} to new value {desired["value"]}')
      update = (cell.data_offset, desired["value"])
      return [update]
    # 3b. Overwrite an unused data array item (if one exists) with the desired value
    #     Overwrite an unused cell definition (if one exists) to point at the new ValueData item
    #     Then repoint our cell at the customized cell defintion
    if unused_value_data_items and unused_cell_definitions:
      unused_value_data_item = unused_value_data_items.pop(0)
      unused_cell_definition = unused_cell_definitions.pop(0)
      # print(f'3b. Overwriting unused data array value at index {unused_value_data_item["data_index"]} to new value {desired["value"]}')
      # print(f'2c. Overwriting unused cell definition {unused_cell_definition["definition_index"]} to point at data index {unused_value_data_item["data_index"]}...')
      # Overwrite the unused data array item
      update = (unused_value_data_item["data_offset"], desired["value"])
      # Point unused cell definition at the updated value
      update2 = (unused_cell_definition["definition_data_offset"], unused_value_data_item["data_index"])
      # Point our cell at the updated definition
      update3 = (cell.offset, unused_cell_definition["definition_index"])
      return [update, update2, update3]

  # 4. Cannot update the value of the specified cell to match the exact desired value without affecting other cells
  # print(f'Cannot update cell {cell.coordinates} to value {desired["value"]} without affecting other cells')
  # 4a. Point our cell an existing cell definition that has the closest value to the desired value
  closest_cell = find_closest_cell_by_value(cell, other_cells, data_array, desired)
  if closest_cell:
    # print(f'4. Pointing cell {cell.coordinates} at definition {closest_cell.definition_index} with closest value {closest_cell.data_value}')
    update = (cell.offset, closest_cell.definition_index)
    return [update]
  # 3b. Find the closest value in the ValueData array and point our cell definition at it
  #     This may have unintended consequences. Consider throwing an error and see how many mods break from the error
  closest_value_index = find_closest_value_index(data_array, desired["value"])
  if closest_value_index:
    # print(f'5. Pointing cell {cell.coordinates} definition {cell.definition_index} at data index {closest_value_index} with closest value {data_array[closest_value_index]}')
    update = (cell.definition_data_offset, closest_value_index)
    return [update]

  # If you got all the way down here then you're out of luck for now.
  raise NotImplementedError(f'Unable to update cell {cell.coordinates} with the desired value {desired["value"]}. Exiting...')


def find_cell(cells: list[XlsxCell], data_type: int, value: any = None, definition_index: int = None, data_index: int = None) -> XlsxCell:
  exact_match = None
  for cell in cells:
    if cell.data_type == data_type:
      if value is not None:
        if cell.data_value == value:
          exact_match = cell
          break
      if definition_index is not None:
        if cell.definition_index == definition_index:
          exact_match = cell
          break
      if data_index is not None:
        if cell.data_index == data_index:
          exact_match = cell
          break
  return exact_match


def get_unused_cell_definitions(extracted_adf: dict, cells: list[XlsxCell]) -> list[dict]:
  unused_cell_definitions = []
  assigned_cell_definitions = [cell.definition_index for cell in cells]
  unused_cell_definitions = [
    {
      "definition_index": i,
      "definition_offset": c.data_offset,
      "definition_data_offset": c.value["DataIndex"].data_offset
    }
    for i, c in enumerate(extracted_adf["Cell"].value)
    if i not in assigned_cell_definitions
  ]
  return unused_cell_definitions


def get_unused_value_data_indicies_and_offsets(extracted_adf: dict, cells: list[XlsxCell]) -> list[dict]:
  assigned_value_data_indicies = [cell.data_index for cell in cells if cell.data_type == 2]
  value_data_offset = extracted_adf["ValueData"].data_offset
  unused_value_data_indicies_and_offsets = [
    {"data_index": i, "data_offset": value_data_offset + ( i * 4)}
    for i, _v in enumerate(extracted_adf["ValueData"].value)
    if i not in assigned_value_data_indicies
  ]
  return unused_value_data_indicies_and_offsets


def find_closest_cell_by_value(cell: XlsxCell, cell_list: list[XlsxCell], data_array: list[any], desired: dict) -> XlsxCell:
  exact_match = None
  if len(data_array) == 0:
    return exact_match
  closest_value_index = find_closest_value_index(data_array, desired["value"])
  for cell in cell_list:
    if cell.data_type == desired["data_type"] and cell.data_index == closest_value_index:
      exact_match = cell
      break
  if exact_match:
    return exact_match
  else:
    new_data_array = [v for i, v in enumerate(data_array) if i != closest_value_index]
    return find_closest_cell_by_value(cell, cell_list, new_data_array, desired)


def find_closest_value_index(value_data: list[float], desired_value: float) -> int:
  exact_match = None
  closest_delta = 9999999
  closest_match = None
  for i, number in enumerate(value_data):
    if float(number) == desired_value:
      exact_match = i
      break
    delta = abs(float(number) - desired_value)
    if delta < closest_delta:
      closest_match = i
      closest_delta = delta
  if exact_match is not None:
    return exact_match
  return closest_match
