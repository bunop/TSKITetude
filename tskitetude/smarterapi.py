
import requests

# global variables
session = requests.Session()


class SheepEndpoint():
    url = "https://webserver.ibba.cnr.it/smarter-api/samples/sheep"
    headers = {}

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
