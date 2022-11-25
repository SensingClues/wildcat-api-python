import pkg_resources
from wildcatpy.src.helper_functions import *

data_path = pkg_resources.resource_filename('wildcatpy', 'extractors/')


def extr_trans(extr, full_key=None):
    """
    Translates extractor given by user to something readable by code
    Output gives the full key: What are the nested keys we have to go through
                     columns: Which columns to extract from this full key

    """
    if full_key == None:  # first (non recursive) call the full key is None and make it empty
        full_key = []
    for key, value in extr.items():
        if key.isnumeric():  # check bc there can be integers
            key = int(key)
        if type(value) is dict:  # if value is another dict make recursive call
            yield from extr_trans(value, full_key + [key])  # for every item in value make call
        else:
            yield (full_key + [key], value)


def extr_row(row, extr,nested_col_names):
    extr_val, expl_val = {}, []
    for val in extr:
        *cols, type_extr = val["full_key"]  # get the columns to loop though and type lookup
        nested_names = "_".join([str(_) for _ in cols])
        # extract everything till reach the level we start extracting
        find_cols = val["columns"]
        filt_data = recurGet(row, cols) if len(cols) > 0 else row
        if type_extr == "extract_values":  # lookup type 1: Just simply get the variable
            extr_val = {**extr_val,
                        **{nested_names + "_" + key if nested_col_names else key:
                               filt_data.get(key, False) for key in find_cols}}
        # Lookup type 2 explode_values
        # This means that the cols give back a list 
        # Which contains a list of dictionaries. Those dictionaries should be exploded
        # We make a list of dictionaries with all the colums from the extracter that we can find
        # Later on those have to be exploded
        elif type_extr == "explode_values":
            # I use row.get(col,None) != None instead of row.get(col,False) because we can found a 0 which
            # which is similar to False. So then we lose values
            expl_val.extend([{nested_names + "_" + col if nested_col_names else col: row[col]
                              for col in find_cols if row.get(col, None) != None}
                             for row in filt_data])
    # in case no exploded values need to be searched it cannot be empty
    # becasue the combination code would give an empty dict
    # so check if exlo is empty and make non empty without data if it is 
    if len(expl_val) == 0: 
        expl_val = [{}]
    # Over here the extract_values and exploded_values are combined
    # The data is not on the same level yet, extract_values = {} and expl_val =[{}]
    # However, every dict in the list of expl_val is related to all the data in extract_values
    # Moreover, we make one dict (row) that contains all extract_values and one dict from expl_val
    # So, even do we only handle one row of input data the output can be multiple rows due to explode_cols
    return [{**extr_val, **add} for add in expl_val]


check_nested = lambda x: any(isinstance(y, dict) for y in x.values())


class dataExtractor:
    """
    This class extracts data from raw input based on a json input file.
    Moreover, we have an json file that is easy to read and update and this file is 
    used to extract the correct data from the raw input. This has two advantages: 
        1. Updates in the output data can be easily implemented in the json which is readible 
           by everyone. <-- update this ... 
        2. No code updates needed for data changes. Just change the input json 
        3. Easily implementing new funcions. We don't have to manually program but just give a json

    This extractor does a couple of things: 
        1. Read the converter based on the name given! Converters need to be put in the wildcatpy/extractors
           folder!! 
        2. Before we can use the data extractor we have to convert it from human readible
           to computer readible
        3. Provide functionality to convert raw data to output data 
    """

    def __init__(self, extractor_name):
        self.extr_name = extractor_name
        self.ext_path = data_path + extractor_name + ".json"
        self._ext_info = self.get_ext_raw(self.ext_path)
        self._ext_clean = self.get_ext_clean(self._ext_info["extractor"])
        self._ext_data_path = self._ext_info["cols_to_data"]

    def get_ext_raw(self, ext_path: str):
        """
        Get the raw extractor
        """
        with open(ext_path, "r") as f:
            return json.load(f)

    def get_ext_clean(self, ext_raw):
        return [{"full_key": key, "columns": value} for key, value in extr_trans(ext_raw)]

    def extr(self, data,nested_col_names=False):
        """

        """
        # only if we need to go deeper in data recurGet should be called
        # Otherwise it's called without arguments and crashes
        if len(self._ext_data_path) > 0: 
            data = recurGet(data,self._ext_data_path )
        # it can happen that only one row of data is given
        # So no list of dicts but only one dict
        # Put it in a list so the code doesn't start iterating a dict
        if isinstance(data,dict):
            data = [data]
        # Iterate through dataset extract for every row
        # flatten with sum 
        return sum([extr_row(row, self._ext_clean,nested_col_names) for row in data], [])






