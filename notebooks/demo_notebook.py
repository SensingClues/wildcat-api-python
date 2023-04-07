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
# This demo shows the available functionality using default settings for parameters. For more detail on what you can configure as a user, see the documentation and description of individual methods in the WildCATApi-class.
#
# ### Before you start
#
# To be able to run this notebook, you should:
# - install the wildcat-api-python package in a virtual environment (`pip install -e .` from the main directory of the repository).
# - install the requirements in requirements.txt (if not already installed automatically in the previous step).
# - create a file '.env' in the root of the wildcat-api-python-repository, containing your Cluey credentials. These will be read in this notebook to log in. The file should look like this:
# ```
# # Cluey credentials
# USERNAME=your_username
# PASSWORD=your_password
# ```

# ## Configuration

from wildcatpy.api_calls import WildCATApi
from wildcatpy.src import helper_functions as helpers
from dotenv import load_dotenv
import matplotlib.pyplot as plt
import json
import os
import pandas as pd

plt.style.use('ggplot')

load_dotenv()

# %load_ext autoreload
# %autoreload 2

username = os.getenv("USERNAME") # you can also type your password here manually
password = os.getenv('PASSWORD') # You can also type your username here manually


# ## Demo-time, here we go!

api_call = WildCATApi(username, password)

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

observations['agentName'] = '#####'
observations.head()

# ### Get track metadata
#
# Note that you can control the scope (e.g. coordinates) of these observations in more detail than done here.
#
# TODO: provide detailed instructions.

tracks = api_call.track_extractor(groups=groups, time_until="23:59:54-00:00")

tracks['agentName'] = '#####'
tracks.head()

# ### Add geosjon to track
#
# Note that you can control the scope (e.g. coordinates) of these observations in more detail than done here.
#
# TODO: provide detailed instructions.

track_entities = tracks['entityId'].unique().tolist()
tracks_geo = api_call.add_geojson_to_track(track_entities)

tracks_merged = tracks.merge(tracks_geo, how="left", on="entityId")

tracks_merged['agentName'] = '#####'
tracks_merged.head()

# ### Get all available layers (projects)

layers = api_call.get_all_layers()

layers

# ### Get details (features) for an individual layer

df = api_call.layer_feature_extractor(project_name='test_polygon')

# #### [optional] Plot available geometries (requires Folium)

# +
# # !pip install folium
# -

import folium

poly_map = folium.Map([51.9244, 4.4777], zoom_start=8, tiles='cartodbpositron')
for _, geometry in df['geometry'].items():
    folium.GeoJson(geometry).add_to(poly_map)
folium.LatLngPopup().add_to(poly_map)
poly_map


# ### Get all available concepts and their hierarchy
#
# As shown later in this notebook, you can use this information to subsequently query:
# - the details for a specific concept
# - check the occurrence of each concept in the group(s) of observations you have access to.

hierarchy = api_call.get_hierarchy()

hierarchy.info()

# ### Get details for specific concepts in the hierarchy
#
# You can get information on children or the parents of a concept in the hierarchy by filtering on its label or id. Use the available helper functions to do so. For example, you could do the following for the concept of a "Kite" (oid = "https://sensingclues.poolparty.biz/SCCSSOntology/222"):
#
# ```
# oid = "https://sensingclues.poolparty.biz/SCCSSOntology/222"
# helpers.get_children_for_id(hierarchy, oid)
# helpers.get_parent_for_id(hierarchy, oid)
# helpers.get_label_for_id(hierarchy, oid)
# ```
#
# or, if filtering on the label itself:
#
# ```
# label = 'Kite'
# helpers.get_children_for_label(hierarchy, label)
# helpers.get_parent_for_label(hierarchy, label)
# helpers.get_id_for_label(hierarchy, label)
# ```
#
# N.B. Alternatively, you could directly filter the `hierarchy`-dataframe yourself of course.

# #### Tell me, what animal belongs to this concept id?

oid = "https://sensingclues.poolparty.biz/SCCSSOntology/222"
helpers.get_label_for_id(hierarchy, oid)

# #### Does this Kite have any children?

label = 'Kite'
children_label = helpers.get_children_for_label(hierarchy, label)
children_label


# #### What are the details for these children?

hierarchy.loc[hierarchy['id'].isin(children_label)]

# ### Count concepts related to observations
#
# Get the number of observations per concept in the ontology (hierarchy), e.g. the number of observations listed as a "Kite" ("https://sensingclues.poolparty.biz/SCCSSOntology/222").
#
# You can filter on for instance:
# - `date_from` and `date_until`. 
# - A list of child concepts, e.g. by extracting children for the label "Animal sighting" from hierarchy (see example below).
# - Note that specifying a range of coordinates (via `coord`) currently does **not** work as a filter.

date_from = '2022-01-01'
date_until = '2023-01-01'
label = 'Animal sighting'
children_label = helpers.get_children_for_label(hierarchy, label)
concept_counts = api_call.get_concept_counts(groups, 
                                             date_from=date_from, date_until=date_until,
                                             concepts=children_label)
concept_counts

# #### Example: visualize concept counts
#
# To make the visualization intelligible, you can add information on labels from the `hierarchy`-dataframe.

min_freq = 5
concept_freq = concept_counts.merge(hierarchy, left_on='_value', right_on='id', how='left')
concept_freq['label'] = concept_freq['label'].fillna(concept_freq['_value'])
concept_freq = concept_freq.set_index('label')['frequency'].sort_values(ascending=True)
concept_freq.loc[concept_freq >= min_freq].plot(kind='barh');
plt.title(f"Number of observations per concept in group(s)\n'{groups}' for label '{label}'\n"
          f"[{date_from} to {date_until} and minimum frequency {min_freq}]", 
          fontsize=12);
plt.xlabel('Number of observations per concept label');
plt.ylabel('Label of concept');


