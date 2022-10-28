import math
import json


def make_nested_dict(value,
                     keys,
                     output_dict=None,
                     ):
    if output_dict == None:
        output_dict = {}
    key = keys.pop(0)
    if (len(keys) > 0 and output_dict.get(key, False)):  # if more then one key and dict key exists
        output_dict[key] = make_nested_dict(value, keys, output_dict[key])
    elif (len(keys) > 0 and not output_dict.get(key, False)):  # if more then one key and dict key doesn't exist
        output_dict[key] = make_nested_dict(value, keys, {})
    else:  # if only 1 key left finalize the dict
        output_dict[key] = value
    return output_dict


def make_query(bounds=None,
               operator = None,
               date_from=None,
               date_to=None,
               type_analysis=None,
               groups=None,
               query_text = None,
               concepts = None,
               page_nbr=1,
               page_length=0,
               end_time = "T23:59:59-00:00", #if someone has to make very specific calls change this
               start_time = "T00:00:00-00:00"
              ):


    """

    :param bounds: dict with coordinates {"north": 90, "south": 90, "west": 90,"east":90"}
    :param operator: The operator that will be put in the query, for example ["intersects"]
    :param date_from: start date for the query
    :param date_to: end date of the query
    :param type_analysis: for example ["Observation", "track"]
    :param groups: for example ["focus-project-7136973"]
    :param query_text: for example entityId: 'exampleE
    :param page_nbr: Which page number to start (call will recalc page number when page_length is given)
    :param page_length: How many pages should a request contain
    :param end_time: For a timestamp for end_date, format = T00:00:00-00:00"
    :param start_time:For a timestamp for start_date, format = T00:00:00-00:00"
    :return:
    """
    page_nbr = None if (page_nbr == None or page_length == None) else page_nbr* page_length +1
    time_from = None if date_from == None else f"{date_from}{start_time}" #add date and time
    time_to = None if date_to == None else f"{date_to}{end_time}" #add date and time

    # shows the value and where it should be placed in the dictionary
    # For new vars just add (<varname, [<cols><in><final><dict>])
    output_prep = [
        (bounds, ["filters", "geoQuery", "mapBounds"]),
        (operator, ["filters", "geoQuery", "operator"]),
        (time_from, ["filters", "dateTimeRange", "from"]),
        (time_to, ["filters", "dateTimeRange", "to"]),
        (type_analysis, ["filters", "entities"]),
        (concepts, ["filters", "concepts"]),
        (groups, ["filters", "dataSources"]),
        (page_nbr, ["options", "start"]),
        (page_length, ["options", "pageLength"]),
        (query_text, ["filters", "queryText"])
    ]

    final_output = [_ for _ in output_prep if _[0] != None]  # only return non None vars
    # convert output_prep to query
    query = make_nested_dict(*final_output[0])  # init query with first row (no output_dict yet)
    for row in final_output[1:]:
        query = make_nested_dict(*row, query)  # loop for the rest, send output dict so it is updated
    print(query)
    return query


def check_bounds(bounds: dict) -> dict:
    """
    check if bounds are in range so marklogic does not return zero results
    :param bounds: dict with north,south,east,west bounds
    :return: fixed bounds if needed
    """
    # should contain correct data
    assert [_ for _ in bounds.keys()].sort() == \
           ["north","east","south","west"].sort(),"please provide north,east,south,west"
    bounds["north"] = 90 if bounds["north"]  > 90 else bounds["north"]
    bounds["south"] = -89 if bounds["south"]  < -89 else bounds["south"]
    bounds["east"] = 180 if bounds["east"]  > 180 else bounds["east"]
    bounds["west"] = -179 if bounds["west"]  < -179 else bounds["west"]
    return bounds

def find_values_to_extract(extractor,
                           values_to_extract = None,
                           full_key = None,
                          ):
    if values_to_extract == None:
        values_to_extract = []
    if full_key == None:
        full_key = []
    for key,value in extractor.items():
        if key.isnumeric(): #check bc there can be integers
            key = int(key)
        if key == "extract_values":
            values_to_extract.append({"full_key":full_key, "all_columns": value, "explode_values": []})
        elif key == "explode_values":
            values_to_extract.append({"full_key":full_key, "all_columns": [], "explode_values": value})

        else:
            new_key = full_key + [key]
            values_to_extract.extend(find_values_to_extract(value,
                                     full_key=new_key)
                                    )
    return values_to_extract

def recurGet(d, ks):
    head, *tail = ks
    return recurGet(d[head], tail) if tail else d[head]

