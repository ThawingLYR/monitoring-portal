import os
import streamlit as st
from loguru import logger


def get_secret(secret_name: str) -> str:
    """
    Retrieve a secret value from Streamlit's secrets management or environment variables.
    Logs an error if the secret does not exist.

    Args:
        secret_name (str): The name of the secret to retrieve.

    Returns:
        str: The value of the secret, or an empty string if not found.

    Raises:
        Logs an error if the secret is not found.
    """
    secret = os.getenv(secret_name)

    if secret is not None:
        logger.debug("Using environment variable for secret: {}", secret_name)
        return secret

    secret = st.secrets.get(secret_name)
    logger.debug("Using streamlet secrets for secret: {}", secret_name)

    if secret is None:
        logger.error(
            "Secret '{}' not found in environment variables or Streamlit secrets",
            secret_name,
        )
        return ""

    return secret
