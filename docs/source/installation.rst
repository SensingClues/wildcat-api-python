Installation
------------

There are various methods to install ``wildcat-api-python``.

For any method, we recommend using a virtual environment when installing the library, such as pyenv or virtualenv.
To download the source code and install the library::

    git clone https://github.com/SensingClues/wildcat-api-python.git
    cd </parent_location_of_the_library/wildcat-api-python/>
    pip install .
    pip install -r requirements.txt

You can also install the repository directly from GitHub:

- Get a personal acces token
    - Upper right corner of git click on picture
    - Go to settings
    - Developer settings
    - Personal access token
    - Generate new token
    - read access
- Install the repository::

    pip install git+https://<personal_access_token>@github.com/SensingClues/wildcat-api-python.git@main
    pip install -r requirements.txt
    pip install jupytext

Further, we recommend using ``jupytext`` when working with Jupyter notebooks. Install it like so::

    pip install jupytext


Finally, you should create an account in the Cluey-app to obtain credentials which you need
to use this library.