
import os
import json
import requests
import datetime

from pathlib import Path
from dotenv import load_dotenv

# global variables
session = requests.Session()


# a class to deal with authentication
class Auth():
    url = "https://webserver.ibba.cnr.it/smarter-api/auth/login"
    headers = {"Content-Type": "application/json"}
    token = None
    expires = None

    def __init__(self, env_file=None) -> None:
        """
        Authenticate to the SMARTER API.

        Args:
            env_file: (optional) Path to the environment file
                (def. "~/.Renviron")
        """
        global session

        if env_file is None:
            # use the same environment file as R does
            env_file = Path.home() / ".Renviron"

        # load the environment file
        load_dotenv(env_file)

        # check if the environment variables are set
        if (os.getenv("SMARTER_API_USERNAME") is None) or (
                os.getenv("SMARTER_API_PASSWORD") is None):
            raise Exception(
                "Environment variables SMARTER_API_USERNAME and "
                "SMARTER_API_PASSWORD are not set"
            )

        data = {
            "username": os.getenv("SMARTER_API_USERNAME"),
            "password": os.getenv("SMARTER_API_PASSWORD")
        }

        # authenticate to SMARTER API
        response = session.post(
            self.url, headers=self.headers, data=json.dumps(data))

        if response.status_code == 200:
            tmp = response.json()
            self.token = tmp["token"]
            self.expires = datetime.datetime.fromisoformat(tmp["expires"])

        else:
            raise Exception("Authentication failed: " + response.text)

    def is_expired(self) -> bool:
        """Check if the token is expired."""
        return datetime.datetime.now() > self.expires


class SheepEndpoint():
    url = "https://webserver.ibba.cnr.it/smarter-api/samples/sheep"
    headers = {}

    def __init__(self, auth: Auth) -> None:
        """Initialize the SamplesEndpoint class.

        Args:
            auth: An instance of the Auth class"""

        # check if the token is expired
        if auth.is_expired():
            raise Exception("Token is expired")

        # set the token
        self.headers["Authorization"] = "Bearer " + auth.token

    def get_samples(
            self,
            type: str = None,
            page: int = None,
            size: int = 100) -> dict:
        """Get the samples from the Sheep SMARTER API."""
        response = session.get(
            self.url,
            headers=self.headers,
            params={
                "size": size,
                "page": page,
                "type": type
            }
        )

        if response.status_code == 200:
            return response.json()
        else:
            raise Exception("Failed to get sheep samples: " + response.text)
