# Imports
import streamlit as st
import requests

#########################
### Instrument status ###
#########################


def instrument_status_Tilsig(sources_tilsig):

    ######################
    ### Authentication ###
    ######################

    # Define the Where2O API endpoint and your credentials
    endpoint = "https://api.tilsig.com/v1/authentication/authenticate"
    username = st.secrets.tilsig_username
    password = st.secrets.tilsig_password

    # Define the data and headers for the token request
    user_data = {
        "username": username,
        "password": password,
    }

    headers = {
        "accept": "application/json",
        "Content-Type": "application/json",
    }

    # Send the token request
    response = requests.post(endpoint, json=user_data, headers=headers)

    # Check if request succeeded and retrieve token
    if response.status_code == 200:
        token_data = response.json()
        access_token = token_data["token"]
    else:
        print("Error! Returned status code %s" % response.status_code)

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
