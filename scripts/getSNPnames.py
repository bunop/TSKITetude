#!/usr/bin/env python
# -*- coding: utf-8 -*-
# collect SNP names from SMARTER API variants endpoint

import logging
import argparse
from functools import partial

import aiohttp
import asyncio

from tskitetude.smarterapi import VariantsEndpoint, variant_worker

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def process_response(response, all_names, lock):
    """Deal with the response from the API"""

    # collect names
    names = [item['name'] for item in response['items']]

    async with lock:
        all_names += names


async def fetch_all_names(chip_name, size):
    async with aiohttp.ClientSession() as session:
        variant_api = VariantsEndpoint(species="Sheep", assembly="OAR3")

        # collect the total number of pages
        response = await variant_api.get_async_variants(
            session, page=1, size=size, chip_name=chip_name)

        total_items = response["total"]
        total_pages = response["pages"]

        # debug
        # total_items = 1000
        # total_pages = int(1000 / size)

        logger.info(f"Total items: {total_items}, Total pages: {total_pages}")

        # process the first page
        all_names = [item['name'] for item in response['items']]

        # create queue and lock
        queue = asyncio.Queue()
        lock = asyncio.Lock()

        # Create the partial function with lock and all_names
        process_response_with_lock = partial(process_response, all_names=all_names, lock=lock)

        # Define the number of workers
        num_workers = 5
        tasks = []

        # create workers
        for i in range(num_workers):
            task = asyncio.create_task(
                variant_worker(
                    queue,
                    session,
                    variant_api,
                    process_response_with_lock,
                    size,
                    chip_name=chip_name),
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

        assert len(all_names) == total_items
        logger.info("All results have been fetched")

        return all_names


async def main(chip_name="IlluminaOvineSNP50", size=50):
    logger.info(f"Fetching SNP names for '{chip_name}'")

    all_names = await fetch_all_names(chip_name, size)

    for name in all_names:
        print(name)


# call the main function
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Fetch SNP names.")
    parser.add_argument("--size", type=int, default=50, help="Size of the pages to fetch")
    parser.add_argument("--chip_name", type=str, default="IlluminaOvineSNP50", help="Chip name")
    args = parser.parse_args()

    asyncio.run(main(chip_name=args.chip_name, size=args.size))
