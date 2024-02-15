
from plinkio import plinkfile

# TODO: remove this?
def search_samples(samples: list[tuple], plink: plinkfile.PlinkFile):
    """
    Search for samples in a plink file a dictionary of sample ids and their
    index in the plink file.
    """
    sample_ids = [sample[1] for sample in samples]
    samples_idx = {}

    for idx, sample in enumerate(plink.get_samples()):
        if sample.iid in sample_ids:
            samples_idx[idx] = sample.iid

    return samples_idx
