
import io
import re
import csv
import json
import logging
import collections
from typing import Dict, Tuple, List

import click
import cyvcf2
import tsdate
import tsinfer
import numpy as np
from click_option_group import (
    optgroup, RequiredMutuallyExclusiveOptionGroup)
from tskit import MISSING_DATA
from tqdm import tqdm

log_fmt = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
logging.basicConfig(level=logging.INFO, format=log_fmt)

# Get an instance of a logger
logger = logging.getLogger(__name__)

# set tsinfer logging to INFO
tsinfer_log = logging.getLogger("tsinfer")
tsinfer_log.setLevel(logging.INFO)


class TqdmToLogger(io.StringIO):
    """
        Output stream for TQDM which will output to logger module instead of
        the StdOut.
    """
    logger = None
    level = None
    buf = ''

    def __init__(self, logger, level=None):
        super(TqdmToLogger, self).__init__()
        self.logger = logger
        self.level = level or logging.INFO

    def write(self, buf):
        self.buf = buf.strip('\r\n\t ')

    def flush(self):
        self.logger.log(self.level, self.buf)


def open_csv(csv_file: str) -> csv.reader:
    """
    Open a csv file and return a csv.reader object
    """

    with open(csv_file) as handle:
        sniffer = csv.Sniffer()
        dialect = sniffer.sniff(handle.read(1024))
        handle.seek(0)
        reader = csv.reader(handle, dialect)

        for line in reader:
            yield line


def add_populations(csv_file: str, samples: tsinfer.SampleData) -> Dict[str, int]:
    """
    Attempt to define metadata like tsinfer tutorial
    """

    # add population to SampleData object and track reference
    pop_lookup = {}

    for breed, _ in open_csv(csv_file):
        if breed not in pop_lookup:
            pop_lookup[breed] = samples.add_population(
                metadata = {"breed": breed})

    return pop_lookup


def add_diploid_individuals(
        csv_file: str, pop_lookup: Dict[str, int],
        samples: tsinfer.SampleData) -> Dict[str, Tuple[int, List[int]]]:
    """
    Try to add diploid samples
    """

    # track added individuals
    indv_lookup = {}

    for breed, sample_id in open_csv(csv_file):
        population = pop_lookup[breed]
        indv_lookup[sample_id] = samples.add_individual(
            ploidy = 2,
            metadata={"sample_id": sample_id},
            population=population
        )

    return indv_lookup


def get_ancestors_estsfs(csv_file: str) -> Dict[Tuple[str, int], int]:
    """
    read tskit-pipeline ancestor file an returns a dictionary
    """

    reader = open_csv(csv_file)
    header = next(reader)

    ResultRecord = collections.namedtuple('ResultRecord', header)

    ancestors = {}

    for record in (ResultRecord(*line) for line in reader):
        ancestors[(record.chrom, int(record.pos))] = int(record.anc_allele)

    return ancestors


def get_chromosome_lengths(vcf: cyvcf2.VCF) -> Dict[str, int]:
    results = {}
    for seqname, seqlen in zip(vcf.seqnames, vcf.seqlens):
        results[seqname] = seqlen

    return results


def add_diploid_sites(
        vcf: cyvcf2.VCF,
        samples: tsinfer.Sample,
        ancestors_alleles: Dict[Tuple[str, int], int],
        allele_chars = set("ATCG*"),
        ancestral_as_reference = False,
        ancestral_method = "estsfs"
        ):
    """
    Read the sites in the vcf and add them to the samples object.
    """

    if ancestral_as_reference:
        logger.info("Using ancestral allele as reference allele")

    # allele_chars is now passed as argument

    # reset position
    pos = 0

    # deal with logging an progress bar
    tqdm_out = TqdmToLogger(logger, level=logging.INFO)
    progressbar = tqdm(
        total=samples.sequence_length,
        mininterval=1,
        desc="Read VCF",
        unit='bp',
        file=tqdm_out)

    # check chromosome we are working on
    chrom = None

    for variant in vcf:  # Loop over variants, each assumed at a unique site
        progressbar.update(variant.POS - pos)

        if not chrom:
            chrom = variant.CHROM

        else:
            if chrom != variant.CHROM:
                raise ValueError("VCF file contains multiple chromosomes")

        if pos == variant.POS:
            print(f"Duplicate entries at position {pos}, ignoring all but the first")
            continue

        else:
            pos = variant.POS

        if any([not phased for _, _, phased in variant.genotypes]):
            raise ValueError("Unphased genotypes for variant at position", pos)

        alleles = [variant.REF.upper()] + [v.upper() for v in variant.ALT]

        if ancestral_as_reference:
            # set ancestral allele to the first allele
            ancestral_allele = 0

        elif ancestral_method == "estsfs":
            # get the ancestral allele from the dictionary (which is a number)
            ancestral_allele = ancestors_alleles.get(
                (variant.CHROM, variant.POS), MISSING_DATA)
        else:
            raise NotImplementedError(
                f"Ancestral method {ancestral_method} not implemented")

        logger.debug(
            f"Adding site at pos {pos} with alleles {alleles} "
            f"(ancestral allele {ancestral_allele})"
        )

        # Check we have ATCG alleles
        for a in alleles:
            if a not in allele_chars:
                print(f"Ignoring site at pos {pos}: allele {a} not in {allele_chars}")
                continue

        # Map original allele indexes to their indexes in the new alleles list.
        genotypes = [g for row in variant.genotypes for g in row[0:2]]
        samples.add_site(pos, genotypes, alleles, ancestral_allele=ancestral_allele)


@click.command()
@click.option(
    "--vcf",
    "vcf_file",
    help="A VCF file with all samples (focal/ancient)",
    type=click.Path(exists=True),
    required=True
)
@click.option(
    "--focal",
    "focal_csv",
    help="focal samples CSV file",
    type=click.Path(exists=True),
    required=True
)
@optgroup.group(
    "Ancestral allele parameters",
    cls=RequiredMutuallyExclusiveOptionGroup
)
@optgroup.option(
    "--ancestral_estsfs",
    help="processed est-sfs ancient allele file",
    type=click.Path(exists=True),
)
@optgroup.option(
    "--ancestral_ensembl",
    help="processed ensembl-compara ancient allele file",
    type=click.Path(exists=True),
)
@optgroup.option(
    "--ancestral_as_reference",
    help="Use ancestral allele as reference allele",
    is_flag=True,
    default=False
)
@click.option(
    "--output_samples",
    help="tsinfer.SampleData output file",
    type=click.Path(exists=False),
    required=True
)
@click.option(
    "--output_trees",
    help="tstree output file",
    type=click.Path(exists=False),
    required=True
)
@click.option(
    "--num_threads",
    help="number of threads with tsinfer",
    type=int,
    default=1
)
@click.option(
    "--mutation_rate",
    help="tsdate mutation rate",
    type=float,
    default=1e-8
)
@click.option(
    "--ne",
    "Ne",
    help="tsdate effective population size",
    type=float,
    default=1e4
)
def create_tstree(
        vcf_file: click.Path, focal_csv: click.Path,
        ancestral_estsfs: click.Path, ancestral_ensembl: click.Path,
        ancestral_as_reference: bool,
        output_samples: click.Path, output_trees: click.Path, num_threads: int,
        mutation_rate: float, Ne: float):
    """
    Read data from phased VCF an try to create a tsinfer.Sample using ancestor
    alleles CSV file. One chromosome at a time.
    """

    vcf = cyvcf2.VCF(vcf_file)
    chromosome_lengths = get_chromosome_lengths(vcf)

    # get first variant to get the sequence length
    variant = next(vcf)
    chrom = variant.CHROM
    sequence_length = chromosome_lengths[chrom]

    logging.info(
        f"Getting information for chromosome {chrom} "
        f"with length {sequence_length} bp")

    # reset the vcf
    vcf = cyvcf2.VCF(vcf_file)

    # time to get the ancestor allele dictionary
    if ancestral_estsfs:
        ancestors_alleles = get_ancestors_estsfs(ancestral_estsfs)
        ancestral_method = "estsfs"

    elif ancestral_ensembl:
        ancestral_method = "ensembl"
        raise NotImplementedError("Ensembl ancestral allele not implemented")

    else:
        ancestors_alleles = {}

    with tsinfer.SampleData(
        path=output_samples,
        sequence_length=sequence_length) as samples:

        pop_lookup = add_populations(focal_csv, samples)
        add_diploid_individuals(focal_csv, pop_lookup, samples)
        add_diploid_sites(
            vcf,
            samples,
            ancestors_alleles,
            ancestral_as_reference=ancestral_as_reference,
            ancestral_method=ancestral_method
        )

    logger.info(
        f"Sample file created for {samples.num_samples} samples "
        f"({samples.num_individuals} individuals) "
        f"with {samples.num_sites} variable sites."
    )

    # Do the inference
    sparrow_ts = tsinfer.infer(
        samples,
        num_threads=num_threads
    )

    # Simplify the tree sequence
    ts = sparrow_ts.simplify()

    logger.info(
        f"Inferred tree sequence `ts`: {ts.num_trees} "
        f"trees over {ts.sequence_length / 1e6} Mb"
    )

    # Check the metadata
    for sample_node_id in ts.samples():
        individual_id = ts.node(sample_node_id).individual
        individual = json.loads(
            ts.individual(individual_id).metadata)["sample_id"]

        population_id = ts.node(sample_node_id).population
        population = json.loads(
            ts.population(population_id).metadata)["breed"]

        logger.debug(
            f"Node {sample_node_id} "
            f"labels a chr {chrom} sampled from individual "
            f"'{individual}' in population '{population}'"
        )

    # Removes unary nodes (currently required in tsdate), keeps historical-only sites
    inferred_ts = tsdate.preprocess_ts(ts, filter_sites=False)

    dated_ts = tsdate.date(
        inferred_ts,
        mutation_rate=mutation_rate,
        Ne=Ne
    )

    # save generated tree
    dated_ts.dump(output_trees)


def create_windows(ts):
    """
    Create windows for the diversity function
    """
    # create a numpy array with position
    sites = np.array([site.position for site in ts.sites()])

    # now duplicate each element and add an offset array
    windows = np.repeat(sites, 2) + np.tile([0, 1], len(sites))

    # add the first window
    windows = np.insert(windows, 0, 0)

    # now add sequence length as the last window
    windows = np.append(windows, ts.sequence_length)

    # remove duplicated items (adjacent SNPS)
    windows = np.unique(windows)

    return windows
