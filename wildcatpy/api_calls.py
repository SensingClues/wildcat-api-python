"""Main WildCATApi-class"""

import io
import math
import warnings
from typing import List, Union

import geopandas
import numpy as np
import pandas as pd
import requests

from wildcatpy import wclogging
from wildcatpy.src import DataExtractor, align_extractor, make_query

logger = wclogging.get_wc_logger()

FOCUS_BASE_URL = "https://focus.sensingclues.org/api/"

ALLOWED_REQUEST_TYPES = ["post", "get"]
DEFAULT_EXCLUDE_PIDS = ["track", "default"]


class WildCATApi(object):
    """Class to extract various types of SensingClues-data"""

    def __init__(self, user_name: str, password: str):
        """Automatically log in when initiating class

        :param user_name: Username for Focus
        :param password: Password for Focus
        """
        self.session = requests.Session()
        self.login(user_name, password)

    def login(self, username: str, password: str) -> requests.models.Response:
        """Function to log in to Focus

        Login is done automatically when initiating the WildCATApi-class.

        :param username: Username for focus
        :param password: Password for focus

        :return: The response to the request made to Focus.
        """

        url_addition = "auth/login"
        payload = {
            "username": username,
            "password": password,
        }
        return self._api_call("post", url_addition, payload)

    def logout(self) -> requests.models.Response:
        """Function to log out of Focus

        :return: The response to the request made to Focus.

        """
        url_addition = "auth/logout"
        return self._api_call("post", url_addition, {})

    def get_groups(self) -> pd.DataFrame:
        """Get overview of groups to which the user has access

        :returns: Dataframe with available groups
        """
        url_addition = "search/all/facets"
        payload = make_query(
            data_type=["observation", "track"],  # TODO: why these types only?
        )
        req = self._api_call("post", url_addition, payload)
        extractor = DataExtractor("groups")
        data = extractor.extract_data(req.json())

        df = pd.DataFrame(data)
        df = df[["name", "value", "count"]]
        df = df.rename(
            columns={
                "value": "description",
                "count": "n_records",
            }
        )
        return df

    def get_observations(
        self, groups: str, include_subconcepts: bool = True, **kwargs
    ) -> pd.DataFrame:
        """Method to acquire observations data from Focus

        Extra (filter) arguments can be passed to this method via kwargs.
        For an overview of the extra arguments allowed, see
        the description of make_query() in helper_functions.py.

        :param groups: Name(s) of groups to query from, passed as a string
            or as a list of strings, e.g. "focus-project-7136973".
        :param include_subconcepts: If filtering on concepts (using the
            concepts-kwarg), this argument allows you to include or exclude
            observations related to concepts lower in the hierarchy than the
            concept you filtered on. For instance, if you filter on 'animal'
            (concepts = "https://sensingclues.poolparty.biz/SCCSSOntology/186")
            , you will also obtain entries for e.g. 'hippo' (which is an
            'animal') if include_subconcepts is True. Default is True.

        :returns: Dataframe with available observations, in line with the
            query parameters specified in kwargs (if any).
        """
        col_trans = {"label": "conceptLabel"}

        obs = self._iterate_api(
            groups,
            data_type=["observation"],
            extractor_name="observations",
            **kwargs,
        )

        concepts = kwargs.get("concepts", None)
        if concepts is not None and obs.shape[0] > 0:
            if not include_subconcepts:
                logger.info(f"Filtering observations on concepts {concepts}.")
                obs = obs.loc[obs["conceptId"] == concepts]

        obs = obs.rename(columns=col_trans)
        return obs

    def get_tracks(
        self, groups: Union[str, list], precision: int = 3, **kwargs
    ) -> pd.DataFrame:
        """Method to acquire tracks data from Focus

        Extra (filter) arguments can be passed to this method via kwargs.
        For an overview of the extra arguments allowed, see
        the description of make_query() in helper_functions.py.

        :param groups: Name(s) of groups to query from, passed as a string
            or as a list of strings, e.g. "focus-project-7136973".
        :param precision: Number of decimals used to round the length and
            duration (hours) of the track. Default is 3.

        :returns: Dataframe with available tracks, in line with the
            query parameters specified in kwargs (if any).

        """
        tracks = self._iterate_api(
            groups,
            data_type=["track"],
            extractor_name="tracks",
            **kwargs,
        )

        if not tracks.empty:
            tracks["startWhen"] = pd.to_datetime(
                tracks["startWhen"], infer_datetime_format=True
            )
            tracks["endWhen"] = pd.to_datetime(
                tracks["endWhen"], infer_datetime_format=True
            )

            tracks["length"] = round(tracks["length"], precision)
            tracks["patrolDuration_hours"] = (
                tracks["endWhen"] - tracks["startWhen"]
            ) / pd.Timedelta(hours=1)
            tracks["patrolDuration_hours"] = round(
                tracks["patrolDuration_hours"], precision
            )

        return tracks

    def add_geojson_to_track(
        self,
        track_entities: List[str],
    ) -> pd.DataFrame:
        """Get geojson data for tracks

        For each unique track, extract geojson data (if available in Focus).

        :param track_entities:
            List of entityId's for tracks to get geojson for.
        :returns: Dataframe with track geojson-data.
        """

        url_addition = "map/all/track/0/features/"

        df = pd.DataFrame()
        unique_routes = np.unique(track_entities)
        for i, entity in enumerate(unique_routes):
            payload = make_query(query_text=f"entityId:'{entity}'")
            req = self._api_call("post", url_addition, payload)
            df_entity = geopandas.read_file(io.BytesIO(req.content))
            if not df_entity.empty:
                logger.debug(f"Found geojson data for track {entity}.")
            else:
                logger.debug(f"No geojson data found for track {entity}.")
            df = pd.concat([df, df_entity], ignore_index=True, sort=False)

        if not df.empty:
            df = df.rename(columns={"EntityId": "entityId"})

        return df

    def get_all_layers(self, exclude_pids: list = None) -> pd.DataFrame:
        """Get layers to which the user has access

        :param exclude_pids: List of pids to exclude, in addition to
            ['track', 'default'], which are always excluded. Default is None,
            in which case exclude_pids is set to ['track', 'default'].
        :returns: Dataframe with project id's and layer names.
        """

        if not exclude_pids:
            exclude_pids = DEFAULT_EXCLUDE_PIDS
        else:
            exclude_pids += DEFAULT_EXCLUDE_PIDS
        exclude_pids = [str(x) for x in exclude_pids]

        cols_to_rename = {"id": "lid", "name": "layerName"}
        url_addition = "/map/all/describe"

        req = self._api_call("get", url_addition)
        output = req.json()

        # key 'pid' is added to access layers in layer_features.
        layer_output = [
            {**{"pid": key}, **output["models"][key]} for key in output["models"].keys()
        ]

        extractor = DataExtractor("all_layers")
        extracted_output = extractor.extract_data(layer_output)

        df = pd.DataFrame(extracted_output).rename(columns=cols_to_rename)

        df = df.loc[~df["pid"].isin(exclude_pids)]
        return df

    def get_layer_features(
        self,
        layer_name: str = None,
        project_id: int = None,
        layer_id: int = None,
        exclude_pids: list = None,
    ) -> geopandas.GeoDataFrame:
        """Extract details for a specific layer

        :param layer_name: Name of project to extract layer features for.
            If not specified, project_id and layer_id should be. Default None.
        :param project_id: id of project to extract. Default is None.
        :param layer_id: id of layer to extract. Default is None.
        :param exclude_pids: List of pids to exclude, in addition to
            ['track', 'default'], which are always excluded. Default is None.

        :returns: geopandas.DataFrame with features of the requested layer.

        """
        all_layers = self.get_all_layers(exclude_pids=exclude_pids)

        if layer_name:
            project_layer = all_layers.loc[all_layers["layerName"] == layer_name]
            if np.shape(project_layer)[0] > 0:
                project_id = project_layer["pid"].astype(int).values[0]
                layer_id = project_layer["lid"].astype(int).values[0]
            else:
                raise ValueError(f"No layer available for layer_name " f"{layer_name}")
        else:
            msg = (
                "If not providing a layer_name, "
                "please specify the project_id and layer_id."
            )
            if not (isinstance(project_id, int) and isinstance(layer_id, int)):
                raise ValueError(msg)

        url_addition = f"map/all/{project_id}/{layer_id}/features/"
        req = self._api_call("post", url_addition)

        # relevant geometry information can be read using geopandas
        gdf = geopandas.read_file(io.BytesIO(req.content))

        # TODO:
        #  some layers have additional columns, so implement option to extract
        #  all available information, without using a extractor-json.
        output = req.json()
        extractor = DataExtractor("layer_features")
        data = extractor.extract_data(output, nested_col_names=True)
        df = pd.DataFrame(data)
        gdf = pd.concat([gdf, df], axis=1)

        return gdf

    def get_hierarchy(self) -> pd.DataFrame:
        """Get available concepts and their hierarchy

        :returns: Dataframe with available concepts in their hierarchy
        """
        url_addition = "ontology/all/hierarchy?language=en"
        payload = {}
        req = self._api_call("get", url_addition, payload)

        extractor = DataExtractor("hierarchy")
        output = req.json()

        # move information on each concept one level up and ignore keys, as
        # these are the same as the 'id' for each entry in output['concepts'].
        hierarchy_output = output["concepts"].values()
        data = extractor.extract_data(hierarchy_output)
        df = pd.DataFrame(data)

        top_concepts = output["topConcepts"]
        df["isTopConcept"] = False
        df.loc[df["id"].isin(top_concepts), "isTopConcept"] = True

        return df

    def get_concept_counts(self, groups: Union[str, list], **kwargs) -> pd.DataFrame:
        """Get counts per ontology concept in observation data

        Extra (filter) arguments can be passed to this method via kwargs.
        For an overview of the extra arguments allowed, see
        the description of make_query() in helper_functions.py.
        Note that coordinates can currently not be passed.

        :param groups: Name(s) of groups to query from, passed as a string
            or as a list of strings, e.g. "focus-project-7136973".
        :returns:
            Dataframe with frequency per concept in filtered observations.
        """

        url_addition = "ontology/all/counts"

        if "coord" in kwargs.keys():
            warnings.warn(
                f"Coordinates cannot be used yet in queries of"
                f" '{url_addition}' and will be ignored."
            )
            kwargs.pop("coord")

        payload = make_query(
            groups=groups,
            data_type=["observation"],
            **kwargs,
        )

        # 'options'-key in payload is not accepted by /ontology/all/counts.
        payload.pop("options")
        req = self._api_call("post", url_addition, payload)

        extractor = DataExtractor("concept_count")
        output = req.json()
        data = extractor.extract_data(output)
        df = pd.DataFrame(data)

        return df

    def _api_call(
        self, action: str, url_addition: str, payload: dict = None
    ) -> requests.models.Response:
        """Main method to make requests from Focus

        This method can be called by all methods available in WildCATApi

        :param action: Type of request, currently 'post' or 'get'.
        :param url_addition: Suffix to base url. Depends on the data requested.
        :param payload: Arguments to be added to the request, such as
            date filters. Default is None.

        :returns: The response to the request made to Focus.

        """
        url = FOCUS_BASE_URL + url_addition
        request_trans = {"post": self.session.post, "get": self.session.get}
        extra_args = {"headers": {"Content-type": "application/json"}}
        if payload:
            extra_args["json"] = payload

        err_msg = f"action must be in {ALLOWED_REQUEST_TYPES}, but is {action}"
        assert action in ALLOWED_REQUEST_TYPES, err_msg

        req = request_trans[action](url, **extra_args)
        # add extra status codes
        if req.status_code == 200:
            # successful request
            pass
        elif req.status_code == 204:
            print(f"Request to {url}, successful logout")
        elif req.status_code == 404:
            raise TypeError(f"Unknown url {url}")
        elif req.status_code == 405:
            raise TypeError(f"Request type {action} not allowed for url {url}.")
        else:
            raise TypeError(
                f"Unknown error {str(req.status_code)}, "
                f"request returned {req.json()}"
            )

        return req

    def _close_session(self):
        """Private method to close the session

        N.B. Currently unused.
        """
        self.session.close()

    def _iterate_api(
        self,
        groups,
        extractor_name: str,
        # TODO: why set page_length here instead of make_query?
        #  what is impact? how does it differ between methods?
        page_length: int = 10,
        **kwargs,
    ) -> pd.DataFrame:
        """Make iterative calls to Focus API to collect requested data

        :param groups: Name(s) of groups to query from, passed as a string
            or as a list of strings, e.g. "focus-project-7136973".
        :param extractor_name: Name of extractor configuration to use.
        :returns: Dataframe with requested data.
        """
        output_data = []
        extractor = DataExtractor(extractor_name)

        # first, determine number of available records.
        query = make_query(groups=groups, page_length=page_length, page_nbr=0, **kwargs)
        req = self._api_call("post", "search/all/results", query)
        nbr_pages = math.ceil(req.json()["total"] / page_length)
        nbr_pages_decile = math.ceil(nbr_pages / 10)
        logger.info(
            f"Group '{groups}' contains {req.json()['total']} records"
            f" for data type '{extractor_name}'."
        )

        # second, verify extractor definition is correct for this particular
        # group by using the first record in the query results.
        if req.json()["total"] > 0:
            # content of the first record in query results
            record_content = req.json()["results"][0]["extracted"]["content"]
            ext_clean_o = align_extractor(extractor.ext_clean, record_content)
            extractor.ext_clean = ext_clean_o

            # extract the data
            logger.info("Started reading available records.")
            for i_page in range(nbr_pages):
                if np.mod(i_page, nbr_pages_decile) == 0:
                    logger.debug(f"Reading page {i_page:>3d} out of {nbr_pages} pages.")
                query = make_query(
                    groups=groups, page_length=page_length, page_nbr=i_page, **kwargs
                )
                req = self._api_call("post", "search/all/results", query)
                data = extractor.extract_data(req.json())
                output_data.extend(data)
            logger.info("Finished reading available records.")
        else:
            logger.warning(
                f"No data available for '{extractor_name}',"
                " returning empty dataframe."
            )

        df = pd.DataFrame(output_data)
        return df
