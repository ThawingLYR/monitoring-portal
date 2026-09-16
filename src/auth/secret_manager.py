"""
Local Secret Store Module

This module provides an encrypted, file-backed store for secrets that a provider
rotates at runtime and that therefore cannot live in the environment.

The motivating case is the Netatmo OAuth refresh token: Netatmo issues
single-use refresh tokens, so each authentication invalidates the token used and
returns a replacement. The replacement must be persisted, or the next
authentication fails permanently. Environment variables and Streamlit secrets are
read-only from the application's point of view, hence this store.

Credit:
    Contributed by PSelleunis (@PSelleunis) in
    https://github.com/ThawingLYR/monitoring-portal/pull/44, to support Netatmo's
    rotating refresh tokens.

Dependencies:
    - cryptography: For Fernet symmetric encryption of the secret file.
    - loguru: For logging.
    - src.auth.secrets: For retrieval of the encryption key itself.
"""

import json
import os

from cryptography.fernet import Fernet
from loguru import logger

from src.auth.secrets import get_secret


class LocalSecretManager:
    """Manages secrets stored in a local file, encrypted at rest with Fernet.

    The encryption key is read from the `local_store_secret_key` secret, which must
    be a url-safe base64-encoded 32-byte key as produced by `Fernet.generate_key()`.

    Attributes:
        secret_file (str): Path to the encrypted secret file.
        key (str): The Fernet key used to encrypt and decrypt the file.

    Note:
        In a containerised deployment the secret file must live on a writable
        volume that survives container recreation. If it does not, rotated
        credentials are lost and the provider can no longer be authenticated.
    """

    def __init__(self, secret_file: str = "./secrets/secrets.enc"):
        """Initializes the secret store, creating an empty file if necessary.

        Args:
            secret_file (str): Path to the encrypted secret file.

        Raises:
            ValueError: If `local_store_secret_key` is unset or is not a valid
                Fernet key.
        """
        self.secret_file = secret_file
        self.key = get_secret("local_store_secret_key")

        # Validate before touching the filesystem: creating the file first would
        # fail inside cryptography with an opaque error and mask the real cause.
        if not self.key:
            raise ValueError(
                "Secret 'local_store_secret_key' is not set. Generate one with "
                '`python -c "from cryptography.fernet import Fernet; '
                'print(Fernet.generate_key().decode())"` and set it as an '
                "environment variable or Streamlit secret."
            )
        try:
            Fernet(self.key.encode())
        except (ValueError, TypeError) as error:
            raise ValueError(
                "Secret 'local_store_secret_key' is not a valid Fernet key "
                f"({error}). It must be a url-safe base64-encoded 32-byte key, as "
                "produced by `Fernet.generate_key()`."
            ) from error

        if not os.path.exists(self.secret_file):
            logger.warning(
                "Secret file '{}' does not exist. Creating an empty one.",
                self.secret_file,
            )
            self.save_secrets({})

    def _encrypt_secrets(self, secrets: dict) -> bytes:
        """Encrypts a dictionary of secrets.

        Args:
            secrets (dict): The secrets to encrypt.

        Returns:
            bytes: The encrypted payload.
        """
        fernet = Fernet(self.key.encode())
        return fernet.encrypt(json.dumps(secrets).encode())

    def _decrypt_secrets(self, encrypted_data: bytes) -> dict:
        """Decrypts an encrypted payload.

        Args:
            encrypted_data (bytes): The payload to decrypt.

        Returns:
            dict: The decrypted secrets.
        """
        fernet = Fernet(self.key.encode())
        return json.loads(fernet.decrypt(encrypted_data).decode())

    def save_secrets(self, secrets: dict):
        """Encrypts secrets and writes them to the local file.

        Args:
            secrets (dict): The complete set of secrets to persist.
        """
        encrypted_data = self._encrypt_secrets(secrets)
        os.makedirs(os.path.dirname(self.secret_file), exist_ok=True)
        with open(self.secret_file, "wb") as f:
            f.write(encrypted_data)

    def load_secrets(self) -> dict:
        """Loads and decrypts the secrets from the local file.

        Returns:
            dict: The stored secrets, or an empty dict if the file is missing.
        """
        if not os.path.exists(self.secret_file):
            logger.error("Secret file '{}' does not exist.", self.secret_file)
            return {}

        with open(self.secret_file, "rb") as f:
            encrypted_data = f.read()

        return self._decrypt_secrets(encrypted_data)

    def get_encrypted_secret(
        self, key: str, default: str = "", create: bool = True
    ) -> str:
        """Retrieves a single secret by key.

        Args:
            key (str): Name of the secret.
            default (str): Value returned, and stored when `create` is True, if the
                secret is not present.
            create (bool): Whether to persist `default` when the secret is missing.

        Returns:
            str: The stored secret, or `default` if it is not present.
        """
        secrets = self.load_secrets()
        if create and key not in secrets:
            self.create_secret(key, default)
            secrets = self.load_secrets()
        return secrets.get(key, default)

    def update_secret(self, key: str, value: str):
        """Creates or overwrites a single secret.

        Args:
            key (str): Name of the secret.
            value (str): Value to store.
        """
        secrets = self.load_secrets()
        secrets[key] = value
        self.save_secrets(secrets)

    def create_secret(self, key: str, value: str):
        """Adds a secret that does not exist yet.

        Args:
            key (str): Name of the secret.
            value (str): Value to store.

        Raises:
            ValueError: If a secret with this key already exists.
        """
        secrets = self.load_secrets()
        if key in secrets:
            raise ValueError(f"Secret with key '{key}' already exists.")
        secrets[key] = value
        self.save_secrets(secrets)
