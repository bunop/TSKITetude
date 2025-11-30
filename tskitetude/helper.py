import io
import csv
import json
import logging
import datetime
import collections
from functools import partial
from typing import Dict, Tuple, List, Union

import click
import cyvcf2
import tsdate
import tsinfer
import tszip
import numpy as np
from click_option_group import optgroup, RequiredMutuallyExclusiveOptionGroup
from tskit import MISSING_DATA
from tqdm import tqdm

from tskitetude import POPULATION_METADATA_SCHEMA, INDIVIDUAL_METADATA_SCHEMA

log_fmt = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
logging.basicConfig(level=logging.INFO, format=log_fmt)

# Get an instance of a logger
logger = logging.getLogger(__name__)

# set tsinfer logging to INFO
tsinfer_log = logging.getLogger("tsinfer")
tsinfer_log.setLevel(logging.INFO)

# some constants
TSDATE_DEFAULT_NE = 1e4


class TqdmToLogger(io.StringIO):
    """
    Output stream for TQDM which will output to logger module instead of
    the StdOut.
    """

    logger = None
    level = None
    buf = ""

    def __init__(self, logger, level=None):
        super(TqdmToLogger, self).__init__()
        self.logger = logger
        self.level = level or logging.INFO

    def write(self, buf):
        self.buf = buf.strip("\r\n\t ")

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
            pop_lookup[breed] = samples.add_population(metadata={"breed": breed})

    return pop_lookup


def add_diploid_individuals(
    csv_file: str, pop_lookup: Dict[str, int], samples: tsinfer.SampleData
) -> Dict[str, Tuple[int, List[int]]]:
    """
    Try to add diploid samples. Returns a dictionary mapping sample_id to
    (individual_id, [sample_indices]).
    """

    # track added individuals
    indv_lookup = {}

    for breed, sample_id in open_csv(csv_file):
        population = pop_lookup[breed]
        indv_lookup[sample_id] = samples.add_individual(
            ploidy=2, metadata={"sample_id": sample_id}, population=population
        )

    return indv_lookup


def get_ancestors_alleles(
    csv_file: str, ancestral_method: str = "estsfs"
) -> Dict[Tuple[str, int], Union[int, str]]:
    """
    read tskit-pipeline ancestor file an returns a dictionary
    """

    reader = open_csv(csv_file)
    header = next(reader)

    ResultRecord = collections.namedtuple("ResultRecord", header)

    ancestors = {}

    for record in (ResultRecord(*line) for line in reader):
        if ancestral_method == "estsfs":
            ancestors[(record.chrom, int(record.position))] = int(record.anc_allele)
        else:
            # return anc_allele as string
            ancestors[(record.chrom, int(record.position))] = record.anc_allele

    return ancestors


def get_chromosome_lengths(vcf: cyvcf2.VCF) -> Dict[str, int]:
    results = {}
    for seqname, seqlen in zip(vcf.seqnames, vcf.seqlens):
        results[seqname] = seqlen

    return results


def get_major_allele(variant: cyvcf2.Variant) -> int:
    """
    Get the index of the major allele from a variant. Returns 0
    (reference allele) in case of a tie.
    """

    alleles = [variant.REF] + variant.ALT
    counts = [0] * len(alleles)

    for g in variant.genotypes:
        for a in g[0:2]:
            counts[a] += 1

    major_idx = counts.index(max(counts))

    logger.debug(f"Got {alleles[major_idx]} as major allele")

    return major_idx


def add_diploid_sites(
    vcf: cyvcf2.VCF,
    samples: tsinfer.Sample,
    ancestors_alleles: Dict[Tuple[str, int], int],
    indv_lookup: Dict[str, int],
    allele_chars=set("ATCG*"),
    ancestral_method="estsfs",
):
    """
    Read the sites in the vcf and add them to the samples object.
    """

    # logging which method we are using
    if ancestral_method in ["reference", "major"]:
        logger.info(f"Using {ancestral_method} allele as ancestral allele")

    elif ancestral_method == "estsfs":
        logger.info("Using ancestral allele from est-sfs")

    elif ancestral_method == "ensembl":
        logger.info("Using ancestral allele from ensembl-compara")

    else:
        raise NotImplementedError("Ancestral method not implemented")

    # allele_chars is now passed as argument

    # reset position
    pos = 0

    # deal with logging an progress bar
    tqdm_out = TqdmToLogger(logger, level=logging.INFO)
    progressbar = tqdm(
        total=samples.sequence_length,
        mininterval=1,
        desc="Read VCF",
        unit="bp",
        file=tqdm_out,
    )

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

        if ancestral_method == "reference":
            # set ancestral allele to the first allele
            ancestral_allele = 0

        elif ancestral_method == "major":
            # get the major allele index
            ancestral_allele = get_major_allele(variant)

        elif ancestral_method == "estsfs":
            # get the ancestral allele from the dictionary (which is a number)
            ancestral_allele = ancestors_alleles.get(
                (variant.CHROM, variant.POS), MISSING_DATA
            )

        elif ancestral_method == "ensembl":
            # get the ancestral allele from the dictionary (which is a string)
            ancestral_allele = ancestors_alleles.get(
                (variant.CHROM, variant.POS), MISSING_DATA
            )

            # find the index of the ancestral allele in the alleles list
            if ancestral_allele != MISSING_DATA and ancestral_allele in alleles:
                ancestral_allele = alleles.index(ancestral_allele)

            else:
                ancestral_allele = MISSING_DATA

        else:
            raise NotImplementedError(
                f"Ancestral method {ancestral_method} not implemented"
            )

        logger.debug(
            f"Adding site at pos {pos} with alleles {alleles} "
            f"(ancestral allele {ancestral_allele})"
        )

        # Check we have ATCG alleles
        for a in alleles:
            if a not in allele_chars:
                print(f"Ignoring site at pos {pos}: allele {a} not in {allele_chars}")
                continue

        # Get genotypes from VCF and reorder them to match the order of individuals in samples
        # VCF.samples gives us the order of samples in the VCF file
        # We need to reorder genotypes to match the order individuals were added to samples
        vcf_genotypes = [g for row in variant.genotypes for g in row[0:2]]

        # Create a mapping from VCF sample order to the individual order in samples
        # vcf.samples gives the VCF order, indv_lookup maps sample_id to individual_id
        # We need to create an index mapping: vcf_index -> samples_index
        vcf_sample_order = vcf.samples

        # Create reordered genotypes array
        # For each individual in the order they were added to samples,
        # find their position in the VCF and extract their genotypes
        genotypes = []
        sample_id_to_vcf_idx = {
            sample_id: idx for idx, sample_id in enumerate(vcf_sample_order)
        }

        # Sort individuals by their individual_id to get them in insertion order
        sorted_samples = sorted(indv_lookup.items(), key=lambda x: x[1])

        for sample_id, _ in sorted_samples:
            if sample_id not in sample_id_to_vcf_idx:
                raise ValueError(
                    f"Sample {sample_id} found in CSV but not in VCF. "
                    f"VCF samples: {vcf_sample_order}"
                )
            vcf_idx = sample_id_to_vcf_idx[sample_id]
            # Each individual is diploid, so genotypes are at positions [vcf_idx*2, vcf_idx*2+1]
            genotypes.extend(vcf_genotypes[vcf_idx * 2 : vcf_idx * 2 + 2])

        samples.add_site(pos, genotypes, alleles, ancestral_allele=ancestral_allele)


@click.command()
@click.option(
    "--vcf",
    "vcf_file",
    help="A VCF file with all samples (focal/ancient)",
    type=click.Path(exists=True),
    required=True,
)
@click.option(
    "--focal",
    "focal_csv",
    help="focal samples CSV file",
    type=click.Path(exists=True),
    required=True,
)
@optgroup.group(
    "Ancestral allele parameters",
    cls=RequiredMutuallyExclusiveOptionGroup,
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
    help="Use reference allele as ancestral allele",
    is_flag=True,
    default=False,
)
@optgroup.option(
    "--ancestral_as_major",
    help="Use major allele as ancestral allele",
    is_flag=True,
    default=False,
)
@click.option(
    "--output_samples",
    help="tsinfer.SampleData output file",
    type=click.Path(exists=False),
    required=True,
)
@click.option(
    "--output_trees",
    help="tstree output file",
    type=click.Path(exists=False),
    required=True,
)
@click.option(
    "--num_threads",
    help="number of threads with tsinfer",
    type=int,
    default=1,
    show_default=True,
)
@click.option(
    "--tsdate_method",
    type=click.Choice(
        ["inside_outside", "variational_gamma", "maximization"], case_sensitive=False
    ),
    default="variational_gamma",
    show_default=True,
    help=(
        "the continuous-time variational_gamma approach is the most accurate. "
        "The discrete-time inside_outside approach is slightly less accurate, "
        "especially for older times, but is slightly more numerically robust "
        "and also allows each node to have an arbitrary (discretised) probability "
        "distribution. The discrete-time maximization approach is always stable "
        "but is the least accurate."
    ),
)
@click.option(
    "--mutation_rate",
    help="tsdate mutation rate",
    type=float,
    default=1e-8,
    show_default=True,
)
@click.option(
    "--recombination_rate",
    help="tsinfer/tsdate recombination rate",
    type=float,
    default=None,
    show_default=True,
)
@click.option(
    "--ne",
    "Ne",
    help=(
        "tsdate effective population size: affect only 'inside_outside' and "
        "'maximization' tsdate_method parameter"
    ),
    type=float,
    default=TSDATE_DEFAULT_NE,
    show_default=True,
)
def create_tstree(
    vcf_file: click.Path,
    focal_csv: click.Path,
    ancestral_estsfs: click.Path,
    ancestral_ensembl: click.Path,
    ancestral_as_reference: bool,
    ancestral_as_major: bool,
    output_samples: click.Path,
    output_trees: click.Path,
    num_threads: int,
    tsdate_method: click.Choice,
    mutation_rate: float,
    recombination_rate: float,
    Ne: float,
):
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
        f"Getting information for chromosome {chrom} with length {sequence_length} bp"
    )

    # reset the vcf
    vcf = cyvcf2.VCF(vcf_file)

    # this simply debug true/false relying on method selected
    logging.debug("ancestral_as_reference: %s", ancestral_as_reference)
    logging.debug("ancestral_as_major: %s", ancestral_as_major)
    logging.debug("ancestral_estsfs: %s", ancestral_estsfs)
    logging.debug("ancestral_ensembl: %s", ancestral_ensembl)

    # time to get the ancestor allele dictionary
    if ancestral_as_reference:
        ancestors_alleles = {}
        ancestral_method = "reference"

    elif ancestral_as_major:
        ancestors_alleles = {}
        ancestral_method = "major"

    elif ancestral_estsfs:
        ancestral_method = "estsfs"
        ancestors_alleles = get_ancestors_alleles(ancestral_estsfs, ancestral_method)

    elif ancestral_ensembl:
        ancestral_method = "ensembl"
        ancestors_alleles = get_ancestors_alleles(ancestral_ensembl, ancestral_method)

    else:
        raise NotImplementedError("Ancestral method not implemented")

    with tsinfer.SampleData(
        path=output_samples, sequence_length=sequence_length
    ) as samples:
        pop_lookup = add_populations(focal_csv, samples)
        indv_lookup = add_diploid_individuals(focal_csv, pop_lookup, samples)
        add_diploid_sites(
            vcf,
            samples,
            ancestors_alleles,
            indv_lookup,
            ancestral_method=ancestral_method,
        )

    logger.info(
        f"Sample file created for {samples.num_samples} samples "
        f"({samples.num_individuals} individuals) "
        f"with {samples.num_sites} variable sites."
    )

    # Do the inference
    sparrow_ts = tsinfer.infer(
        samples, num_threads=num_threads, recombination_rate=recombination_rate
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
        individual = json.loads(ts.individual(individual_id).metadata)["sample_id"]

        population_id = ts.node(sample_node_id).population
        population = json.loads(ts.population(population_id).metadata)["breed"]

        logger.debug(
            f"Node {sample_node_id} "
            f"labels a chr {chrom} sampled from individual "
            f"'{individual}' in population '{population}'"
        )

    # Removes unary nodes (currently required in tsdate), keeps historical-only sites
    inferred_ts = tsdate.preprocess_ts(ts, filter_sites=False)

    logger.info(f"Inferring dates using {tsdate_method} method")

    # warn if a user has specified a value for Ne
    if Ne != TSDATE_DEFAULT_NE and tsdate_method == "variational_gamma":
        logger.warning(
            "You have specified a custom value for Ne, "
            "but it will ignored by the 'variational_gamma' method."
        )

    # Prepare the base tsdate call with common parameters
    date_partial = partial(
        tsdate.date,
        inferred_ts,
        method=tsdate_method,
        mutation_rate=mutation_rate,
        recombination_rate=recombination_rate,
    )

    # Add Ne parameter only for methods that support it
    if tsdate_method in ("inside_outside", "maximization"):
        dated_ts = date_partial(Ne=Ne)
    elif tsdate_method == "variational_gamma":
        dated_ts = date_partial()
    else:
        raise NotImplementedError(f"Dating method '{tsdate_method}' not implemented")

    # save generated tree
    dated_ts.dump(output_trees)

    # take note of the time
    logger.info("Dated Tree Sequence saved to %s", output_trees)
    logger.info("Done!")


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


@click.command()
@click.option(
    "--input_tsz",
    help="Input tree sequence file",
    type=click.Path(exists=True),
    required=True,
)
@click.option(
    "--input_vcf",
    help="Input VCF file with sample metadata",
    type=click.Path(exists=True),
    required=True,
)
@click.option(
    "--sample_file",
    help="File with sample ID and breed information",
    type=click.Path(exists=True),
    required=True,
)
@click.option(
    "--output_tsz",
    help="Output annotated tree sequence file",
    type=click.Path(exists=False),
    required=True,
)
@click.option(
    "--software_name",
    help="Software name for provenance record",
    type=str,
    required=True,
)
@click.option(
    "--software_version",
    help="Software version for provenance record",
    type=str,
    required=True,
)
def annotate_tree(
    input_tsz: click.Path,
    input_vcf: click.Path,
    sample_file: click.Path,
    output_tsz: click.Path,
    software_name: str,
    software_version: str,
):
    """
    Annotate tree sequence with sample metadata.
    """

    # Read sample metadata from the provided file
    with open(sample_file, "r") as f:
        sample_info = []

        for line in f:
            if line.strip():
                breed, sample_id = line.strip().split()
                sample_info.append((sample_id, breed))

    logger.info(f"Loaded metadata for {len(sample_info)} samples.")

    # open vcf and get sample names
    vcf = cyvcf2.VCF(input_vcf)
    vcf_sample_order = vcf.samples

    # now order sample_info according to VCF sample order
    try:
        sample_info = sorted(sample_info, key=lambda x: vcf_sample_order.index(x[0]))

    except ValueError:
        logger.critical(
            "Sample information doesn't match samples used in tree sequence. "
            f"Please check that all samples in {sample_file} are present in {input_vcf}"
        )
        raise

    # Load the input tree sequence
    input_tsz = tszip.load(input_tsz)

    # create a copy of the table that can be modified
    tables = input_tsz.dump_tables()

    # now I need to determine how many distinct populations (breeds) there are
    breeds = set(breed for _, breed in sample_info)

    # apply population metadata
    tables.populations.metadata_schema = POPULATION_METADATA_SCHEMA

    breed_to_id = {}

    for breed in breeds:
        metadata = {"breed": breed}
        pop_id = tables.populations.add_row(metadata=metadata)
        breed_to_id[breed] = pop_id

    # apply individual metadata and set population
    tables.individuals.metadata_schema = INDIVIDUAL_METADATA_SCHEMA

    individual_to_id = {}

    for sample_id, _ in sample_info:
        if "sample_id" not in individual_to_id:
            metadata = {"sample_id": sample_id}
            ind_id = tables.individuals.add_row(metadata=metadata)
            individual_to_id[sample_id] = ind_id

    # now set the population for each individual
    # we are talking about diploid individuals here
    for i, (sample_id, breed) in enumerate(sample_info):
        pop_id = breed_to_id[breed]
        ind_id = individual_to_id[sample_id]

        # update both nodes for the diploid individual
        for j in range(2):
            node_id = i * 2 + j
            node = tables.nodes[node_id]

            # Replace the node with an updated one
            tables.nodes[node_id] = node.replace(population=pop_id, individual=ind_id)

    # Create provenance record
    provenance_record = {
        "software": {"name": software_name, "version": software_version},
        "parameters": {
            "input_file": str(input_vcf),
            "metadata_added": True,
            "populations_added": len(breed_to_id),
            "individuals_added": len(individual_to_id),
        },
        "timestamp": datetime.datetime.now().isoformat(),
        "description": "TreeSequence generated with threads and metadata added for populations and individuals",
    }

    # Add provenance to tables
    tables.provenances.add_row(
        timestamp=provenance_record["timestamp"], record=json.dumps(provenance_record)
    )

    # write a tsz file as output
    annotated_ts = tables.tree_sequence()

    logger.info(f"Num of populations: {annotated_ts.num_populations}")
    logger.info(f"Num of individuals: {annotated_ts.num_individuals}")
    logger.info(f"Num of nodes: {annotated_ts.num_nodes}")

    tszip.compress(annotated_ts, output_tsz)

    logger.info(f"Annotated tree sequence saved to {output_tsz}")
    logger.info("Done!")
