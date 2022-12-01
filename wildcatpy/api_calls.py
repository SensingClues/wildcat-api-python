#username = "jobvancreij"
#password =

import requests
import json
import geopandas
from wildcatpy.src.helper_functions import *
import pandas as pd
from wildcatpy.src.cleaner import dataCleaner
from wildcatpy.src.data_extractor import dataExtractor
import io


class WildcatApi:
    """
    Class which can be used to extract sensing clues data 
    
    """
    def __init__(self, user_name: str,password: str):
        """
        Autoamtically login when initiate class
        :param user_name: Username for focus
        :param password: Password for focus
        """
        self.session = requests.Session() #session object to share between calls
        self.login(user_name,password)

    def _api_call(self,
                 action,
                 url_addition,
                 payload = {}):
        """
        One function for a requests made so we only need to program logic once (catching errors etc)
        
        :param action: Type of request, currently post or get
        :param url_addition: what to add to the base url
        :param payload: the payload that has to be send
        :return:
        """

        url = "https://focus.sensingclues.org/api/" + url_addition
        request_trans = {
            "post": self.session.post,
            "get": self.session.get
        }
        # extra args that have to be send
        extra_args = {
            "headers": {'Content-type': 'application/json'}
        }
        if payload:  # only add payload if it is not empty
            extra_args["json"] = payload

        r = request_trans[action](
            url,
            **extra_args
        )
        # add extra status codes
        if r.status_code == 200: pass # print(f"req to {url} success")
        elif r.status_code == 204: print(f"req to {url}, sucessfull logout") #only seen by logout
        elif r.status_code == 404: raise TypeError(f"unknown url {url}")
        elif r.status_code == 405: raise TypeError(f"Check post/get for url {url}")
        else: raise TypeError(f"Unknow error {str(r.status_code)}, {r.json()} ")
        return r


    def login(self,username: str,password: str):
        """
        Have to login before making requests. The login is done automatically 
        when initiating the class
        
        :param username: Username for focus
        :param password: Passowrd for focus
        :return: Api call result
        """

        url_addition = "auth/login"
        payload = {
            'username': username,
            'password': password,
        }
        return self._api_call("post",url_addition, payload)

    def logout(self):
        """
        Logs the user out

        :return: Api call result

        """
        url_addition = "auth/logout"
        return self._api_call("post",url_addition, {})

    def get_groups(self) -> pd.DataFrame:
        """
        Function to get the groups to which the user has access
        :return: df with groups
        """
        url_addition = "search/all/facets"
        payload = make_query(
            date_from= "1900-01-01",
            date_to= "9999-12-31",
            type_analysis = ["Observation", "track"],
            page_nbr=1,
            page_length=0
        )
        r = self._api_call("post", url_addition, payload)
        extr = dataExtractor("groups_extractor")
        data = extr.extr(r.json())
        cleaner = dataCleaner(data)
        return cleaner.list_to_pd()

    def get_all_layers(self,
                       exclude_pids: list = None) -> pd.DataFrame:
        """Get layers to which the user has access

        :param exclude_pids: List of pids to exclude, in addition to
        ['track', 'default'], which are always excluded. Default is None,
        in which case exclude_pids is set to ['track', 'default'].
        :returns: pd.DataFrame with layer names and id's
        """

        default_exclude_pids = ['track', 'default']
        if not exclude_pids:
            exclude_pids = default_exclude_pids
        else:
            exclude_pids.append(default_exclude_pids)

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

        extractor = dataExtractor("all_layers")
        extracted_output = extractor.extr(layer_output)
        df = pd.DataFrame(extracted_output) \
               .rename(columns=cols_to_rename)
        df = df.loc[~df['pid'].isin(exclude_pids)]
        return df

    def _close_session(self):
        self.session.close()

    def track_extractor(self, groups, **kwargs):

        """
        Function to acquire tracks data. 
        This function takes the **kwargs argument. This means that extra arguments can be 
        added. Those arguments are used to call subfunctions. The allowed extra arguments are added
        in the parameters. The group argument is mandotory, the rest is optional
    
        :param groups: for example ["focus-project-7136973"]
        :param bounds: dict with coordinates {"north": 90, "south": 90, "west": 90,"east":90"}
        :param operator: The operator that will be put in the query, for example ["intersects"]
        :param date_from: start date for the query
        :param date_to: end date of the query
        :param type_analysis: for example ["Observation", "track"]
        :param query_text: for example entityId: 'exampleE
        :param page_nbr: Which page number to start (call will recalc page number when page_length is given)
        :param page_length: How many pages should a request contain
        :param end_time: For a timestamp for end_date, format = T00:00:00-00:00"
        :param start_time:For a timestamp for start_date, format = T00:00:00-00:00"

        """
        return self._iterate_api(groups,
                                     **kwargs,
                                     type_analysis=["track"],
                                     extractor_name="track_extractor",
                                     )

    def observation_extractor(self,
                              groups: str,
                              **kwargs) -> pd.DataFrame: 
        """
        Extract observations 
        
        This function takes the **kwargs argument. This means that extra arguments can be 
        added. Those arguments are used to call subfunctions. The allowed extra arguments are added
        in the parameters. The group argument is mandotory, the rest is optional
        
        :param groups: for example ["focus-project-7136973"]
        :param bounds: dict with coordinates {"north": 90, "south": 90, "west": 90,"east":90"}
        :param operator: The operator that will be put in the query, for example ["intersects"]
        :param date_from: start date for the query
        :param date_to: end date of the query
        :param type_analysis: for example ["Observation", "track"]
        :param query_text: for example entityId: 'exampleE
        :param page_nbr: Which page number to start (call will recalc page number when page_length is given)
        :param page_length: How many pages should a request contain
        :param end_time: For a timestamp for end_date, format = T00:00:00-00:00"
        :param start_time: For a timestamp for start_date, format = T00:00:00-00:00"
        :return: Df containing the observations according to the filters
        """
        col_trans = {
            "label": "conceptLabel"
        }
        
        df = self._iterate_api(groups,
                                   **kwargs,
                                   type_analysis=["observation"],
                                   extractor_name="observation_extractor",
                                   )
        # Extra filter implementation 
        # If you filter  on concepts other concepts from an observation that had the 
        # filtered concept are returned. So do another filtering 
        concepts = kwargs.get("concepts", None)
        if concepts is not None:
            df = df.loc[df["conceptId"] == concepts]
        df = df.rename(columns=col_trans)
        return df

    def _iterate_api(
            self,
            groups,
            type_analysis,
            extractor_name,
            bounds={"north": 90, "east": 180, "west": -179, "south": -89},
            from_date="1900-01-01",
            to_date="9999-12-31",
            _page_length=10,
            **kwargs #extra args for make_query such as begin and end time

    ):
        """
        Iterates to df and makes calls <-- update 
        
        :param groups: Filter on the group 
        :param type_analysis: 
        """
        output_data = []
        extra_request = True
        first_iter = True
        page_nbr = 0
        extr = dataExtractor(extractor_name)
        # fix timestamp!!
        while extra_request: #while loop so first call can directly be used
            query = make_query(bounds=bounds,
                               date_to=to_date,
                               date_from=from_date,
                               type_analysis=type_analysis,
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
            cleaner = dataCleaner(data)
            output_data.extend(cleaner.get_list_dict())
            if page_nbr == nbr_pages:
                break
            page_nbr += 1
        return dataCleaner(output_data).list_to_pd()

    def add_geojson_to_track(self, metadata_input: pd.DataFrame) -> pd.DataFrame:
        """
        Takes track metadata and adds geojson to it

        :param track_metadata: the output of the track_extractor function 
        :return: Df containing the tracks with the geojson
        """
        import copy
        track_metadata = copy.deepcopy(metadata_input) #make shallow copy from old dataframe
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

    def layer_feature_extractor(self,
                                project_id: int,
                                layer_id: int):
        """Extract details for a specific layer"""

        url_addition = f"map/all/{project_id}/{layer_id}/features/"

        r = self._api_call("get", url_addition)
        output = r.json()

        # TODO
        # extractor = dataExtractor("layer_features")
        pass
