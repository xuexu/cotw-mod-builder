import math
from openpyxl.utils import column_index_from_string, get_column_letter
from openpyxl.utils.cell import coordinate_from_string

class XlsxCell:
    __slots__ = (
        'coordinates',
        'sheet_name',
        'index',
        'offset',
        'definition_index',
        'definition_offset',
        'data_type',
        'data_type_offset',
        'data_index',
        'definition_data_offset',
        'data_value',
        'data_offset',
    )

    def __init__(self, extracted_adf: dict, sheet: dict, index: int = None, coordinates: str = None, desired_value: any = None) -> None:
        if index is None and coordinates is None:
            raise ValueError('Must provide one of "coordinates" or "index"')
        self.sheet_name = sheet["Name"].value.decode("utf-8")
        if coordinates:
            self.coordinates = coordinates
            col_str, row = split_col_and_row(coordinates)
            col = column_index_from_string(col_str)
            self.index = ( ( row - 1 ) * sheet["Cols"].value ) + col - 1
        else:
            self.index = int(index)
            self.calculate_coordinates(self.index, sheet["Cols"].value)
        self.offset = sheet["CellIndex"].data_offset + ( self.index * 4 )
        self.definition_index = int(sheet["CellIndex"].value[self.index])
        self.definition_offset = extracted_adf["Cell"].value[self.definition_index].data_offset
        cell_value = extracted_adf["Cell"].value[self.definition_index].value
        self.definition_data_offset = cell_value["DataIndex"].data_offset
        self.data_type = int(cell_value["Type"].value)
        self.data_type_offset = int(cell_value["Type"].data_offset)
        self.data_index = int(cell_value["DataIndex"].value)
        if self.data_type == 0:
            self.data_value = extracted_adf["BoolData"].value[self.data_index]
            self.data_offset = extracted_adf["BoolData"].data_offset + ( self.data_index * 4 )
        if self.data_type == 1:
            self.data_value = extracted_adf["StringData"].value[self.data_index].value
            self.data_offset = extracted_adf["StringData"].value[self.data_index].data_offset
        if self.data_type == 2:
            self.data_value = extracted_adf["ValueData"].value[self.data_index]
            self.data_offset = extracted_adf["ValueData"].data_offset + ( self.data_index * 4 )

    def as_dict(self) -> dict:
        return {slot: getattr(self, slot) for slot in self.__slots__}

    def calculate_coordinates(self, index: int, cols: int) -> str:
        cell_number = index + 1
        row = math.ceil(cell_number / cols)
        col = cell_number - ( ( row - 1 ) * cols )
        self.coordinates = f"{get_column_letter(col)}{row}"


def split_col_and_row(coordinates) -> tuple[str, int]:
    return coordinate_from_string(coordinates)