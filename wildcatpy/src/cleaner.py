import json
import pandas as pd
import pkg_resources
from wildcatpy.src.helper_functions import *

data_path = pkg_resources.resource_filename('wildcatpy', 'extractors/')

class dataCleaner:
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







