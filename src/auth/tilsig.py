import requests
from loguru import logger

from src.auth.secrets import get_secret


def get_bearer_token():
    try:
        # Define the Tilsig API endpoint and credentials
        endpoint = "https://api.tilsig.com/v1/authentication/authenticate"
        username = get_secret("tilsig_username")
        password = get_secret("tilsig_password")

        # Define the data and headers for the token request
        data = {
            "username": username,
            "password": password,
        }

        headers = {
            "accept": "application/json",
            "Content-Type": "application/json",
        }

        # Send the token request
        r = requests.post(endpoint, json=data, headers=headers)

        # Check if request succeeded and retrieve token
        if r.status_code == 200:
            token_data = r.json()
            access_token = token_data["token"]
        else:
            raise Exception(f"Authentication failed with status code {r.status_code}")

        return access_token

    except Exception as e:
        logger.error(f"Error during authentication: {e}")
        return None
