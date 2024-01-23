"""Module to extract specific elements from raw Focus data"""

import json
from typing import List, Union

import pkg_resources

from wildcatpy.src import flatten_list, recursive_get_from_dict

data_path = pkg_resources.resource_filename("wildcatpy", "extractors/")

DEFAULT_EXTRACTION_TYPES = [
    "extract_values",
    "explode_values",
]


class DataExtractor(object):
    """Extract specific elements from raw data returned by calls to Focus.

    The elements to extract are specified in local JSON files, located in
    /wildcatpy/extractors/.

    N.B. If you want to extract different elements, e.g. because you are
    developing a new method for the WildCATApi-class, you can add your own
    json-files, without modifying this DataExtractor-class.

    N.B. This class currently only has 1 method, so it could be a function.
    We kept it as a class for now, as its functionality may be extended later.

    """

    def __init__(self, extractor_name: str):
        """Read and process extractor configuration

        Extractor configurations should all be located in wildcatpy/extractors/.

        :param extractor_name: Name of extractor configuration to use.
        """
        self.extractor_name = extractor_name
        self.extractor_path = data_path + extractor_name + ".json"
        self.extractor_cfg = get_extractor_cfg(self.extractor_path)
        self.ext_clean = process_extractor_cfg(self.extractor_cfg["extractor"])
        self._ext_cols_to_data = self.extractor_cfg["cols_to_data"]

    def extract_data(
        self, data: Union[dict, List[dict]], nested_col_names: bool = False
    ) -> List[dict]:
        """Extract data using extractor configuration

        :param data: Dictionary containing data from Focus.
        :param nested_col_names: Boolean indicating if columns to extract
            are nested. Default is False, in which case original column names
            are used in the output.
        :returns: List of dictionaries, which contains the records in the data.
        """
        # cols_to_data indicates if requested data is located deeper in dict.
        if len(self._ext_cols_to_data) > 0:
            data = recursive_get_from_dict(data, self._ext_cols_to_data)

        # ensure that a single row of data is also placed in a list
        if isinstance(data, dict):
            data = [data]

        # iterate through each row (which is a dictionary) in the extracted data
        output_data = [
            extract_row(row, self.ext_clean, nested_col_names) for row in data
        ]

        return flatten_list(output_data)


def extract_row(
    row: dict,
    extractor: List[dict],
    nested_col_names: bool,
) -> List[dict]:
    """Extract requested data from a row in the full dataset

    Note that the output may contain multiple records (when extraction_type =
    'explode_values'), although the input was only one row of the original data.

    :param row: Dictionary with data
    :param extractor: List of dictionaries specifying where in the dataset
        ('full_key') to extract which data from ('columns').
    :param nested_col_names: Boolean indicating if columns to extract are nested.
    """

    extract_vals = {}
    explode_vals = []
    for val in extractor:
        *nested_keys, extraction_type = val["full_key"]
        nested_names = "_".join([str(_) for _ in nested_keys])

        find_cols = val["columns"]
        data = (
            recursive_get_from_dict(row, nested_keys) if len(nested_keys) > 0 else row
        )
        if extraction_type == "extract_values":
            # simple extraction type, data can be extracted directly.
            extract_vals = {
                **extract_vals,
                **{
                    "_".join([nested_names, col])
                    if nested_col_names
                    else col: data[col]
                    for col in find_cols
                    if col in data.keys()
                },
            }
        elif extraction_type == "explode_values":
            # more complex extraction type, data consists of a list of dicts.
            # these dictionaries are exploded to get actual values.
            explode_vals.extend(
                [
                    {
                        "_".join([nested_names, col])
                        if nested_col_names
                        else col: record[col]
                        for col in find_cols
                        if col in record.keys()
                    }
                    for record in data
                ]
            )

        else:
            err_msg = (
                f"extraction_type should be one of "
                f"{DEFAULT_EXTRACTION_TYPES}, but is {extraction_type}."
            )
            raise NotImplementedError(err_msg)

    # ensure explode_vals is non-empty to enable combination with extract_vals
    if len(explode_vals) == 0:
        explode_vals = [{}]

    # note that the output may contain multiple records (in explode_vals),
    # although the input was only one row of the original data.
    return [{**extract_vals, **record} for record in explode_vals]


def get_extractor_cfg(extractor_path: str) -> dict:
    """Get extraction configuration from local JSON-file

    :param extractor_path: Location of JSON-file with extraction configuration.
    :returns: Dictionary with extraction configuration.
    """
    with open(extractor_path, "r") as f:
        return json.load(f)


def process_extractor_cfg(extractor_cfg: dict) -> List[dict]:
    """Process extractor configuration

    :param extractor_cfg: Raw configuration for data to extract from Focus.
    :returns: Processed configuration of extraction, usable by extract_data().
    """
    return [
        {"full_key": key, "columns": columns}
        for key, columns in translate_extractor_cfg(extractor_cfg)
    ]


def translate_extractor_cfg(extractor: dict, full_key: list = None) -> tuple:
    """Translate extraction configuration to list of columns to extract

    :param extractor: Dictionary with data to extract
    :param full_key: Initial list of keys specifying the starting location
        in a (nested) dict for which to return its value.
    :returns: Tuple with a list of keys specifying the location in a
        nested dict and value representing a list of fields to extract data for.
    """
    if full_key is None:
        full_key = []
    for key, value in extractor.items():
        if key.isnumeric():
            key = int(key)
        if isinstance(value, dict):
            # recursive call if value is of type dictionary
            yield from translate_extractor_cfg(value, full_key + [key])
        else:
            yield full_key + [key], value
