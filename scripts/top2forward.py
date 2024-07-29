#!/usr/bin/env python
# -*- coding: utf-8 -*-
# an attempt to collect variants from the SMARTER API variants endpoint and
# to convert from TOP to FORWARD using plink `--update-alleles` option

import csv
import sys
import logging
from urllib.parse import urljoin

import asyncio
import aiohttp

from tskitetude.smarterapi import BASE_URL

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


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


class VariantsEndpoint:
    def __init__(self, species, assembly):
        self.base_url = urljoin(
            BASE_URL,
            f"smarter-api/variants/{species.lower()}/{assembly.upper()}"
        )
        logger.info(f"Initialized VariantsEndpoint with URL: {self.base_url}")

    async def get_variants(self, session, page=1, size=25, retries=5, backoff_factor=5):
        url = f"{self.base_url}?page={page}&size={size}"
        for attempt in range(retries):
            try:
                async with session.get(url) as response:
                    response.raise_for_status()
                    logger.info(f"Successfully fetched data for page {page}")
                    return await response.json()

            except (aiohttp.ClientError, asyncio.exceptions.TimeoutError) as exc:
                if attempt < retries - 1:
                    wait_time = backoff_factor * (2 ** attempt)
                    logger.warning(f"Error {exc}, retrying in {wait_time} seconds...")
                    await asyncio.sleep(wait_time)
                else:
                    logger.error(f"Failed to fetch data for page {page} after {retries} attempts")
                    raise exc


async def worker(queue, session, variant_api, all_locations, lock, size):
    while True:
        page = await queue.get()
        try:
            response = await variant_api.get_variants(session, page=page, size=size)
            locations = []

            for item in response["items"]:
                location = Location(name=item["name"], data=item["locations"][0])
                locations.append(location)

            async with lock:
                all_locations += locations

            logger.debug(f"Got {len(locations)} results for page {page}")

        finally:
            queue.task_done()


async def fetch_all_locations(size=25):
    async with aiohttp.ClientSession() as session:
        variant_api = VariantsEndpoint(species="Sheep", assembly="OAR3")

        # collect the total number of pages
        response = await variant_api.get_variants(session, page=1, size=size)
        total_items = response["total"]
        total_pages = response["pages"]

        logger.info(f"Total items: {total_items}, Total pages: {total_pages}")

        # where location will be stored
        all_locations = []

        # process the first page
        for item in response["items"]:
            location = Location(name=item["name"], data=item["locations"][0])
            all_locations.append(location)

        # create queue and lock
        queue = asyncio.Queue()
        lock = asyncio.Lock()

        # Define the number of workers
        num_workers = 5
        tasks = []

        # create workers
        for i in range(num_workers):
            task = asyncio.create_task(
                worker(queue, session, variant_api, all_locations, lock, size),
                name=f"worker-{i}"
            )
            tasks.append(task)

        # Populate the queue with page numbers. Start with next page
        for page in range(2, total_pages + 1):
            await queue.put(page)

        # Wait until the queue is fully processed
        await queue.join()

        # Cancel all worker tasks
        for task in tasks:
            task.cancel()

        # Wait until all worker tasks are cancelled
        await asyncio.gather(*tasks, return_exceptions=True)

        assert len(all_locations) == total_items
        logger.info("All results have been fetched")

        return all_locations


async def main():
    all_locations = await fetch_all_locations(size=50)

    writer = csv.writer(sys.stdout, delimiter="\t", lineterminator="\n")

    for location in all_locations:
        writer.writerow(location.to_update_alleles())


# call the main function
if __name__ == "__main__":
    asyncio.run(main())
