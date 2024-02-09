
import csv
import tsinfer


def add_populations(csv_file: str, samples: tsinfer.SampleData) -> dict:
    """
    Attempt to define metadata like tsinfer tutorial
    """

    with open(csv_file) as handle:
        sniffer = csv.Sniffer()
        dialect = sniffer.sniff(handle.read(1024))
        handle.seek(0)
        reader = csv.reader(handle, dialect)

        # add population to SampleData object and track reference
        pop_lookup = {}

        for breed, _ in reader:
            if breed not in pop_lookup:
                pop_lookup[breed] = samples.add_population(
                    metadata = {"breed": breed})

    return pop_lookup


def add_diploid_individuals(
        csv_file: str, pop_lookup: dict, samples: tsinfer.SampleData) -> None:
    """
    Try to add diploid samples
    """

    with open(csv_file) as handle:
        sniffer = csv.Sniffer()
        dialect = sniffer.sniff(handle.read(1024))
        handle.seek(0)
        reader = csv.reader(handle, dialect)

        # track added individuals
        indv_lookup = {}

        for breed, sample_id in reader:
            population = pop_lookup[breed]
            indv_lookup[sample_id] = samples.add_individual(
                ploidy = 2,
                metadata={"sample_id": sample_id},
                population=population
            )

    return indv_lookup
