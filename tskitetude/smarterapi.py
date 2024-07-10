
import logging
import requests

from urllib.parse import urljoin

log_fmt = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
logging.basicConfig(level=logging.INFO, format=log_fmt)

# Get an instance of a logger
logger = logging.getLogger(__name__)

# global variables
SESSION = requests.Session()
BASE_URL = "https://webserver.ibba.cnr.it"

class EndPointMixin():
    url = None
    headers = {}

    def get(self, **kwargs):
        logger.debug(f"Getting data from {self.url}")
        logger.debug(f"Params: {kwargs}")

        # add page and size if not in kwargs
        if "page" not in kwargs:
            kwargs["page"] = 1

        if "size" not in kwargs:
            kwargs["size"] = 100

        response = SESSION.get(
            self.url,
            headers=self.headers,
            params=kwargs
        )

        if response.status_code == 200:
            return response.json()
        else:
            raise Exception(f"Failed to get data from {self.url}: {response.text}")


class SheepEndpoint(EndPointMixin):
    url = urljoin(BASE_URL, "smarter-api/samples/sheep")

    def get_samples(
            self,
            _type: str = None,
            breed: str = None,
            code: str = None,
            chip_name: str = None,
            **kwargs) -> dict:
        """Get the samples from the Sheep SMARTER API."""

        return self.get(
            type=_type,
            breed=breed,
            breed_code=code,
            chip_name=chip_name,
            **kwargs
        )


class BreedEndpoint(EndPointMixin):
    url = urljoin(BASE_URL, "smarter-api/breeds")

    def get_breeds(
            self,
            species: str = None,
            **kwargs) -> dict:
        """Get the breeds from the Sheep SMARTER API."""

        return self.get(
            species=species,
            **kwargs
        )


class ChipEndpoint(EndPointMixin):
    url = urljoin(BASE_URL, "smarter-api/supported-chips")

    def get_chips(
            self,
            species: str = None,
            manufacturer: str = None,
            **kwargs) -> dict:
        """Get the chips from the Sheep SMARTER API."""

        return self.get(
            species=species,
            manufacturer=manufacturer,
            **kwargs
        )


class VariantsEndpoint(EndPointMixin):
    def __init__(self, species, assembly) -> None:
        super().__init__()

        self.url = urljoin(
            BASE_URL,
            f"smarter-api/variants/{species.lower()}/{assembly.upper()}"
        )

    def get_variants(
            self,
            chip_name: str = None,
            region: str = None,
            **kwargs) -> dict:
        """Get the variants from the Variant SMARTER API."""

        response = self.get(
            chip_name=chip_name,
            region=region,
            **kwargs
        )

        # unnesting locations items: get first item
        for item in response["items"]:
            item["locations"] = item["locations"][0]

        return response
