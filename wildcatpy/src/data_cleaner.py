"""Helper functions to clean data in WildcatApi"""

import pkg_resources
from typing import List

data_path = pkg_resources.resource_filename('wildcatpy', 'extractors/')


def flatten_list(nested_list: list) -> list:
    """Flatten a nested list into a new list

    :param nested_list: A (potentially) nested list
    :returns: A list containing all the elements in the original list
    """
    return [item for sublist in nested_list for item in sublist]


def get_list_values(data: List[dict]):
    """Get values of dictionaries in a list

    :param data: List of dictionaries with keys representing columns in data
        extracted from Focus.
    :returns: List of lists with the values in the dictionaries in the data.
    """
    return [list(row.values()) for row in data]


def select_columns(data: List[dict], keep_cols: list) -> List[dict]:
    """Select columns in a list of dictionaries

    :param data: List of dictionaries with keys representing columns in data
        extracted from Focus.
    :param keep_cols: List of columns (keys) in data to keep.
    :returns: List of dictionaries for keys in keep_cols.
    """
    return [
        {key: item} for row in data for key, item in row.items()
        if key in keep_cols
    ]
