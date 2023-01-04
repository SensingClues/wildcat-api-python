"""Helper functions to clean data in WildcatApi"""

import pkg_resources
from typing import List

data_path = pkg_resources.resource_filename('wildcatpy', 'extractors/')


def select_columns(data: List[dict], keep_cols: list) -> List[dict]:
    """Select columns in a list of dictionaries

    :param data: List of dictionaries with keys representing columns in data
        extracted from Focus/Cluey.
    :param keep_cols: List of columns (keys) in data to keep.
    :returns: List of dictionaries for keys in keep_cols.
    """
    return [
        {key: item} for row in data for key, item in row.items()
        if key in keep_cols
    ]


def get_list_values(data: List[dict]):
    """Get values of dictionaries in a list

    :param data: List of dictionaries with keys representing columns in data
        extracted from Focus/Cluey.
    :returns: List of lists with the values in the dictionaries in the data.
    """
    return [list(row.values()) for row in data]
