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

# # Demo of functionality available in wildcat-api-python
#
# This demo shows the available functionality using default settings for parameters. For more detail on what you can configure as a user, see the documentation and description of individual methods in the WildcatApi-class.
#
# ### Before you start
#
# To be able to run this notebook, you should:
# - install the wildcat-api-python package in a virtual environment (`pip install -e .` from the main directory of the repository).
# - install the requirements in requirements.txt (if not already installed automatically in the previous step).
# - create a file '.env' in the root of the wildcat-api-python-repository, containing your Cluey credentials. These will be read in this notebook to log in. The file should look like this:
# <br>`# Cluey credentials`
# <br>`USERNAME=your_username`
# <br>`PASSWORD=your_password`

# ## Configuration

from wildcatpy.api_calls import WildcatApi
from wildcatpy.src import helper_functions as helpers
from dotenv import load_dotenv
import json
import os
import pandas as pd

import pdb


load_dotenv()

# %load_ext autoreload
# %autoreload 2

username = os.getenv("USERNAME") # you can also type your password here manually
password = os.getenv('PASSWORD') # You can also type your username here manually


# ## Demo-time, here we go!

api_call = WildcatApi(username, password)

# ### Login 

# expected output if successful: '<Response [200]>'
api_call.login(username, password)

# +
# It is not necessary to log out, but you can do so by calling:
# api_call.logout()
# -

# ### Obtain the groups you have access to

info = api_call.get_groups()

info.head()

# for other functionality, you can specify a group to extract data from
groups = "focus-project-7136973"

# ### Get observations
#
# Note that you can control the scope (e.g. coordinates) of these observations in more detail than done here.
#
# TODO: provide detailed instructions.


observations = api_call.observation_extractor(groups=groups, operator=["intersects"])

observations.info()

observations.head()

# ### Get track metadata
#
# Note that you can control the scope (e.g. coordinates) of these observations in more detail than done here.
#
# TODO: provide detailed instructions.

tracks = api_call.track_extractor(groups=groups, time_until="23:59:54-00:00")

tracks.head()

# ### Add geosjon to track
#
# Note that you can control the scope (e.g. coordinates) of these observations in more detail than done here.
#
# TODO: provide detailed instructions.

tracks_geo = api_call.add_geojson_to_track(tracks)

tracks_geo.head()

# ### Get all available layers (projects)

layers = api_call.get_all_layers()

layers

# ### Get details (features) for an individual layer

df = api_call.layer_feature_extractor(project_name='test_polygon')

# #### [optional] Plot available geometries (requires Folium)

# !pip install folium

import folium

poly_map = folium.Map([51.9244, 4.4777], zoom_start=8, tiles='cartodbpositron')
for _, geometry in df['geometry'].items():
    folium.GeoJson(geometry).add_to(poly_map)
folium.LatLngPopup().add_to(poly_map)
poly_map


# ### Get all available concepts and their hierarchy
#
# You can 

hierarchy = api_call.get_hierarchy()

hierarchy.info()

# ### Get details for specific concepts in the hierarchy
#
# You can get information on children or the parents of a concept in the hierarchy by filtering on its label or id. Use the helper functions to do so. For example, you could do the following for the concept of a "Kite" ("https://sensingclues.poolparty.biz/SCCSSOntology/222"):
#
# ```
# oid = "https://sensingclues.poolparty.biz/SCCSSOntology/222"
# helpers.get_children_for_id(hierarchy, oid)
# helpers.get_parent_for_id(hierarchy, oid)
# helpers.get_label_for_id(hierarchy, oid)
# ```
#
# or, if filtering on a label:
#
# ```
# label = 'Kite'
# helpers.get_children_for_label(hierarchy, label)
# helpers.get_parent_for_label(hierarchy, label)
# helpers.get_id_for_label(hierarchy, label)
# ```
#
# Alternatively, you can also filter the hierarchy-dataframe yourself of course.

oid = "https://sensingclues.poolparty.biz/SCCSSOntology/222"
helpers.get_label_for_id(hierarchy, oid)

label = 'Kite'
helpers.get_children_for_label(hierarchy, label)


