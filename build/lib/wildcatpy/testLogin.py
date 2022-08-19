#username = "jobvancreij"
#password =

import requests
import json




class WildcatApi:
    def __init__(self, user_name,password):
        self.session = requests.Session()
        self.login(user_name,password)

    def api_call(self,
                 action,
                 url_addition,
                 payload = {}):
        url = "https://focus.sensingclues.org/api/" + url_addition
        request_trans = {
            "post": self.session.post,
            "get": self.session.get
        }
        r = request_trans[action](
                        url,
                        json=payload,
                        headers = {'Content-type': 'application/json'}
                       )
        if r.status_code == 200: print(f"req to {url} success")
        elif r.status_code == 204: print(f"req to {url}, sucessfull logout")
        elif r.status_code == 404: raise TypeError(f"unknown url {url}")
        elif r.status_code == 405: raise TypeError(f"Check post/get for url {url}")
        else: raise TypeError(f"Unknow error {str(r.status_code)} ")
        return r


    def login(self,username,password):
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
        payload ={"filters":
                    {
                        "dateTimeRange":
                            {"to": "' + to + 'T24:00:00.000Z",
                             "from": "' + from + 'T00:00:00.000Z"
                             },
                        "entities": ["Observation", "track"]
                    },
                    "options": {
                        "start": 1,
                        "pageLength": 0
                    }
                }
        r = self.api_call("post",url_addition, payload)
        return r.json()

    def close_session(self):
        self.session.close()
#api_test = WildcatApi(username,password)
#output = api_test.get_groups()
#api_test.close_session()
#print(output)aa