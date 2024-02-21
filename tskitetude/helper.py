
import csv
import collections

import tsinfer


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


def add_populations(csv_file: str, samples: tsinfer.SampleData) -> dict:
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
        csv_file: str, pop_lookup: dict, samples: tsinfer.SampleData) -> None:
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


def get_ancestors_alleles(csv_file: str) -> dict:
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
