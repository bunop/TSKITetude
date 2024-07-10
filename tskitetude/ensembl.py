
import csv
import logging
from urllib.parse import urljoin

import click
import pandas as pd
from tqdm import tqdm
from ensemblrest import EnsemblRest

from .smarterapi import VariantsEndpoint

log_fmt = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
logging.basicConfig(level=logging.INFO, format=log_fmt)

# Get an instance of a logger
logger = logging.getLogger(__name__)


class ComparaSheepSNP():
    species = "ovis_aries"
    params = [
        ('method', 'EPO'),
        ('species_set_group', 'mammals'),
        ('display_species_set', 'ovis_aries'),
        ('display_species_set', 'capra_hircus')
    ]
    chrom = None
    position = None
    last_response = None

    def __init__(self, base_url = "https://rest.ensembl.org"):
        logger.info(f"Using base URL: {base_url}")
        self.base_url = base_url
        self.ensembl = EnsemblRest(base_url=base_url)
        self.session = self.ensembl.session

    def get_ancestor(self, chrom, position):
        self.chrom = chrom
        self.position = position

        url = urljoin(
            self.base_url,
            f"alignment/region/{self.species}/{chrom}:{position}-{position}"
        )
        response = self.session.get(url, params=self.params)
        self.last_response = response

        if response.status_code != 200:
            try:
                data = response.json()
                logger.debug(
                    f"Failed to get data for {chrom}:{position}: "
                    f"{data['error']}")

            except Exception as e:
                logger.error(e)
                logger.error(f"Failed to get data from {url}: {response.text}")

            return None

        return self._parse_response(response.json())

    def _parse_response(self, response):
        if "error" in response:
            logger.warning(
                f"No data for variant '{self.chrom}:{self.position}'")
            return None

        if isinstance(response, list):
            return self._parse_list(response)

        else:
            raise ValueError(f"Unexpected response: {response}")

    def _parse_list(self, response):
        if len(response) != 1:
            message = f"Multiple data for variant '{self.chrom}:{self.position}'"
            logger.error(message)
            raise ValueError(message)

        # get alignments
        alignments = response[0]["alignments"]

        ancestors = list(
            filter(
                lambda alignment: "ancestor" in alignment["seq_region"].lower(),
                alignments
            )
        )

        if len(ancestors) == 1:
            logger.debug(f"Found ancestor {ancestors[0]}")
            return ancestors[0]

        else:
            logger.debug(
                f"Cannot find ancestor for '{self.chrom}:{self.position}'")
            return None


@click.command()
@click.option(
    '--assembly',
    type=click.Choice(
        ['OAR3'],
        case_sensitive=False),
    required=True,
    help='Assembly version')
@click.option(
    '--chip_name',
    type=click.Choice(
        ['IlluminaOvineSNP50'],
        case_sensitive=False),
    help='Chip name')
@click.option(
    '--output',
    type=click.File('w'),
    help='Output file',
    required=True)
def collect_compara_ancestors(assembly, chip_name, output):
    compara_assemblies = {
        "OAR3": "https://nov2020.rest.ensembl.org"
    }

    logger.info(f"Using assembly: {assembly}")
    logger.info(f"Using ensembl REST URL: {compara_assemblies[assembly]}")
    ensRest = EnsemblRest(base_url=compara_assemblies[assembly])
    compara = ComparaSheepSNP(base_url=compara_assemblies[assembly])

    writer = csv.writer(output, delimiter=',', lineterminator="\n")
    writer.writerow(["chrom", "position", "alleles", "ancestor"])

    # get top level regions from ensembl endpoint
    data = ensRest.getInfoAssembly(species="ovis_aries")
    chromosomes = pd.DataFrame(list(
        filter(
            lambda record: record['coord_system'] == "chromosome",
            data["top_level_region"]
        )
    ))

    for _, chromosome in chromosomes.iterrows():
        logger.info(f"getting variants for chromosome {chromosome['name']}")

        variant_api = VariantsEndpoint(species="Sheep", assembly=assembly)
        data = variant_api.get_variants(
            chip_name=chip_name, region=chromosome['name'])
        page = data["page"]
        variants = pd.json_normalize(data["items"])

        if variants.shape[0] == 0:
            logger.warning(f"No variants found for chromosome {chromosome['name']}")
            continue

        # deal with pagination
        while data["next"] is not None:
            data = variant_api.get_variants(
                chip_name=chip_name, region=chromosome['name'], page=page+1)
            df_page = pd.json_normalize(data["items"])
            page = data["page"]
            variants = pd.concat([variants, df_page], ignore_index=True)

        # iterate over variants and collect data from ensembl
        for _, variant in tqdm(variants.iterrows(), total=variants.shape[0]):
            ancestor = compara.get_ancestor(
                chrom=variant["locations.chrom"],
                position=variant["locations.position"])

            if ancestor is not None:
                writer.writerow([
                    variant['locations.chrom'],
                    variant['locations.position'],
                    variant['locations.alleles'],
                    ancestor['seq']
                ])

            # end of variant loop

        # end of chromosome loop
        logger.info(f"Done with chromosome {chromosome['name']}")
