import json
import pandas as pd
from wildcatpy.src.helper_functions import *
import pkg_resources

data_path = pkg_resources.resource_filename('wildcatpy', 'extractors/')

class dataExtractor:
    def __init__(self,
                 input_data
                 ):
        self.input_data = input_data
        self.data = input_data

    def deeper_in_nested(self, keys):
        self.data = recurGet(self.data, keys)

    def select_columns(self, keep_cols):
        self.data = [
            {key: item} for row in self.data \
            for key, item in row.items() \
            if key in keep_cols
        ]

    def list_to_pd(self):
        return pd.DataFrame(self.data)

    def flatten_data(self):
        self.data = sum(self.data, [])

    def get_list_dict(self):
        return self.data

    def get_list_values(self):
        return [[_ for _ in row.values()] for row in self.data]

    def get_extractor_json(self, file_name):
        with open(f"{data_path}{file_name}.json", "r") as f:
            return find_values_to_extract(json.load(f))

    def iterate_extractor(self, extractor_file_name):
        new_data = []
        for row in self.data:
            new_data.append(self.extract_with_extractor(row, extractor_file_name))
        self.data = new_data

    def extract_with_extractor(self,
                               data_for_extract,
                               extractor_file_name
                               ):
        new_data = {}
        additional = [{}]  # if it isn't made in the extraction of exploding columns
        for extract_val in self.get_extractor_json(extractor_file_name):
            if len(extract_val["all_columns"]) > 0:
                full_key = extract_val["full_key"]
                all_columns = extract_val["all_columns"]
                data = recurGet(data_for_extract, full_key)
                new_data = {**new_data, **{key: data[key] for key in all_columns}}
        for extract_val in self.get_extractor_json(extractor_file_name):
            if len(extract_val["explode_values"]) > 0:
                full_key = extract_val["full_key"]
                data = recurGet(data_for_extract, full_key)
                all_extr_columns = extract_val["explode_values"]
                if len(data) > 0:
                    additional = [{col: row[col] for col in all_extr_columns if row.get(col,False)} for row in data ]
        return [{**new_data, **add} for add in additional]






