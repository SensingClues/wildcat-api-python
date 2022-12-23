"""Main WildcatApi-class"""

import geopandas
import io
import math
import numpy as np
import pandas as pd
import requests

from wildcatpy.src import (
    DataCleaner,
    DataExtractor,
    make_query,
)

DEFAULT_EXCLUDE_PIDS = ['track', 'default']


class WildcatApi:
    """Class to extract various types of SensingClues-data"""

    def __init__(self, user_name: str, password: str):
        """
        Automatically login when initiate class
        :param user_name: Username for focus
        :param password: Password for focus
        """
        self.session = requests.Session()
        self.login(user_name, password)

    def _api_call(self,
                  action,
                  url_addition,
                  payload: dict = None):
        """Main method to make requests from Focus/Cluey

        This method can be called by all methods available in WildcatApi

        :param action: Type of request, currently post or get
        :param url_addition: what to add to the base url
        :param payload: the payload that has to be sent
        :return:
        """

        url = "https://focus.sensingclues.org/api/" + url_addition
        request_trans = {
            "post": self.session.post,
            "get": self.session.get
        }
        extra_args = {
            "headers": {'Content-type': 'application/json'}
        }
        if payload:
            extra_args["json"] = payload

        r = request_trans[action](
            url,
            **extra_args
        )
        # add extra status codes
        if r.status_code == 200:
            pass  # print(f"req to {url} success")
        elif r.status_code == 204:
            print(f"req to {url}, sucessfull logout")  # only seen by logout
        elif r.status_code == 404:
            raise TypeError(f"unknown url {url}")
        elif r.status_code == 405:
            raise TypeError(f"Check post/get for url {url}")
        else:
            raise TypeError(f"Unknow error {str(r.status_code)}, {r.json()} ")
        return r

    def login(self, username: str, password: str):
        """Function to log in to Focus/Cluey

        Login is done automatically when initiating the WildcatApi-class.
        
        :param username: Username for focus
        :param password: Password for focus
        :return: Api call result
        """

        url_addition = "auth/login"
        payload = {
            'username': username,
            'password': password,
        }
        return self._api_call("post", url_addition, payload)

    def logout(self):
        """Function to log out of Focus/Cluey

        :return: Api call result

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
        r = self._api_call("post", url_addition, payload)
        extr = DataExtractor("groups_extractor")
        data = extr.extr(r.json())
        cleaner = DataCleaner(data)
        df = cleaner.list_to_pd()

        df = df[['name', 'value', 'count']]
        df = df.rename(columns={
            'value': 'description',
            'count': 'n_records',
        })
        return df

    def _close_session(self):
        self.session.close()

    def track_extractor(self, groups, **kwargs):

        """
        Function to acquire tracks data. 
        This function takes the **kwargs argument. This means that extra arguments can be 
        added. Those arguments are used to call subfunctions. The allowed extra arguments are added
        in the parameters. The group argument is mandatory, the rest is optional
    
        For an overview of the extra arguments allowed, see
        the description of make_query in helper functions.

        TODO: Can copy argument-description back here once finalized.

        :param groups: Name(s) of groups to query from,
        e.g. "focus-project-7136973". TODO: check if both str and list allowed.

        """
        return self._iterate_api(groups,
                                 **kwargs,
                                 data_type=["track"],
                                 extractor_name="track_extractor",
                                 )

    def observation_extractor(self,
                              groups: str,
                              include_subconcepts: bool = True,
                              **kwargs) -> pd.DataFrame:
        """Extract observations from Focus/Cluey
        
        For an overview of the extra arguments (kwargs)allowed, see
        the description of make_query in helper_functions.

        TODO: Can copy argument-description back here, once finalized.

        :param groups: Name of group or list of groups to query from,
        e.g. "focus-project-7136973".
        :param include_subconcepts: Whether or not keep observations related to
            concepts lower in the hierarchy than the concept filtered on using
            the concepts-kwarg. For instance, if you filter on 'animal'
            (concepts = "https://sensingclues.poolparty.biz/SCCSSOntology/186"),
            you will also obtain entries for e.g. 'hippo' (which is an 'animal')
            if include_subconcepts is True. Default is True.

        :returns: Dataframe with observations according to the query parameters
        specified in kwargs (if any).
        """
        col_trans = {
            "label": "conceptLabel"
        }

        df = self._iterate_api(groups,
                               **kwargs,
                               data_type=["observation"],
                               extractor_name="observation_extractor",
                               )

        concepts = kwargs.get("concepts", None)
        if concepts is not None and df.shape[0] > 0:
            if not include_subconcepts:
                df = df.loc[df["conceptId"] == concepts]

        df = df.rename(columns=col_trans)
        return df

    def _iterate_api(
            self,
            groups,
            data_type,
            extractor_name,
            _page_length=10,
            **kwargs  # extra args for make_query such as begin and end time

    ):
        """
        Iterates to df and makes calls <-- update 
        
        :param groups: Filter on the group 
        :param data_type: 
        """
        output_data = []
        extra_request = True
        first_iter = True
        page_nbr = 0
        extr = DataExtractor(extractor_name)
        # fix timestamp!!
        while extra_request:  # while loop so first call can directly be used
            query = make_query(data_type=data_type,
                               groups=groups,
                               page_length=_page_length,
                               page_nbr=page_nbr,
                               **kwargs)
            r = self._api_call("post", "search/all/results", query)
            if first_iter:
                nbr_pages = math.ceil(r.json()["total"] / _page_length)
                if nbr_pages == 0:
                    break
            data = extr.extr(r.json())
            cleaner = DataCleaner(data)
            output_data.extend(cleaner.get_list_dict())
            if page_nbr == nbr_pages:
                break
            page_nbr += 1
        return DataCleaner(output_data).list_to_pd()

    def add_geojson_to_track(self, metadata_input: pd.DataFrame) -> pd.DataFrame:
        """
        Takes track metadata and adds geojson to it

        :param track_metadata: the output of the track_extractor function 
        :return: Df containing the tracks with the geojson
        """
        import copy
        track_metadata = copy.deepcopy(metadata_input)  # make shallow copy from old dataframe
        url_addition = "map/all/track/0/features/"
        track_metadata["endWhen"] = pd.to_datetime(track_metadata["endWhen"], infer_datetime_format=True)
        track_metadata["startWhen"] = pd.to_datetime(track_metadata["startWhen"], infer_datetime_format=True)
        track_metadata["patrolDuration"] = round(
            (track_metadata["endWhen"] - track_metadata["startWhen"])
            / pd.Timedelta(hours=1), 3)
        track_metadata["length"] = round(track_metadata["length"], 3)
        unique_routes = track_metadata["entityId"].unique()  # only look through unique routes
        for i, entity in enumerate(unique_routes):
            payload = make_query(query_text=f"entityId:'{entity}'")
            r = self._api_call("post", url_addition, payload)
            new_df = geopandas.read_file(io.BytesIO(r.content))
            if i == 0:
                df = new_df
            else:
                df = pd.concat([df, new_df], ignore_index=True, sort=False)
        return df.merge(track_metadata, how="right", left_on="EntityId", right_on="entityId")

    def get_all_layers(self,
                       exclude_pids: list = None) -> pd.DataFrame:
        """Get layers to which the user has access

        :param exclude_pids: List of pids to exclude, in addition to
        ['track', 'default'], which are always excluded. Default is None,
        in which case exclude_pids is set to ['track', 'default'].
        :returns: pd.DataFrame with project id's and layer names
        """

        if not exclude_pids:
            exclude_pids = DEFAULT_EXCLUDE_PIDS
        else:
            exclude_pids += DEFAULT_EXCLUDE_PIDS
        exclude_pids = [str(x) for x in exclude_pids]

        cols_to_rename = {
            "id": "lid",
            "name": "layerName"
        }
        url_addition = "/map/all/describe"

        r = self._api_call("get", url_addition)
        output = r.json()

        # key 'pid' is added to access layers in layer_feature_extractor.
        layer_output = [{**{"pid": key}, **output["models"][key]}
                        for key in output["models"].keys()]

        extractor = DataExtractor("all_layers")
        extracted_output = extractor.extr(layer_output)
        df = pd.DataFrame(extracted_output) \
            .rename(columns=cols_to_rename)

        df = df.loc[~df['pid'].isin(exclude_pids)]
        return df

    def layer_feature_extractor(self,
                                project_name: str = None,
                                project_id: int = None,
                                layer_id: int = None,
                                **kwargs):
        """Extract details for a specific layer

        :param project_name: Name of project to extract layer features for.
        If not specified, project_id and layer_id should be. Default is None.
        :param project_id: id of project to extract. Default is None.
        :param layer_id: id of layer to extract. Default is None.

        :returns: geopandas.DataFrame with features of the requested layer

        """

        all_layers = self.get_all_layers(**kwargs)

        if project_name:
            project_layer = all_layers.loc[all_layers['layerName'] ==
                                           project_name]
            if np.shape(project_layer)[0] > 0:
                project_id = project_layer['pid'].astype(int).values[0]
                layer_id = project_layer['lid'].astype(int).values[0]
            else:
                raise ValueError(f'No layer available for project_name '
                                 f'{project_name}')
        else:
            msg = (f'If not providing a project_name, '
                   f'please specify the project_id and layer_id.')
            assert (isinstance(project_id, int) and isinstance(layer_id,
                                                               int)), msg

        url_addition = f"map/all/{project_id}/{layer_id}/features/"

        r = self._api_call("post", url_addition)

        # relevant geometry information can be read using geopandas
        gdf = geopandas.read_file(io.BytesIO(r.content))

        # TODO: do we even need the other details?
        output = r.json()
        extr = DataExtractor("layer_features")
        extr_output = extr.extr(output, nested_col_names=True)
        df = pd.DataFrame(extr_output)
        gdf = pd.concat([gdf, df], axis=1)

        return gdf
