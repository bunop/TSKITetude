
import logging
import requests

log_fmt = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
logging.basicConfig(level=logging.INFO, format=log_fmt)

# Get an instance of a logger
logger = logging.getLogger(__name__)

# global variables
session = requests.Session()


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

        response = session.get(
            self.url,
            headers=self.headers,
            params=kwargs
        )

        if response.status_code == 200:
            return response.json()
        else:
            raise Exception(f"Failed to get data from {self.url}: {response.text}")


class SheepEndpoint(EndPointMixin):
    url = "https://webserver.ibba.cnr.it/smarter-api/samples/sheep"

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
    url = "https://webserver.ibba.cnr.it/smarter-api/breeds"

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
    url = "https://webserver.ibba.cnr.it/smarter-api/supported-chips"

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
