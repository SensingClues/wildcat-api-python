# WildCAT API to extract data from SensingClues' Cluey-app 

## Introduction

`wildcat-api-python` allows Python-users to connect to SensingClues' database and download 
data logged in the Cluey-app and data available in Focus. This includes data such as
wildlife observations and tracks, custom map layers, and the wildlife ontology used by 
SensingClues.

**Note:** you need credentials for the [Cluey](https://sensingclues.org/cluey)-app to 
connect to the database.

## Installation

There are various methods to install `wildcat-api-python`.

For any method, we recommend using a virtual environment when installing the library, such as pyenv or virtualenv.
To download the source code and install the library:

```python
git clone https://github.com/SensingClues/wildcat-api-python.git
cd </parent_location_of_the_library/wildcat-api-python/>
pip install .
pip install -r requirements.txt
```

You can also install the repository directly from GitHub:
- Get a personal acces token
  - Upper right corner of git click on picture
  - Go to settings
  - Developer settings
  - Personal access token
  - Generate new token
  - read access
- Install the repository:
```python
pip install git+https://<personal_access_token>@github.com/SensingClues/wildcat-api-python.git@main
pip install -r requirements.txt
pip install jupytext
```

Further, we recommend using `jupytext` when working with Jupyter notebooks. Install it like so:
```python
pip install jupytext
```

Finally, you should create an account in the Cluey-app to obtain credentials which you need
to use this library.

## Usage

The best way to get acquainted with the functionality availability in wildcat-api-python is 
to check the notebook `notebooks/demo_notebook.py.`

Methods which are currently implemented are:
- `login` and `logout`: Connect to the database.
- `get_groups`: Obtain overview of groups you have access to.
- `observation_extractor`: Extract observations. 
- `track_extractor`: Extract track data.
- `add_geojson_to_track`: Add geospatial information to track data.
- `get_all_layers`: Obtain overview of all layers you have access to.
- `layer_feature_extractor`: Extract detailed information on a layer.
- `get_hierarchy`: Get full hierarchy (ontology) used in database.
- helper functions related to the hierarchy/ontology, such as `get_label_for_id` and
`get_children_for_label`
- `get_concept_counts`: Get number of occurrences for a specific concept in the ontology.

Some methods, like those to extract data on observations and tracks, can be filtered
on for instance dates, coordinates and specific elements in the ontology.
See the detailed [API-documentation](https://wildcat-api-python.readthedocs.io/en/latest/#) 
of each function to check which filters are available. 
