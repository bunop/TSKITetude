#!/usr/bin/env python
# -*- coding: utf-8 -*-
# an attempt to collect variants from the SMARTER API variants endpoint and
# to convert from TOP to FORWARD using plink `--update-alleles` option

import csv
import sys
import logging
from functools import partial

import asyncio
import aiohttp

from tskitetude.smarterapi import Location, VariantsEndpoint, variant_worker

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def process_response(response, all_locations):
    """Deal with the response from the API"""

    for item in response["items"]:
        location = Location(name=item["name"], data=item["locations"])
        all_locations.append(location)



async def fetch_all_locations(size=25):
    async with aiohttp.ClientSession() as session:
        variant_api = VariantsEndpoint(species="Sheep", assembly="OAR3")

        # collect the total number of pages
        response = await variant_api.get_async_variants(
            session, page=1, size=size)

        total_items = response["total"]
        total_pages = response["pages"]

        # debug
        # total_items = 1000
        # total_pages = int(1000 / size)

        logger.info(f"Total items: {total_items}, Total pages: {total_pages}")

        # where location will be stored
        all_locations = []

        # process the first page
        for item in response["items"]:
            location = Location(name=item["name"], data=item["locations"])
            all_locations.append(location)

        # create queue
        queue = asyncio.Queue()

        # Create the partial function with lock and all_locations
        process_response_with_lock = partial(process_response, all_locations=all_locations)

        # Define the number of workers
        num_workers = 5
        tasks = []

        # create workers
        for i in range(num_workers):
            task = asyncio.create_task(
                variant_worker(queue, session, variant_api, process_response_with_lock, size),
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
