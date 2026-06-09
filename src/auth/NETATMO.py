import requests
from loguru import logger
from pathlib import Path
import re

from src.auth.secrets import get_secret


def get_bearer_token():
    try:
        # Define the NETATMO API endpoint and credentials
        endpoint = "https://api.netatmo.com/oauth2/token"
        refresh_token = get_secret("netatmo_refresh_token")
        client_id = get_secret("netatmo_client_id")
        client_secret = get_secret("netatmo_client_secret")

        # Define the data and headers for the token request
        data = {
            "grant_type": "refresh_token",
            "refresh_token": refresh_token,
            "client_id": client_id,
            "client_secret": client_secret,
        }

        r = requests.post(endpoint, data=data)
        # Check if request succeeded and retrieve token
        if r.status_code == 200:
            token_data = r.json()
            access_token = token_data["access_token"]
        else:
            raise Exception(f"Authentication failed with status code {r.status_code}")

        # search upward from cwd for .streamlit/secrets.toml
        p = Path.cwd()
        for d in [p, *p.parents]:
            candidate = d / ".streamlit" / "secrets.toml"
            if candidate.exists():
                break
        if not candidate.exists():
            logger.error(
                f"Secrets file not found. Rewrite the new refresh token ({token_data['refresh_token']}) to the secrets file."
            )
        else:
            p = Path(candidate)

        # Save the new refresh token for future use
        secrets = p.read_text(encoding="utf-8").splitlines(keepends=True)
        new_secrets = re.sub(
            r"^.*netatmo_refresh_token.*$\n?",
            f"netatmo_refresh_token=\"{token_data['refresh_token']}\"\n",
            "".join(secrets),
            count=1,
            flags=re.M,
        )
        p.write_text(new_secrets, encoding="utf-8")

        return access_token

    except Exception as e:
        logger.error(f"Error during authentication: {e}")
        return None
