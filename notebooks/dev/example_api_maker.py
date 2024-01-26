# ---
# jupyter:
#   jupytext:
#     text_representation:
#       extension: .py
#       format_name: light
#       format_version: '1.5'
#       jupytext_version: 1.14.1
#   kernelspec:
#     display_name: Python 3 (ipykernel)
#     language: python
#     name: python3
# ---

# # Demo of developing a new method for Wildcat API
#
# This notebook shows an example of how to create a method for the Wildcat API: `get_all_layers`, a method which extracts an overview of available project layers from Focus. When running the example, you only see layers to which you have access.
#
# Note that this method is already part of the Wildcat python-package. You can create new methods in a similar fashion.

# ## Configuration

import os

import pandas as pd
from dotenv import load_dotenv

from wildcatpy.api_calls import WildCATApi
from wildcatpy.src import DataExtractor


# ### Login details
#
# The preferred approach to provide your Cluey login details is to:
# - create a file '.env' in the root of the wildcat-api-python-repository, containing:
# <br>`# Cluey credentials`
# <br>`USERNAME=your_username`
# <br>`PASSWORD=your_password`
# - call load_dotenv() from the *dotenv*-package (install via `!python3 -m pip install python-dotenv`)
# - read the username and password using the *os*-package.
#
# This prevents your login details from ending up in this notebook and even the repository. Alternatively, you can specify these details manually (not preferred).

load_dotenv()

username = os.getenv("USERNAME")  # you can also type your username here manually
password = os.getenv("PASSWORD")  # You can also type your password here manually

# initialize API
api_call = WildCATApi(username, password)

# ## 1. Create get_all_layers

# ### Check available content
#
# - You can use the private function `_api_call` to check information available for a certain url.
# - The base url is https://focus.sensingclues.org/api/.
# - To obtain information on layers, we add `"/map/all/describe"`.

add = "/map/all/describe"
output = api_call._api_call("get", add, {}).json()
print(output)

# The above shows the elements available. The elements relevant to layer-information need to be placed in a new json-file, which is used by the DataExtractor-class to process the data.

# set the relevant part for the get_all_layers-method
key_of_interest = "models"

# ### Create json-file for DataExtractor
#
# The content defined below should be placed in a json-file in *wildcatpy/extractors/*. In this example, the content below is stored as `wildcatpy/extractors/all_layers.json`.
#
# #### Detailed notes on json-structure
#
# You can check the DataExtractor to understand how the nested elements in the json are being processed. In short:
#
# - cols_to_data is used to move deeper into a nested dict when needed. In this case this is not needed, as we need the models-key for get_all_layers, which already contains the layer overview.
# - Per row, it will extract the values in the extract_values argument
# - It will explode every row with values that are in the explode_values
# - For this particular case, we will also get rows for two projects called 'default' and 'track'. We fix this afterwards by filtering.

# the content of this 'all_layers.json' is used for the get_all_layers-method.
{
    "cols_to_data": [],
    "extractor": {
        "extract_values": ["pid"],
        "layers": {"explode_values": ["id", "name", "geometryType"]},
    },
}

# ### Apply DataExtractor to created json
#
# To extract all available layers with the DataExtractor-class, we need to apply a small change to the output we received from `_api_call` above. This ensures that the structure of `output[key_of_interest]` in this case is consistent with other calls.
#
# #### Detailed notes
#
# The DataExtractor requires a list from which it can start extracting, while the content of `output[key_of_interest]` is a nested dict. Therefore, we convert the dict to a list of dicts and add the type of layer ('track' or 'default') as item in the list.

output_pid = [
    {**{"pid": key}, **output[key_of_interest][key]}
    for key in output[key_of_interest].keys()
]


output_pid

extr = DataExtractor("all_layers")
extr_output = extr.extract_data(output_pid)

extr_output

# create a dataframe from the output of the DataExtractor
col_trans = {"id": "lid"}
df = (
    pd.DataFrame(extr_output)
    .rename(columns=col_trans)
    .query("pid != 'track' and pid != 'default'")
)


df.head()

# ### Create and test method
#
# - Combine the steps above into the new method
# - Test the new function by extend the existing WildCATApi-class.
# - If the function works here, you can implement it in api_calls.py.
#
# Note: the `get_all_layers`-method is relatively simple, but we aim to illustrate the concept here.

# +
DEFAULT_EXCLUDE_PIDS = ["track", "default"]


class TestNewAPI(WildCATApi):
    def get_all_layers(self, exclude_pids: list = None):
        if not exclude_pids:
            exclude_pids = DEFAULT_EXCLUDE_PIDS
        else:
            exclude_pids += DEFAULT_EXCLUDE_PIDS
        exclude_pids = [str(x) for x in exclude_pids]

        cols_to_rename = {"id": "lid", "name": "layerName"}
        url_addition = "/map/all/describe"

        r = self._api_call("get", url_addition)
        output = r.json()

        # key 'pid' is added to access layers in layer_feature_extractor.
        layer_output = [
            {**{"pid": key}, **output["models"][key]} for key in output["models"].keys()
        ]

        extractor = DataExtractor("all_layers")
        extracted_output = extractor.extract_data(layer_output)
        df = pd.DataFrame(extracted_output).rename(columns=cols_to_rename)

        df = df.loc[~df["pid"].isin(exclude_pids)]
        return df


# +
# run test if it works
# if so we can implement it
test = TestNewAPI(username, password)
df = test.get_all_layers()

# a quick assertion on the output
expected_cols = ["pid", "lid", "layerName", "geometryType"]
assert [
    c in df.columns for c in expected_cols
], "Not all expected columns are in the output."
# -

# Success! (at least regarding the columns, that is).
#
# - You can develop new methods in a similar fashion. See the methods already available in *api_calls.py* for more examples how to extract the correct fields om Cluey/Focus.
# - Further, the R-library *wildcat-api-r* provides additional methods which could be created here as well (or you could experiment with using a conversion package like *rpy2*).
