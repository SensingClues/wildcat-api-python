"""Helper functions for WildcatApi"""

import copy
from datetime import datetime
import operator as python_ops
from typing import Any, Union
import warnings

DEFAULT_DATA_TYPES = ['observation', 'track']
DEFAULT_DT_FORMAT = {
    'date_from': "%Y-%m-%d",
    'date_until': "%Y-%m-%d",
    'time_from': "%H:%M:%S%z",
    'time_until': "%H:%M:%S%z",
}

COORD_PRECISION_LIMIT = 4


def make_query(data_type: Union[str, list] = None,
               groups: Union[str, list] = None,
               operator: Union[str, list] = 'intersects',
               # query_text: str = None,
               concepts: str = None,
               coord: dict = None,
               date_from: str = None,
               date_until: str = None,
               time_from: str = "00:00:00-00:00",
               time_until: str = "23:59:59-00:00",
               page_nbr: int = 1,
               page_length: int = 0,
               ) -> dict:
    """Build a query from user input arguments

    This function can be used by every method in WildcatAPI, since it
    allows for all possible filters via its kwargs.

    TODO:
     - query_text
     - page_nbr
     - page_length
     - operation
     - data_type (which options?)


    :param data_type: Type of data to extract. Level 0 of hierarchy in Focus.
        Must be one of ['observation', 'track']. Default is None, in which
        case data_type is set to ['observation', 'track'].
    :param groups: Names of groups to query from, e.g. "focus-project-7136973".
        Default is None.
    :param operator: Operation to perform in the query.
        Default is "intersects" (currently the only implemented option).
    :param concepts: Concept to search for, e.g. 'animal', specified as a Pool
        Party URL, e.g. "https://sensingclues.poolparty.biz/SCCSSOntology/186".
    :param query_text: Specify query text manually, e.g."entityId: 'exampleC'".
        TODO: do not include in make_query for now, does not work yet.
         - Check how the input should look like.
         - Check if query_text is additional or overwrites other kwargs.
    :param coord: Dictionary with coordinates, e.g.
        {"north": 90, "south": -40, "west": 10, "east": 90}. Default is None.
    :param date_from: Start date to filter data on. Required format is
        'YYYY-mm-dd'. Default is None.
    :param date_until: End date to filter data on. Required format is
        'YYYY-mm-dd'. Default is None.
    :param time_from: Start time on date_from to filter data on.
        Data for which the timestamp >= {date_from}{time_from} is returned.
        Default is "00:00:00-00:00", i.e. the start of the day at UTC.
    :param time_until: End time on date_until to filter data on.
        Data for which the timestamp < {date_from}{time_from} is returned, i.e.
        the filter excludes the exact time of time_until itself.
        Default is "23:59:59-00:00", i.e. the end of the day at UTC.
    :param page_nbr: Page number to start at. If both page_nbr and page_length
        are set, page_nbr = page_nbr * page_length + 1. Default is 1.
    :param page_length: Length of a page. Default is 0. TODO: meaning?

    :returns: Dictionary containing all elements of query as key-value pairs.
    """
    assert isinstance(operator, (str, list)), 'operator should be str or list.'
    if groups:
        assert isinstance(groups, (str, list)), \
            'groups should be str or list.'
    if data_type:
        assert isinstance(data_type, (str, list)), \
            'data_type should be str or list.'

    if not data_type:
        data_type = DEFAULT_DATA_TYPES

    if coord:
        check_coordinates(coord)

    for dt_var in DEFAULT_DT_FORMAT.keys():
        if eval(dt_var):
            validate_datetime(eval(dt_var), dt_var, DEFAULT_DT_FORMAT[dt_var])

    datetime_from = f"{date_from}T{time_from}" if date_from else None
    datetime_until = f"{date_until}T{time_until}" if date_until else None

    if page_nbr is None or page_length is None:
        page_nbr = None
    else:
        page_nbr = page_nbr * page_length + 1

    # Location of each variable in the nested query dictionary to be created.
    # To implement new vars, just add (<varname, [<cols><in><final><dict>])
    query_template = [
        (coord, ["filters", "geoQuery", "mapCoords"]),
        (operator, ["filters", "geoQuery", "operator"]),
        (datetime_from, ["filters", "dateTimeRange", "from"]),
        (datetime_until, ["filters", "dateTimeRange", "to"]),
        (data_type, ["filters", "entities"]),
        (concepts, ["filters", "concepts"]),
        (groups, ["filters", "dataSources"]),
        (page_nbr, ["options", "start"]),
        (page_length, ["options", "pageLength"]),
        # (query_text, ["filters", "queryText"]),  # TODO
    ]

    query_input = [var for var in query_template if var[0] is not None]

    query = {}
    for query_val, query_keys in query_input:
        query = make_nested_dict(query_val, query_keys, output_dict=query)

    return query


def make_nested_dict(value: Any,
                     all_keys: list,
                     output_dict: dict = None,
                     ) -> dict:
    """Build a nested dictionary

    If an existing dictionary is passed, this dictionary is updated with
    the specified value in a nested dict at the location specified in 'keys'.

    :param value: Value to add to the dictionary. Can be of multiple data types
        (e.g. str, int, float, datetime).
    :param all_keys: List of keys specifying the (nested) location of the value
        in the resulting dictionary.
    :param output_dict: Dictionary to update. Default is None, in which case
        a new dictionary is created.

    :returns: Dictionary updated with 'value' in location specified by 'keys'
    """
    if output_dict is None:
        output_dict = {}

    # use deepcopy to prevent elements in all_keys also being popped
    # from objects passed as all_keys during calls to make_nested_dict.
    keys = copy.deepcopy(all_keys)
    key = keys.pop(0)
    if len(keys) > 0 and output_dict.get(key, False):
        # keys contains at least 1 more level and key already exists in dict
        output_dict[key] = make_nested_dict(value, keys,
                                            output_dict=output_dict[key])
    elif len(keys) > 0 and not output_dict.get(key, False):
        # keys contains at least 1 more level and key does not exist in dict yet
        output_dict[key] = make_nested_dict(value, keys,
                                            output_dict={})
    else:
        # the deepest level specified keys has been reached, finalize the dict.
        output_dict[key] = value
    return output_dict


def check_coordinates(coord: dict) -> dict:
    """Check if coordinates are in accepted range

    Do so to ensure that MarkLogic does not return zero results.
    The coordinates are always sorted in order north, south, east, west.

    The precision used when querying Focus/Cluey is 4 decimals currently.
    Warn the user if more precise coordinates are specified.

    :param coord: Dictionary with north, south, east, west coordinates in degrees.
    :returns: Dictionary in which the coordinates have been sorted.
    """
    # specify required order of boundaries and their limit
    reqs = {
        "north": [90, python_ops.le],
        "east": [180, python_ops.le],
        "south": [-90, python_ops.ge],
        # setting west = -180 returns a JSONDecodeError, so set to -179.9999.
        "west": [-179.9999, python_ops.ge],
    }

    err_msg = f"Coordinates are required for north, east, south and west, " \
              f"but you only specified coordinates for {list(coord.keys())}"
    assert all([c in coord.keys() for c in reqs.keys()]), err_msg

    err_msg = f'All coordinates should be of a numeric type'
    assert all([isinstance(v, (int, float)) for v in coord.values()]), err_msg

    err_msg = 'Coordinate for north should be larger or equal to south'
    assert coord['north'] >= coord['south'], err_msg

    err_msg = 'Coordinate for east should be larger than or equal to west'
    assert coord['east'] >= coord['west'], err_msg

    for c, rule in reqs.items():
        limit, ops = rule
        v = coord[c]
        assert ops(v, limit), f'"{c}"-coordinate is {v} ' \
                              f'and exceeds limit {limit}'

    for c, v in coord.items():
        n_dec = str(v)[::-1].find('.')
        if n_dec > COORD_PRECISION_LIMIT:
            warn_msg = (
                f'The precision of coordinates used in query is limited'
                f' to {COORD_PRECISION_LIMIT} decimals, while you specified'
                f' {n_dec} for "{c}" ({v}). Note that digits beyond '
                f'{COORD_PRECISION_LIMIT} will be ignored.'
            )
            warnings.warn(warn_msg)

    sorted_coord = dict()
    for c in reqs.keys():
        sorted_coord[c] = coord[c]

    return sorted_coord


def recursive_get_from_dict(nested_dict: dict, keys: list) -> Any:
    """Recursively select data from a (nested) dictionary

    As long as 'keys' has more than 1 element, the function calls
    itself until the deepest level of the nested dictionary is reached,
    upon which the value for the corresponding key is returned.

    :param nested_dict: (Nested) dictionary to select elements from.
    :param keys: List of keys in a nested dictionary
    :returns: Value for deepest level in dictionary, or a call
        to this same function if the deepest level has not yet been reached.
    """
    head, *tail = keys
    if tail:
        return recursive_get_from_dict(nested_dict[head], tail)
    else:
        return nested_dict[head]


def validate_datetime(dt_val: str, dt_name: str, dt_format: str):
    """Validate format of a date or time

    :param dt_val: Date or time to evaluate
    :param dt_format: Format the date/time should adhere to.
    :param dt_name: Name or description of the date/time to evaluate.
    :raises: ValueError, TypeError
    """

    try:
        datetime.strptime(dt_val, dt_format)
    except ValueError:
        raise ValueError(f'{dt_name} should be of format {dt_format}, '
                         f'but is {dt_val}.')
    except TypeError:
        raise TypeError(f'{dt_name} should be of type "str", '
                        f'but is {type(dt_val)}.')
