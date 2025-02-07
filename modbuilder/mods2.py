import math
from deca.ff_adf import Adf, AdfValue
from deca.file import ArchiveFile
from modbuilder import mods
from openpyxl.utils import column_index_from_string, get_column_letter
from openpyxl.utils.cell import coordinate_from_string

def deserialize_adf(filename: str) -> dict:
  modded_file = mods.get_modded_file(filename)
  adf = Adf()
  with ArchiveFile(open(modded_file, 'rb')) as f:
    adf.deserialize(f)
  return adf.table_instance_full_values[0].value


class XlsxCell:
  __slots__ = (
    'coordinates',              # coordinates of cell in sheet
    'sheet_name',               # sheet that cell is located on
    'sheet_index',              # index of the sheet in the extracted ADF file
    'src_filename',             # file containing the sheet data
    'index',                    # index of the cell from all cells in the sheet
    'definition_index',         # index in the list of cell definitions
    'definition_index_offset',  # offset where "defintiion_index" is stored
    'value_index',              # index of the value in the data array
    'value_index_offset',       # offset where "value_index" is stored
    'value',                    # value of the cell in the parsed ADF
    'value_offset',             # offset where the value is stored in the data array
    'data_type',                # type of data (0=bool, 1=str, 2=float)
    'data_array_name',          # name of the array the value is stored in
    'attribute_index',          # attribute_index from cell definition
    'desired_value',            # ideal value after transform is applied
    'desired_data_type',        # data type of the ideal value
    'desired_data_array_name',  # name of the array the desired value is stored in
  )

  coordinates: str
  sheet_name: str
  sheet_index: int
  src_filename: str
  index: int
  definition_index: int
  definition_index_offset: int
  value_index: int
  value_index_offset: int
  value: any
  value_offset: int
  data_type: int
  data_array_name: str
  attribute_index: int
  desired_value: any
  desired_data_type: int
  desired_data_array_name: str

  def __init__(self, src_filename: str, extracted_adf: AdfValue, update_data: dict) -> 'XlsxCell':
    self.src_filename = src_filename
    self.coordinates = update_data["coordinates"]
    self.sheet_name = update_data["sheet"]
    sheet, self.sheet_index = get_sheet(extracted_adf, self.sheet_name)
    if sheet is None:
      raise ValueError(f'Unable to find sheet "{self.sheet_name}" in file "{src_filename}"')
    # get value of current cell
    self._get_value_and_offsets(extracted_adf, sheet, src_filename)
    # calculate desired value
    self._format_desired_data(update_data)

  def _get_value_and_offsets(self, extracted_adf: AdfValue, sheet: AdfValue, src_filename: str) -> None:
    col_str, row = coordinate_from_string(self.coordinates)
    col = column_index_from_string(col_str)
    self.index = ( ( row - 1 ) * sheet["Cols"].value ) + col - 1  # -1 because spreadsheets start at A1 but lists start at 0

    self.definition_index = int(sheet["CellIndex"].value[self.index])
    self.definition_index_offset = int(sheet["CellIndex"].data_offset + ( self.index * 4 ))

    cell_definition = extracted_adf["Cell"].value[self.definition_index].value
    self.value_index = int(cell_definition["DataIndex"].value)
    self.value_index_offset = int(cell_definition["DataIndex"].data_offset)
    self.data_type = int(cell_definition["Type"].value)
    self.attribute_index = int(cell_definition["AttributeIndex"].value)

    self.value = None
    if self.data_type == 0:
      self.data_array_name = "BoolData"
      self.value = extracted_adf[self.data_array_name].value[self.value_index]
      self.value_offset = extracted_adf[self.data_array_name].data_offset + ( self.value_index * 4 )
    if self.data_type == 1:
      self.data_array_name = "StringData"
      self.value = extracted_adf[self.data_array_name].value[self.value_index].value
      self.value_offset = extracted_adf[self.data_array_name].value[self.value_index].data_offset
    if self.data_type == 2:
      self.data_array_name = "ValueData"
      self.value = extracted_adf[self.data_array_name].value[self.value_index]
      self.value_offset = extracted_adf[self.data_array_name].data_offset + ( self.value_index * 4 )
    if self.value is None:
      raise ValueError(f'Unable to find cell "{self.coordinates}" on sheet "{self.sheet_name}" in file "{src_filename}"')

  def _format_desired_data(self, update_data: dict) -> dict:
    transform = update_data.get("transform")
    if transform == "multiply":
      self.desired_value = self.value * update_data["value"]
    elif transform == "add":
      self.desired_value = self.value + update_data["value"]
    else:
      self.desired_value = update_data["value"]

    if isinstance(self.desired_value, bool):
      self.desired_data_type = 0
      self.desired_data_array_name = "BoolData"
    if isinstance(self.desired_value, str):
      self.desired_value = self.desired_value.encode("utf-8")  # for comparison against encoded values in StringData
      self.desired_data_type = 1
      self.desired_data_array_name = "StringData"
    if isinstance(self.desired_value, float) or isinstance(self.desired_value, int):
      self.desired_value = float(self.desired_value)
      self.desired_data_type = 2
      self.desired_data_array_name = "ValueData"


def get_sheet(extracted_adf: AdfValue, sheet_name: str) -> tuple[AdfValue, int]:
  for i, sheet in enumerate(extracted_adf["Sheet"].value):
    if sheet.value["Name"].value.decode("utf-8") == sheet_name:
      return sheet.value, i
  return None, None

def process_cell_update(cell: XlsxCell, extracted_adf: AdfValue, skip_overwrite: bool = False, force: bool = False, verbose: bool = False) -> list[tuple[int, any]]:
  if verbose:
    print()
    print(f'Cell = Coordinates: {cell.coordinates}   Sheet: {cell.sheet_name}   Value: {cell.value}   Data Type: {cell.data_type}')
    print(f'Definition = Index: {cell.definition_index}   AttributeIndex: {cell.attribute_index}')
    print(f'Desired = Value: {cell.desired_value}   Data Type: {cell.desired_data_type}')

  # 0. If current cell already has desired value and is the correct type, don't change anything
  if cell.value == cell.desired_value and cell.data_type == cell.desired_data_type:
    if verbose:
      print('0. Current value and data type match. No changes to apply')
    return []

  # Try to find a safe way to overwrite data or repoint cell definitions to preferred values
  # 1. Check if the desired value is already in the data array. If it is then work with it
  if is_desired_value_in_data_array(extracted_adf, cell, verbose=verbose):
    updates = use_value_from_data_array(extracted_adf, cell, verbose=verbose)
    if updates is not None:
      return updates

  # 2. Desired value does not exist in the data array. See if we can write it in without conflicts
  if not skip_overwrite:
    updates = write_value_to_data_array(extracted_adf, cell, verbose=verbose)
    if updates is not None:
      return updates

  # 3. Cannot update the value of the specified cell to match the exact desired value without affecting other cells
  if verbose:
    print(f'3. Cannot update cell {cell.coordinates} to exact value {cell.desired_value} without affecting other cells')
  # If we were told to force the exact value then overwrite the value in the array
  # This only works if we're dealwing with the same data type
  if force and cell.data_type == cell.desired_data_type:
    updates = force_overwrite_value(extracted_adf, cell)
    return updates
  # Locate the closest value in the data array and see if we can work with that. This only works for ValueData cells
  if cell.data_type == 2:
    updates = use_closest_value_in_array(extracted_adf, cell, verbose=verbose)
    if updates is not None:
      return updates

  # If you got all the way down here then you're out of luck for now.
  raise NotImplementedError(f'Unable to update cell {cell.coordinates} with the desired value {cell.desired_value}. Exiting...')


def is_desired_value_in_data_array(extracted_adf: AdfValue, cell: XlsxCell, verbose: bool = False) -> bool:
  if cell.data_array_name in ["BoolData", "ValueData"]: # values stored directly in array
    return cell.desired_value in extracted_adf[cell.desired_data_array_name].value
  if cell.data_array_name == "StringData": # StringData is an array of AdfValues
    array_values = [s.value for s in extracted_adf["StringData"].value]
    return cell.desired_value in array_values


def use_value_from_data_array(extracted_adf: AdfValue, cell: XlsxCell, verbose: bool = False) -> list[tuple[int, any]]:
  if verbose:
    print(f'1. Desired value {cell.desired_value} is in data array {cell.desired_data_array_name}')
  # Value may exist more than once in array
  if cell.desired_data_array_name == "StringData":
    desired_value_indexes = [i for i, data in enumerate(extracted_adf[cell.desired_data_array_name].value) if data.value == cell.desired_value]
  else:
    desired_value_indexes = [i for i, value in enumerate(extracted_adf[cell.desired_data_array_name].value) if value == cell.desired_value]

  # 1a. Point current cell at a different definition that references the desired value
  cell_defs_with_matching_value = find_cell_definitions(extracted_adf["Cell"].value, cell.desired_data_type, desired_value_indexes, verbose=verbose)
  matching_definition = None
  if cell_defs_with_matching_value:
    cell_defs_with_matching_atttribute = [def_tuple for def_tuple in cell_defs_with_matching_value if def_tuple[1].value["AttributeIndex"] == cell.attribute_index]
    if cell_defs_with_matching_atttribute:
      matching_definition = cell_defs_with_matching_atttribute.pop()
    else:
      matching_definition = cell_defs_with_matching_value.pop()
    if matching_definition:
      update = (cell.definition_index_offset, matching_definition[0])
      extracted_adf["Sheet"].value[cell.sheet_index].value["CellIndex"].value[cell.index] = matching_definition[0]
      if verbose:
        print(f'1a. Cell definition {matching_definition[0]} points at the desired value. Updating cell to use that definition.')
        print(update)
      return [update]

  # 1b. Check if any other cells use the same definition as our cell
  #     If not, point current cell definition at desired value
  cells_with_same_definition = find_cells(extracted_adf, definition_indexes=[cell.definition_index], ignore_cell=cell)
  if verbose:
      print(f'1b. {len(cells_with_same_definition)} cells point at the same definition.')
  if not cells_with_same_definition:
    update = (cell.value_index_offset, desired_value_indexes[0])
    extracted_adf["Cell"].value[cell.definition_index].value["DataIndex"].value = desired_value_indexes[0]
    if verbose:
      print(f'1b. No other cells share the same definition. Repointing defintiion at desired value {cell.desired_value} at index {desired_value_indexes[0]}.')
      print(update)
    return [update]

  # 1c. Overwrite an unused cell definition (if one exists) to point it at the desired value in the data array
  #     Then point our cell at the customized cell definition
  unused_definition_indexes = get_unused_cell_def_indexes(extracted_adf)
  if unused_definition_indexes:
    unused_definition_index = unused_definition_indexes.pop()
    unused_definition = extracted_adf["Cell"].value[unused_definition_index].value
    # Point unused cell definition at the desired value index
    update = (unused_definition["DataIndex"].data_offset, desired_value_indexes[0])
    extracted_adf["Cell"].value[unused_definition_index].value["DataIndex"].value = desired_value_indexes[0]
    # Point our cell at the updated definition
    update2 = (cell.definition_index_offset, unused_definition_index)
    extracted_adf["Sheet"].value[cell.sheet_index].value["CellIndex"].value[cell.index] = unused_definition_index
    if verbose:
      print(f'1c. Overwriting unused cell definition {unused_definition_index} to point at desired value {cell.desired_value} at index {desired_value_indexes[0]}')
      print(update)
      print(update2)
    return [update, update2]
  # 1z. Unable to use the existing value in the array. Find another way to do it
  return None


def write_value_to_data_array(extracted_adf: AdfValue, cell: XlsxCell, verbose: bool = False) -> list[tuple[int, any]]:
  if verbose:
    print(f'2. Desired value {cell.desired_value} is not in the data array {cell.desired_data_array_name}')

  # 2a. If data type is not changing, try to overwrite our current value
  #     Check if any other cells in the entire sheet point at the same value as our cell
  #     (there might be a cell index that points at our cell but it could be unused)
  #     If none are found then overwrite our current value in the data array
  if cell.data_type == cell.desired_data_type:
    cells_with_shared_value = find_cells(extracted_adf, data_type=cell.data_type, value_index=cell.value_index, ignore_cell=cell)
    if verbose:
      print(f"2a. {len(cells_with_shared_value)} cells point at the same value.")
      # for (si,ci,di) in cells_with_shared_value:
      #   print(f"Sheet: {extracted_adf["Sheet"].value[si].value["Name"].value}   Coords: {calculate_coordinates(ci, extracted_adf["Sheet"].value[si].value["Cols"].value)}")

    if not cells_with_shared_value:
      update = (cell.value_offset, cell.desired_value)
      if cell.desired_data_type == 1:
        extracted_adf[cell.desired_data_array_name].value[cell.value_index].value = cell.desired_value
      else:
        extracted_adf[cell.desired_data_array_name].value[cell.value_index] = cell.desired_value
      if verbose:
        print(f'2a. Overwriting {cell.desired_data_array_name} value at index {cell.value_index} to new value {cell.desired_value}')
        print(update)
      return [update]

  # 2b/c. Try to find an unused item in the data array to overwrite
  unused_value_indexes_and_offsets = get_unused_value_indexes_and_offsets(extracted_adf, cell.desired_data_array_name, cell.desired_data_type)
  # 2b. If one exists, check if any other cells share our definition
  #     If not, overwrite the value and point our definition at the new value
  if unused_value_indexes_and_offsets:
    if not find_cells(extracted_adf, definition_indexes=[cell.definition_index], ignore_cell=cell):
      # Overwrite the unused data array item
      unused_value = unused_value_indexes_and_offsets.pop()
      if verbose:
        print(f'2b. Overwriting unused {cell.desired_data_array_name} value at index {unused_value["index"]} to new value {cell.desired_value}')
      update1 = (unused_value["offset"], cell.desired_value)
      if cell.desired_data_type == 1:
        extracted_adf[cell.desired_data_array_name].value[unused_value["index"]].value = cell.desired_value
      else:
        extracted_adf[cell.desired_data_array_name].value[unused_value["index"]] = cell.desired_value
      # Point our cell definition at the desired value
      update2 = (cell.value_index_offset, unused_value["index"])
      extracted_adf["Cell"].value[cell.definition_index].value["DataIndex"].value = unused_value["index"]
      if verbose:
        print(f'2b. Pointing cell {cell.coordinates} definition {cell.definition_index} at value index {unused_value["index"]} with value {cell.desired_value}')
        print(update1)
        print(update2)
      return [update1, update2]

  # 2c. There's still an unused data array item we can overwrite
  #     Check if there is an unused cell definition that we can repurpose
  #     If so. overwrite the unused data item, repoint the unused definition, and repoint our cell at that definition
  unused_definition_indexes = get_unused_cell_def_indexes(extracted_adf)
  if unused_value_indexes_and_offsets and unused_definition_indexes:
    unused_value = unused_value_indexes_and_offsets.pop()
    unused_definition_index = unused_definition_indexes.pop()
    unused_definition = extracted_adf["Cell"].value[unused_definition_index].value

    # Overwrite the unused data array item
    if verbose:
      print(f'2c. Overwriting unused {cell.desired_data_array_name} value at index {unused_value["index"]} to new value {cell.desired_value}')
    update1 = (unused_value["offset"], cell.desired_value)
    if cell.desired_data_type == 1:
      extracted_adf[cell.desired_data_array_name].value[unused_value["index"]].value = cell.desired_value
    else:
      extracted_adf[cell.desired_data_array_name].value[unused_value["index"]] = cell.desired_value

    # Point the unused cell definition at the new data array item
    if verbose:
       print(f'2c. Overwriting unused cell definition {unused_definition_index} to point at value index {unused_value["index"]}')
    update2 = (unused_definition["DataIndex"].data_offset, unused_value["index"])
    extracted_adf["Cell"].value[unused_definition_index].value["DataIndex"].value = unused_value["index"]
    # Write our cell definition type and attribute to the unused cell definition
    update3 = (unused_definition["Type"].data_offset, cell.data_type)
    update4 = (unused_definition["AttributeIndex"].data_offset, cell.attribute_index)
    extracted_adf["Cell"].value[unused_definition_index].value["Type"].value = cell.data_type
    extracted_adf["Cell"].value[unused_definition_index].value["AttributeIndex"].value = cell.attribute_index
    # Point our cell at the definition
    if verbose:
        print(f'2c. Pointing cell {cell.coordinates} at definition {unused_definition_index} with value {cell.desired_value}')
    update5 = (cell.definition_index_offset, unused_definition_index)
    extracted_adf["Sheet"].value[cell.sheet_index].value["CellIndex"].value[cell.index] = unused_definition_index
    if verbose:
      print(update1)
      print(update2)
      print(update3)
      print(update4)
      print(update5)
    return [update1, update2, update3, update4, update5]

  # 2z. Unable to update a value in the array. Find another way to do it
  return None


def update_string_data(extracted_adf: AdfValue, cell: XlsxCell, verbose: bool = False) -> list[tuple[int, str]]:
  # TODO: This requires matching the data length otherwise all "downstream" offsets need to be updated
  #       Will need to abandon updating at offsets and instead rebuild from extracted ADF
  # StringData can currently only be overwritten by StringData
  if cell.data_type == cell.desired_data_type == 1:
    update = (cell.value_offset, cell.desired_value)
    extracted_adf["StringData"].value[cell.value_index].value = cell.desired_value
    if verbose:
      print(f'2a. Overwriting StringData index {cell.value_index} with value {cell.desired_value}')
      print(update)
    return [update]
  raise NotImplementedError(f'Unable to update cell {cell.coordinates} with type {cell.data_type} to the desired value {cell.desired_value} with type {cell.desired_data_type}.')


def force_overwrite_value(extracted_adf: AdfValue, cell: XlsxCell, verbose: bool = False) -> list[tuple[int,str]]:
  # If force=True then overwrite the value in the data array
  update = (cell.value_offset, cell.desired_value)
  if cell.desired_data_type == 1:
    extracted_adf[cell.data_array_name].value[cell.value_index].value = cell.desired_value
  else:
    extracted_adf[cell.data_array_name].value[cell.value_index] = cell.desired_value
  if verbose:
    print(f'   FORCE: Overwriting {cell.data_array_name} value at index {cell.value_index} with {cell.desired_value}')
    print(update)
  return [update]


def use_closest_value_in_array(extracted_adf: AdfValue, cell: XlsxCell, verbose: bool = False) -> list[tuple[int, int]]:
  # Find the closest value in the array
  closest_value_index, closest_value = find_closest_value(extracted_adf["ValueData"].value, cell.desired_value)
  # 3a. Check if any other cells are using the same definition as our cell.
  #     If not, point our cell definition at the closest value in the array
  cells_with_same_definition = find_cells(extracted_adf, definition_indexes=[cell.definition_index], ignore_cell=cell)
  if verbose:
      print(f'3a. {len(cells_with_same_definition)} cells point at the same definition as our cell.')
  if not cells_with_same_definition:
    update = (cell.value_index_offset, closest_value_index)
    extracted_adf["Cell"].value[cell.definition_index].value["DataIndex"].value = closest_value_index
    if verbose:
      print(f'3a. Pointing cell {cell.coordinates} definition {cell.definition_index} with closest value {closest_value}')
      print(update)
    return [update]
  # 3b. Check if any other definitions are pointing at the closest value
  #    If one is found then point our cell at that definition
  defs_with_closest_value = find_cell_definitions(extracted_adf["Cell"].value, cell.data_type, [closest_value_index], verbose=verbose)
  if verbose:
    print(f'3a. {len(defs_with_closest_value)} cell definitions point at a definition with the closest value {closest_value}: {[d[0] for d in defs_with_closest_value]}')
  if defs_with_closest_value:
    defs_with_same_attributes = [(i,d) for (i,d) in defs_with_closest_value if d.value["AttributeIndex"].value == cell.attribute_index]
    if defs_with_same_attributes:
      if verbose:
        print(f'3a. {len(defs_with_same_attributes)} cell definitions have the same attribute ({cell.attribute_index}): {[d[0] for d in defs_with_same_attributes]}.')
      chosen_definition = defs_with_same_attributes.pop()
    else:
      chosen_definition = defs_with_closest_value.pop()
    update = (cell.definition_index_offset, chosen_definition[0])
    extracted_adf["Sheet"].value[cell.sheet_index].value["CellIndex"].value[cell.index] = chosen_definition[0]
    if verbose:
      print(f'3b. Pointing cell {cell.coordinates} at definition {chosen_definition[0]} with closest value {closest_value}')
      print(update)
    return [update]
  # 3c. Point our cell definition at the closest value
  #     This will have unintended consequences since other cells use this cell definition
  #     TODO: A proper method to add new data to arrays and rebuild from ADF will solve this
  update = (cell.value_index_offset, closest_value_index)
  extracted_adf["Cell"].value[cell.definition_index].value["DataIndex"].value = closest_value_index
  if verbose:
    print(f'3c. Pointing cell {cell.coordinates} definition {cell.definition_index} at value index {closest_value_index} with closest value {closest_value}')
    print(update)
  return [update]


def range_to_coordinates_list(column: str, start_row: int, end_row: int) -> list[str]:
  coordinates_list = [f"{column}{row}" for row in range(start_row, end_row + 1)]
  return coordinates_list


def apply_coordinate_updates_to_file(src_filename: str, coordinate_updates: list[dict], skip_overwrite: bool = False, force: bool = False, verbose: bool = False) -> None:
  extracted_adf = deserialize_adf(src_filename)
  offsets_and_values = []
  for update_data in coordinate_updates:
    cell = XlsxCell(src_filename, extracted_adf, update_data)
    offset_updates = process_cell_update(cell, extracted_adf, skip_overwrite=skip_overwrite, force=force, verbose=verbose)
    offsets_and_values.extend(offset_updates)
  mods.update_file_at_offsets_with_values(src_filename, offsets_and_values)


def update_file_at_coordinates(src_filename: str, update_data: dict, skip_overwrite: bool = False, force: bool = False, verbose: bool = None) -> None:
  extracted_adf = deserialize_adf(src_filename)
  cell = XlsxCell(src_filename, extracted_adf, update_data)
  offsets_and_values = process_cell_update(cell, extracted_adf, skip_overwrite-skip_overwrite, force=force, verbose=verbose)
  mods.update_file_at_offsets_with_values(src_filename, offsets_and_values)


def update_file_at_multiple_coordinates_with_value(src_filename: str, sheet_name: str, coordinates_list: list[str], value: any, transform: str = None, skip_overwrite: bool = False, force: bool = False, verbose: bool = False) -> None:
  coordinate_updates = []
  for coordinates in coordinates_list:
    coordinate_updates.append({
      "sheet": sheet_name,
      "coordinates": coordinates,
      "value": value,
      "transform": transform,
    })
  apply_coordinate_updates_to_file(src_filename, coordinate_updates, skip_overwrite=skip_overwrite, force=force, verbose=verbose)


def update_coordinates_in_row(src_filename: str, sheet_name: str, row: int, start: str = "A", end: str = None, value: any = None, transform: str = None, skip_overwrite: bool = False, force: bool = False, verbose: bool = False) -> None:
  extracted_adf = deserialize_adf(src_filename)
  sheet, _i = get_sheet(extracted_adf, sheet_name)
  if sheet is None:
    raise ValueError(f'Unable to find sheet "{sheet_name}" in file "{src_filename}"')
  if not end:  # default to last column in sheet
    end = get_column_letter(sheet["Cols"].value)
  coordinates_range = [f"{column}{row}" for column in get_column_range(start, end)]
  updates = [{
    "sheet": sheet_name,
    "coordinates": coordinates,
    "value": value,
    "transform": transform,
  } for coordinates in coordinates_range]
  apply_coordinate_updates_to_file(src_filename, updates, skip_overwrite=skip_overwrite, force=force, verbose=verbose)


def get_data_array_for_data_type(extracted_adf: AdfValue, data_type: int) -> tuple[list, int]:
  if data_type == 0:
    array_name = "BoolData"
  if data_type == 1:
    array_name = "StringData"
  if data_type == 2:
    array_name = "ValueData"
  return array_name, extracted_adf[array_name].value, extracted_adf[array_name].data_offset


def find_cells(
    extracted_adf: AdfValue,
    definition_indexes: int = None,
    data_type: int = None,
    value_index: int = None,
    ignore_cell: XlsxCell = None,
    verbose: bool = False,
  ) -> list[tuple[int, int, int]]:  # (sheet_index, cell_index, definition_index)
  matching_cells = []
  if definition_indexes:  # find cells with same definition index
    for sheet_index, sheet in enumerate(extracted_adf["Sheet"].value):
      matching_cells.extend([(sheet_index, cell_index, def_index) for cell_index, def_index in enumerate(sheet.value["CellIndex"].value) if def_index in definition_indexes])
  if data_type and value_index:  # find cells that point at the same value index
    defs_with_value_match = find_cell_definitions(extracted_adf["Cell"].value, data_type=data_type, value_indexes=[value_index], verbose=verbose)
    matching_cells.extend(find_cells(extracted_adf, definition_indexes=[i for (i,_d) in defs_with_value_match]))
  if ignore_cell:  # don't return the cell we're trying to match
    matching_cells = [c for c in matching_cells if c != (ignore_cell.sheet_index, ignore_cell.index, ignore_cell.definition_index)]
  return matching_cells


def find_cell_definitions(
    cell_definitions: list[AdfValue],
    data_type: int,
    value_indexes: list[int],
    verbose: bool = False,
  ) -> list[tuple[int, AdfValue]]:  # (definition_index, definition_object)
  defs_with_value_match = []
  defs_with_data_type_match = [(i,d) for i,d in enumerate(cell_definitions) if d.value["Type"].value == data_type]
  if verbose:
    print(f"Found {len(defs_with_data_type_match)} cell defs with data type {data_type}")
  if defs_with_data_type_match:
    defs_with_value_match = [def_tuple for def_tuple in defs_with_data_type_match if def_tuple[1].value["DataIndex"].value in value_indexes]
    if verbose:
      print(f"Found {len(defs_with_value_match)} cell defs that point at value index in {value_indexes}")
  return defs_with_value_match


def get_unused_cell_def_indexes(extracted_adf: AdfValue) -> list[int]:  # defitition_index
  unused_definition_indexes = set(range(len(extracted_adf["Cell"].value)))
  for sheet in extracted_adf["Sheet"].value:
    in_use = set(sheet.value["CellIndex"].value)
    unused_definition_indexes.difference_update(in_use)
  return list(unused_definition_indexes)


def get_unused_value_indexes_and_offsets(extracted_adf: AdfValue, data_array_name: str, data_type: int) -> list[dict]:  # (index, offset)
  # Check if any cell defs point at the value (we don't know if the definition is unused)
  # all_value_indexes = set(range(len(extracted_adf[data_array_name].value)))
  # assigned_value_indexes = set(d.value["DataIndex"].value for d in extracted_adf["Cell"].value)
  # unused_value_indexes = all_value_indexes - assigned_value_indexes
  # Check if any cells point at the value
  all_value_indexes = list(range(len(extracted_adf[data_array_name].value)))
  unused_value_indexes = []
  for value_index in all_value_indexes:
    if not find_cells(extracted_adf, data_type=data_type, value_index=value_index):
      unused_value_indexes.append(value_index)

  unused_value_indicies_and_offsets = []
  array_offset = extracted_adf[data_array_name].data_offset
  for index in unused_value_indexes:
    if data_array_name == "StringData":
      offset = extracted_adf[data_array_name].value[index].data_offset
    else:
      offset = array_offset + (index * 4)
    unused_value_indicies_and_offsets.append({"index": index, "offset": offset})
  return unused_value_indicies_and_offsets


def find_closest_value(value_array: list[float], desired_value: float) -> tuple[int, float]:
  match_index = None
  closest_delta = 9999999
  closest_match_index = None
  for i, number in enumerate(value_array):
    if float(number) == desired_value:
      match_index = i
      break
    delta = abs(float(number) - desired_value)
    if delta < closest_delta:
      closest_match_index = i
      closest_delta = delta
  if match_index is not None:
    return match_index, value_array[match_index]
  return closest_match_index, value_array[closest_match_index]


def calculate_coordinates(index: int, cols: int) -> str:
    cell_number = index + 1  # index starts at 0, cells start at A1
    row = math.ceil(cell_number / cols)
    col = cell_number - ( ( row - 1 ) * cols )
    return f"{get_column_letter(col)}{row}"

def get_column_range(start_col: str, end_col: str) -> list[str]:
    start_index = column_index_from_string(start_col)
    end_index = column_index_from_string(end_col)
    return [get_column_letter(i) for i in range(start_index, end_index + 1)]
