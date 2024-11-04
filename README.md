# WeatherAPI
A simple REST API built with FastAPI to manage sensor values of IOT devices and provide data for applications.

## Features
- The API allows to create multiple sensors and users.
- Users can be normal users or superusers with elevated permissions.
- A user (sensor) can create sensor data. The sensor data shall contain temperature, humidity, pressure and voltage.
- The read and write access to sensors and their data is protected. With SensorPermissions you can allow a user to read and / or write data for a given sensor.
  - This allows permission control, so that devices providing data can only write data to specific sensors and applications or users can only read data from specific sensors.
- The API has endpoints to request a forecast for a given location.
- The API offers endpoints to request data from the Prepaid-Hoster REST API, to give information about the status of the server.

## Running the API
### Prerequisites
1. You must have **Python3.11** installed (not tested with other versions).
2. You will need a running instance of PostgreSQL. The API has been tested on version 16.4.

### Setup
1. Create and activate a venv:
2. Install all the needed requirements from the `requirements.txt` file.
    - In case you want to develop you will also need the `dev-requirements.txt` installed.
      - This includes test dependencies as well as black and isort.
3. Copy the file `SECRETS.example.py` and name it `SECRETS.py`
4. Set up a user and a database for the api and update the `PSQL_URL` string accordingly in the SECRETS file.
5. For requesting forecast data the api also accesses the [Openweathermap One Call API 3.0](https://openweathermap.org/api/one-call-3).
    - Create a token and update the `OPENWEATHERMAP_KEY` string in the SECRETS file.
6. For requesting stats about the server from my personal hoster (prepaid-hoster.de) I access data from their API.
    - For that you also need to add a valid API token and update the `SERVERSTATS_SETTINGS` dict accordingly.
7. To create the initial user in the database without manually writing to the database, there is a filed called `cli_create_user.py`.
   - With `python cli_create_user.py --username <username> --password <password> [--superuser]` you can create a new user with the given name and password.

### Running
- To run the api use the following command: `uvicorn api.main:app --reload`
- on `localhost:8000/docs` you will get detailed documentation over all endpoints.