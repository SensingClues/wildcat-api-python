"""Helper functions for WildcatApi"""

import copy
import operator as python_ops


def make_nested_dict(value,
                     all_keys: list,
                     output_dict: dict = None,
                     ):
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


def make_query(bounds=None,
               operator=None,
               date_from=None,
               date_to=None,
               data_type=None,
               groups=None,
               query_text=None,
               concepts: str = None,
               page_nbr=1,
               page_length=0,
               end_time="T23:59:59-00:00",
               start_time="T00:00:00-00:00"
               ):
    """Build a query from user input arguments

    This function can be used by every method in WildcatAPI, since it
    allows for all possible filters via its kwargs.

    TODO: create asserts on input kwargs and correct description for each kwarg.

    :param bounds: dict with coordinates, e.g.
    {"north": 90, "south": -40, "west": 10, "east": 90"}
    :param operator: operation to perform in the query.
    Default is "intersects" (currently the only implemented option).
    :param date_from: start date to filter data on. Default is None.
    :param date_to: end date to filter data on. Default is None.
    :param data_type: type of data to extract. Level 0 of hierarchy in Focus.
    Must be one of ['Observation', 'track']. Default is None.
    :param concepts: Concept to search for, e.g. a tiger, in the format of
    an URL, e.g. “https://sensingclues.poolparty.biz/SCCSSOntology/97”.
    :param groups: Names of groups to query from, e.g. ["focus-project-7136973"].
    Default is None. TODO: check if both str and list allowed.
    :param query_text: specify query tect manually, e.g."entityId: 'exampleC'".
    TODO: check if query_text is additional or overwrites other kwargs.
    :param page_nbr: page number to start at. If both page_nbr and page_length
     are set, page_nbr = page_nbr * page_length + 1. Default is 1.
    :param page_length: Length of a page. Default is 0. TODO: meaning?
    :param start_time: start time of day, only used if start_date is set.
    Default is T00:00:00-00:00".
    :param end_time: end time of day, only used if end_time is set.
    Default is "T23:59:59-00:00".

    :returns: Dictionary containing all elements of query as key-value pairs.
    """
    if page_nbr is None or page_length is None:
        page_nbr = None
    else:
        page_nbr = page_nbr * page_length + 1

    time_from = f"{date_from}{start_time}" if date_from else None
    time_to = f"{date_to}{end_time}" if date_to else None

    # Location of each variable in the nested query dictionary to be created.
    # To implement new vars, just add (<varname, [<cols><in><final><dict>])
    query_template = [
        (bounds, ["filters", "geoQuery", "mapBounds"]),
        (operator, ["filters", "geoQuery", "operator"]),
        (time_from, ["filters", "dateTimeRange", "from"]),
        (time_to, ["filters", "dateTimeRange", "to"]),
        (data_type, ["filters", "entities"]),
        (concepts, ["filters", "concepts"]),
        (groups, ["filters", "dataSources"]),
        (page_nbr, ["options", "start"]),
        (page_length, ["options", "pageLength"]),
        (query_text, ["filters", "queryText"]),
    ]

    query_input = [var for var in query_template if var[0] is not None]

    query = {}
    for query_val, query_keys in query_input:
        query = make_nested_dict(query_val, query_keys, output_dict=query)

    return query


def check_bounds(bounds: dict) -> dict:
    """Check if bounds (coordinates) are in accepted range

    Do so to ensure that MarkLogic does not return zero results.
    The coordinates are always sorted in order north, south, east, west.

    :param bounds: Dictionary with north, south, east, west bounds in degrees.
    :returns: Dictionary in which the coordinates have been sorted.
    """
    # specify required order of boundaries and their limit
    # TODO: check necessity for -1 degree difference for south and west
    reqs = {
        "north": [90, python_ops.le],
        "east": [180, python_ops.le],
        "south": [-89, python_ops.ge],
        "west": [-179, python_ops.ge],
    }

    err_msg = f"Coordinates required for north, east, south and west, " \
              f"but only have {bounds.keys()}"
    assert all([c in bounds.keys() for c in reqs.keys()]), err_msg

    for c, rule in reqs.items():
        limit, ops = rule
        v = bounds[c]
        assert ops(v, limit), f"{c}-coordinate is {v} and exceeds limit {limit}"

    sorted_bounds = dict()
    for c in reqs.keys():
        sorted_bounds[c] = bounds[c]

    return sorted_bounds


def recursive_get_from_dict(nested_dict, keys):
    """Recursively select data from a (nested) dictionary

    While the list ks has more than 1 element, the function calls
    itself until the deepest level of the nested dictionary is reached,
    upon which the value for the corresponding key is returned.

    :param nested_dict: Dictionary to select from
    :param keys: list of keys in a nested dictionary
    :returns: value for deepest-level key in dictionary, or a call
    to this same function if the deepest level has not yet been reached.
    """
    head, *tail = keys
    if tail:
        return recursive_get_from_dict(nested_dict[head], tail)
    else:
        return nested_dict[head]
