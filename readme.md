### Part 1: Install

Command to make new wheel file
```python
python3 setup.py bdist_wheel 
```
How to pip install the github repo 
- Get a personal acces token
  - Upper right corner of git click on picture
  - Go to settings
  - Developer settings
  - Personal access token
  - Generate new token
  - read access
```python
!python3 -m pip install git+https://<personal_access_token>@github.com/SensingClues/wildcat-api-python.git@main
```



## Part 2: Run code (see demo_notebook.ipynb)

#### 2.1: Login
Make a variable that calls the WildcatApi with your username and password. 
This variable can be used in the next calls
```python
api_call = WildcatApi(username,password)
```
#### 2.1: Get groups
Get the variable from the login and extent it with the get_groups command. This gives
you the groups you can see
```python
info = api_call.get_groups()
```
#### 2.2: Get groups
Get the variable from the login and extent it with the observation_extractor command. 
You have to provide a group as argument. This delivers a pandas dataframe with observations

Possible arguments: 

```python
observations = api_call.observation_extractor(groups=groups)
```
