
import logging

from urllib.parse import urljoin
from ensemblrest import EnsemblRest

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
