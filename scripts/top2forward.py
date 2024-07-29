#!/usr/bin/env python
# -*- coding: utf-8 -*-
# an attempt to collect variants from the SMARTER API variants endpoint and
# to convert from TOP to FORWARD using plink `--update-alleles` option

import csv
import sys
from urllib.parse import urljoin

import asyncio
import aiohttp

from tskitetude.smarterapi import BASE_URL


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

    async def get_variants(self, session, page=1, size=100):
        url = f"{self.base_url}?page={page}&size={size}"
        async with session.get(url) as response:
            return await response.json()


async def fetch_all_locations():
    async with aiohttp.ClientSession() as session:
        variant_api = VariantsEndpoint(species="Sheep", assembly="OAR3")

        # collect the total number of pages
        size = 100
        first_response = await variant_api.get_variants(session, page=1, size=size)
        total_items = first_response["total"]
        total_pages = first_response["pages"]

        tasks = []
        for page in range(1, total_pages + 1):
            tasks.append(variant_api.get_variants(session, page=page, size=size))

        all_responses = await asyncio.gather(*tasks)

        all_locations = []

        for response in all_responses:
            for item in response["items"]:
                location = Location(name=item["name"], data=item["locations"][0])
                all_locations.append(location)

        assert len(all_locations) == total_items

        return all_locations


async def main():
    all_locations = await fetch_all_locations()

    writer = csv.writer(sys.stdout, delimiter="\t", lineterminator="\n")

    for location in all_locations:
        writer.writerow(location.to_update_alleles())

# call the main function
if __name__ == "__main__":
    asyncio.run(main())
