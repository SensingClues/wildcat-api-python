#username = "jobvancreij"
#password =

import requests
import json
from wildcatpy.src.helper_functions import *
import pandas as pd
from wildcatpy.src.cleaner import dataExtractor

class WildcatApi:
    def __init__(self, user_name,password):
        """
        Autoamtically login when initiate class
        :param user_name: Username for focus
        :param password: Password for focus
        """
        self.session = requests.Session() #session object to share between calls
        self.login(user_name,password)

    def api_call(self,
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
        print(payload)
        r = request_trans[action](
                        url,
                        json=payload,
                        headers = {'Content-type': 'application/json'}
                       )

        # add extra status codes
        if r.status_code == 200: print(f"req to {url} success")
        elif r.status_code == 204: print(f"req to {url}, sucessfull logout") #only seen by logout
        elif r.status_code == 404: raise TypeError(f"unknown url {url}")
        elif r.status_code == 405: raise TypeError(f"Check post/get for url {url}")
        else: raise TypeError(f"Unknow error {str(r.status_code)}, {r.json()} ")
        return r


    def login(self,username,password):
        """
        Have to login before making requests
        :param username: Username for focus
        :param password: Passowrd for focus
        :return:
        """

        url_addition = "auth/login"
        payload = {
            'username': username,
            'password': password,
        }
        return self.api_call("post",url_addition, payload)

    def logout(self):
        url_addition = "auth/login"
        return self.api_call("post",url_addition, {})

    def get_groups(self):
        url_addition = "search/all/facets"
        payload = make_query(
            date_from= "1900-01-01",
            date_to= "9999-12-31",
            type_analysis = ["Observation", "track"],
            page_nbr=1,
            page_length=0
        )
        r = self.api_call("post",url_addition, payload)
        cleaner = dataExtractor(r.json())
        cleaner.data = cleaner.extract_with_extractor(cleaner.data,"groups_extractor")
        return cleaner.list_to_pd()

    def close_session(self):
        self.session.close()

    def track_extractor(self, groups, **kwargs):
        return self.general_api_test(groups,
                                     **kwargs,
                                     type_analysis=["track"],
                                     extractor_name="track_extractor",
                                     )

    def observation_extractor(self, groups, **kwargs):
        df = self.general_api_test(groups,
                                   **kwargs,
                                   type_analysis=["observation"],
                                   extractor_name="observation_extractor",
                                   )
        return df

    def general_api_test(
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
        output_data = []
        extra_request = True
        first_iter = True
        page_nbr = 0
        # fix timestamp!!
        while extra_request: #while loop so first call can directly be used
            query = make_query(bounds=bounds,
                               date_to=to_date,
                               date_from=from_date,
                               type_analysis=type_analysis,
                               groups=groups,
                               **kwargs)
            r = self.api_call("post", "search/all/results", query)
            if first_iter:
                nbr_pages = math.ceil(r.json()["total"] / _page_length)
                if nbr_pages == 0:
                    break
            cleaner = dataExtractor(r.json())
            cleaner.deeper_in_nested(["results"])
            cleaner.iterate_extractor(extractor_name)
            cleaner.flatten_data()
            output_data.extend(cleaner.get_list_dict())
            if page_nbr == nbr_pages:
                break
            page_nbr += 1
        return dataExtractor(output_data).list_to_pd()


