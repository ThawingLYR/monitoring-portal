# Imports
import requests

from src.auth.tilsig import get_bearer_token as get_tilsig_bearer_token

#########################
### Instrument status ###
#########################


def instrument_status_Tilsig(sources_tilsig):

    access_token = get_tilsig_bearer_token()

    ####################
    ### Data request ###
    ####################

    # Define headers
    headers = {"accept": "application/json", "Authorization": "Bearer " + access_token}

    # Define the Tilsig endpoint and parameters
    endpoint = "https://api.tilsig.com/v1/device/all"
    parameters = {
        "sensors": "true",
        "station": "true",
    }

    # Issue an HTTP GET request
    response = requests.get(endpoint, parameters, headers=headers)
    status = response.json()

    return status
