
from typing import List

import click
from plinkio import plinkfile

from .helper import open_csv
from .estsfs import search_samples


@click.command()
@click.option(
    "--plink",
    help="plink prefix file",
    type=str,
    required=True
)
@click.option(
    "--focal",
    help="focal samples CSV file",
    type=click.Path(exists=True),
    required=True
)
@click.option(
    "--outgroup",
    "outgroups",
    help="outgroup samples CSV file",
    multiple=True,
    type=click.Path(exists=True),
    required=True,
)
def make_est_sfs_input(
        plink: str, focal: click.Path, outgroups: List[click.Path]):

    # open plink file
    plink = plinkfile.PlinkFile(plink)

    # read focal samples
    focal_samples = list(open_csv(focal))

    outgroup_samples = {}
    outgroup_samples_idx = {}

    # deal with outgroup samples
    for idx, outgroup in enumerate(outgroups):
        outgroup_samples[idx] = list(open_csv(outgroup))
        outgroup_samples_idx[idx] = search_samples(
            outgroup_samples[idx], plink)

    print(outgroup_samples_idx)
