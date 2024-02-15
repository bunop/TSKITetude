
from typing import List

import click
from cyvcf2 import VCF

from .helper import open_csv
from .estsfs import search_samples


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
        vcf_file: click.Path, focal: click.Path, outgroups: List[click.Path]):

    # read focal samples
    focal_samples = list(open_csv(focal))

    # deal with outgroup samples
    outgroup_samples = {}
    for idx, outgroup in enumerate(outgroups):
        outgroup_samples[idx] = list(open_csv(outgroup))

    print(focal_samples)
    print(outgroup_samples)
