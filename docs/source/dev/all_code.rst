

Main module
==========
This part contains the main code of the api. Moreover, the code that is used by the end users

.. automodule:: wildcatpy.api_calls
   :members:
   :undoc-members:

Sub modules
===========

Extractor
---------
| The extractor takes a json file from the extractors directory and translates this do data type which is
  readable by the program. With help from this json files it knows which data to extract and where to
  look for this data. Which makes changing / addding api's easier.
.. automodule:: wildcatpy.src.data_extractor
   :members:
   :undoc-members:

Helper functions
----------------
| Functions used by other submodules/ main module

.. automodule:: wildcatpy.src.helper_functions
   :members:
   :undoc-members:

Cleaner
-------
| Standard cleaning that has to be done in different scopes can be automated with this lib
.. automodule:: wildcatpy.src.cleaner
   :members:
   :undoc-members:


