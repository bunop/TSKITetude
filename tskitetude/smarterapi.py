
import logging
import requests
from requests.models import PreparedRequest

import asyncio
import aiohttp
from urllib.parse import urljoin

# Get an instance of a logger
logger = logging.getLogger(__name__)

# global variables
SESSION = requests.Session()
BASE_URL = "https://webserver.ibba.cnr.it"
SIZE = 100


class Location():
    _data = {}
    name = None
    chrom = None
    position = None

    illumina_top = None
    illumina_forward = None

    def __init__(self, name: str = None, data = {}):
        self.name = name

        if data:
            self._data = data
            self.read_data(data)

    def __str__(self):
        return (
            f"{self.name}: {self.chrom}:{self.position} [{self.illumina_top}]"
        )

    def read_data(self, data):
        # read some attributes for simplicity
        self.chrom = data.get("chrom")
        self.position = data.get("position")
        self.illumina_forward = data.get("illumina_forward")
        self.illumina_top = data.get("illumina_top")

    def to_update_alleles(self):
        old_code = self.illumina_top.split("/")
        new_code = self.illumina_forward.split("/")

        return [self.name, old_code[0], old_code[1], new_code[0], new_code[1]]


class EndPointMixin():
    url = None
    headers = {}

    def _update_kwargs(self, kwargs):
        # add page and size if not in kwargs
        if "page" not in kwargs:
            kwargs["page"] = 1

        if "size" not in kwargs:
            kwargs["size"] = SIZE

        return kwargs

    def get(self, **kwargs):
        logger.debug(f"Getting data from {self.url}")
        logger.debug(f"Params: {kwargs}")

        # check for page and size
        kwargs = self._update_kwargs(kwargs)

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

        logger.info(f"Initialized VariantsEndpoint with URL: {self.url}")

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

        # un-nesting locations items: get first item
        for item in response["items"]:
            item["locations"] = item["locations"][0]

        return response

    async def get_async_variants(
            self, session, retries=5, backoff_factor=5, **kwargs) -> dict:
        """
        Fetches async variants from the specified URL.

        Args:
            session (aiohttp.ClientSession): The aiohttp client session.
            retries (int, optional): The number of retries in case of errors. Defaults to 5.
            backoff_factor (int, optional): The backoff factor for retrying. Defaults to 5.
            kwargs (dict): The query parameters to pass to

        Returns:
            dict: The fetched data as a dictionary.

        Raises:
            aiohttp.ClientError: If there is an error with the aiohttp client.
            asyncio.exceptions.TimeoutError: If the request times out.
            Exception: If the data cannot be fetched after the specified number of retries.
        """

        # test for page and size in kwargs
        kwargs = self._update_kwargs(kwargs)

        for attempt in range(retries):
            try:
                req = PreparedRequest()
                req.prepare_url(self.url, kwargs)

                logger.debug(f"Getting data from {req.url}")

                async with session.get(self.url, params=kwargs) as response:
                    response.raise_for_status()
                    result = await response.json()
                    logger.info(
                        f"Successfully fetched data for page {kwargs['page']}")

                    # un-nesting locations items: get first item
                    for item in result["items"]:
                        item["locations"] = item["locations"][0]

                    return result

            except (aiohttp.ClientError, asyncio.exceptions.TimeoutError) as exc:
                if attempt < retries - 1:
                    wait_time = backoff_factor * (2 ** attempt)
                    logger.warning(f"Error {exc}, retrying in {wait_time} seconds...")
                    await asyncio.sleep(wait_time)
                else:
                    logger.error(
                        f"Failed to fetch data for page {kwargs['page']} "
                        f"after {retries} attempts")
                    raise exc


async def variant_worker(
        queue, session, variant_api, async_processing_func, size, **kwargs):
    while True:
        page = await queue.get()

        try:
            response = await variant_api.get_async_variants(
                session, page=page, size=size, **kwargs)

            # call my processing function
            await async_processing_func(response)

            logger.debug(
                f"Got {len(response['items'])} results for page {page}")

        finally:
            queue.task_done()
