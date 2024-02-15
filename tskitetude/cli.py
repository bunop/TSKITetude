
import csv
import sys
from typing import List

import click
from cyvcf2 import VCF

from .helper import open_csv


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

    writer = csv.writer(sys.stdout, delimiter="\t", lineterminator="\n")

    # read focal samples
    focal_samples = [sample_id for _, sample_id in open_csv(focal)]

    # deal with outgroup samples
    outgroup_samples = {}
    for idx, outgroup in enumerate(outgroups):
        outgroup_samples[idx] = [sample_id for _, sample_id in open_csv(outgroup)]

    # open a vcf file
    vcf = VCF(vcf_file)

    for variant in vcf:
        # test if I have all genotypes for focal samples. All my focal variants
        # are at the left side of the VCF
        if (-1, -1) in [
            (a1, a2) for a1, a2, _ in variant.genotypes[0:len(focal_samples)]]:
            continue

        genotypes = {sample: genotype for sample, genotype in zip(
            vcf.samples, variant.gt_bases)}

        # A, C, G, T count for focal samples
        bases = ["A", "C", "G", "T"]
        focal_counts = [0, 0, 0, 0]

        outgroup_counts = {}
        for i in range(len(outgroups)):
            outgroup_counts[i] = [0, 0, 0, 0]

        for focal_sample in focal_samples:
            # I suppose that my focal samples are always phased
            genotype = genotypes[focal_sample].split("|")

            for allele in genotype:
                idx = bases.index(allele)
                focal_counts[idx] += 1

        # time to count for outgroup samples
        for i, outgroup in enumerate(outgroups):
            for outgroup_sample in outgroup_samples[i]:
                genotype = genotypes[outgroup_sample].split("/")

                for allele in genotype:
                    idx = bases.index(allele)
                    outgroup_counts[i][idx] += 1

            # get the most common allele for outgroup
            most_common_idx = max(
                enumerate(outgroup_counts[i]), key=lambda x: x[1])[0]

            # redefine the outgroup counts
            outgroup_counts[i] = [0, 0, 0, 0]
            outgroup_counts[i][most_common_idx] = 1

        # time to define the output record
        record = [",".join([str(count) for count in focal_counts])]

        for i in range(len(outgroups)):
            record += [",".join([str(count) for count in outgroup_counts[i]])]

        # print a est-sfs input file record
        writer.writerow(record)
