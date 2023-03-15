Main functionality
==================

The main class is ``wildcatpy.api_calls``.

.. automodule:: wildcatpy.api_calls
   :members:
   :undoc-members:

Supporting modules
==================

Extractor
---------
Extracts specific elements from raw data returned by calls to Focus.
The elements to extract are specified in local JSON files, located in ``/wildcatpy/extractors/``.
Usage of these extractor-jsons makes it easier to add or change methods in the API.

.. automodule:: wildcatpy.src.data_extractor
   :members:
   :undoc-members:

Helper functions
----------------
Supporting functions used by other modules in the package.

.. automodule:: wildcatpy.src.helper_functions
   :members:
   :undoc-members:

Cleaner
-------
Supporting functions geared to cleaning or reshaping or processing of data.

.. automodule:: wildcatpy.src.data_cleaner
   :members:
   :undoc-members:


