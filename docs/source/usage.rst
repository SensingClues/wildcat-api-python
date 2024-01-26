Usage
-----

The best way to get acquainted with the functionality availability in wildcat-api-python is
to check the :ref:`tutorial`-section.

Methods which are currently implemented are:

- ``login`` and ``logout``: Connect to the database.
- ``get_groups``: Obtain overview of groups you have access to.
- ``get_observations``: Extract observations.
- ``get_tracks``: Extract track data.
- ``add_geojson_to_track``: Add geospatial information to track data.
- ``get_all_layers``: Obtain overview of all layers you have access to.
- ``layer_feature_extractor``: Extract detailed information on a layer.
- ``get_hierarchy``: Get full hierarchy (ontology) used in database.
- helper functions related to the hierarchy/ontology, such as ``get_label_for_id`` and ``get_children_for_label``.
- ``get_concept_counts``: Get number of occurrences for a specific concept in the ontology.

Some methods, like those to extract data on observations and tracks, can be filtered
on for instance dates, coordinates and specific elements in the ontology.
See the detailed `API-documentation <https://wildcat-api-python.readthedocs.io/en/latest/#>`_
of each function to check which filters are available.
