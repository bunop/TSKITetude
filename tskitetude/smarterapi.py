
import requests

# global variables
session = requests.Session()


class SheepEndpoint():
    url = "https://webserver.ibba.cnr.it/smarter-api/samples/sheep"
    headers = {}

    def get_samples(
            self,
            _type: str = None,
            breed: str = None,
            code: str = None,
            page: int = None,
            size: int = 100) -> dict:
        """Get the samples from the Sheep SMARTER API."""
        response = session.get(
            self.url,
            headers=self.headers,
            params={
                "size": size,
                "page": page,
                "type": _type,
                "breed": breed,
                "breed_code": code
            }
        )

        if response.status_code == 200:
            return response.json()
        else:
            raise Exception("Failed to get sheep samples: " + response.text)


class BreedEndpoint():
    url = "https://webserver.ibba.cnr.it/smarter-api/breeds"
    headers = {}

    def get_breeds(
            self,
            species: str = None,
            page: int = None,
            size: int = 100) -> dict:
        """Get the breeds from the Sheep SMARTER API."""
        response = session.get(
            self.url,
            headers=self.headers,
            params={
                "size": size,
                "page": page,
                "species": species
            }
        )

        if response.status_code == 200:
            return response.json()
        else:
            raise Exception("Failed to get sheep breeds: " + response.text)
