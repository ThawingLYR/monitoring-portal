import os
from cryptography.fernet import Fernet
import json
from loguru import logger


class LocalSecretManager:
    """A class to manage secrets stored in a local file with encryption."""

    def __init__(self, secret_file: str = "./secrets/secrets.enc"):
        self.secret_file = secret_file
        if not os.path.exists(self.secret_file):
            logger.warning(
                "Secret file '%s' does not exist. Creating a empty one.",
                self.secret_file,
            )
            self.save_secrets({})
        self.key = os.getenv("local_store_secret_key")
        if not self.key:
            raise ValueError("Environment variable 'local_store_secret_key' not set.")

    def _encrypt_secrets(self, secrets: dict) -> bytes:
        """Encrypt a dictionary of secrets using the provided key."""
        fernet = Fernet(self.key.encode())
        return fernet.encrypt(json.dumps(secrets).encode())

    def _decrypt_secrets(self, encrypted_data: bytes) -> dict:
        """Decrypt the encrypted data using the provided key."""
        fernet = Fernet(self.key.encode())
        return json.loads(fernet.decrypt(encrypted_data).decode())

    def save_secrets(self, secrets: dict):
        """Encrypt and save secrets to a local file."""
        encrypted_data = self._encrypt_secrets(secrets)
        os.makedirs(os.path.dirname(self.secret_file), exist_ok=True)
        with open(self.secret_file, "wb") as f:
            f.write(encrypted_data)

    def load_secrets(self) -> dict:
        """Load and decrypt secrets from a local file."""
        if not os.path.exists(self.secret_file):
            logger.error("Secret file '%s' does not exist.", self.secret_file)
            return {}

        with open(self.secret_file, "rb") as f:
            encrypted_data = f.read()

        return self._decrypt_secrets(encrypted_data)

    def get_secret(self, key: str, default: str = "", create: bool = True) -> str:
        """Retrieve a specific secret by its key."""
        secrets = self.load_secrets()
        if create and key not in secrets:
            self.create_secret(key, default)
            secrets = self.load_secrets()
        return secrets.get(key, default)

    def update_secret(self, key: str, value: str):
        """Update a specific secret."""
        secrets = self.load_secrets()
        secrets[key] = value
        self.save_secrets(secrets)

    def create_secret(self, key: str, value: str):
        """Add a new secret."""
        secrets = self.load_secrets()
        if key in secrets:
            raise ValueError(f"Secret with key '{key}' already exists.")
        secrets[key] = value
        self.save_secrets(secrets)
