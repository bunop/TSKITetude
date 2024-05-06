
import csv
import logging
import itertools
import collections
from typing import List

import click
from cyvcf2 import VCF

from .helper import open_csv

log_fmt = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
logging.basicConfig(level=logging.INFO, format=log_fmt)

# Get an instance of a logger
logger = logging.getLogger(__name__)


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
@click.option(
    "--output_data",
    help="Output data file",
    required=True
)
@click.option(
    "--output_config",
    help="Output config file",
    required=True
)
@click.option(
    "--output_mapping",
    help="Output mapping file",
    required=True
)
@click.option(
    "--model",
    help="Model type",
    default=2
)
@click.option(
    "--nrandom",
    help="N random iterations",
    default=10
)
def make_est_sfs_input(
        vcf_file: click.Path, focal: click.Path, outgroups: List[click.Path],
        output_data: str, output_config: str, output_mapping: str, model: int,
        nrandom: int):

    """
    inspired from: "https://github.com/Popgen48/scalepopgen_v1/blob/defb5d6a8a95b3fd84bd4312c4a42ef2ef6b9b7b/bin/create_estsfs_inputs.py"
    """

    data_handle = open(output_data, "w")
    data_writer = csv.writer(data_handle, delimiter="\t", lineterminator="\n")

    mapping_handle = open(output_mapping, "w")
    mapping_writer = csv.writer(mapping_handle, delimiter=",", lineterminator="\n")

    # since the mapping writer will be used by the pipeline, add header:
    header = ["chrom", "pos", "ref", "alt", "major"]
    mapping_writer.writerow(header)

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
        # are at the left side of the VCF (I have imputed this data, if I'm skipping
        # a variant, maybe I have ancient allele and not focal, for example
        # when ancient is an HD variant and focal not).
        # My focal samples have been inputed, so I will not expect an half missing
        # or a missing samples in focal genotype
        if (-1, -1) in (
            (a1, a2) for a1, a2, _ in variant.genotypes[0:len(focal_samples)]):
            logger.debug(
                f"skipping {variant.ID} ({variant.CHROM}:{variant.POS}): "
                "missing a focal sample genotype"
            )
            continue

        # there's also the possibility that all the ancient genotypes are missing:
        # even in this casa I need to skip the variant
        if all(x == (-1, -1) for x in (
                (a1, a2) for a1, a2, _ in variant.genotypes[len(focal_samples):])):
            logger.debug(
                f"skipping {variant.ID} ({variant.CHROM}:{variant.POS}): "
                "all ancient samples are missing"
            )
            continue

        # there's the possibility to have no ALT  allele
        if not variant.ALT:
            logger.warning(
                f"skipping {variant.ID} ({variant.CHROM}:{variant.POS}): "
                "no ALT allele!"
            )
            continue

        # there's the possibility to have more than 1 ALT allele: s42964.1
        # for example seems to have different reference sequence than forward
        # and ncbi alleles, while normalization fix the reference allele
        # but not genotypes. Discard SNP
        if len(variant.ALT) > 1:
            logger.warning(
                f"skipping {variant.ID} ({variant.CHROM}:{variant.POS}): "
                f"multiple ALT alleles ({variant.ALT})"
            )
            continue

        # TODO: need I to check if I have *at least* one allele for all outgroups?

        # get all genotype (as letters) for each sample
        genotypes = {sample: genotype for sample, genotype in zip(
            vcf.samples, variant.gt_bases)}

        mapping_record = [
            variant.CHROM, variant.POS, variant.REF, variant.ALT[0]]

        # A, C, G, T count for focal samples
        bases = ["A", "C", "G", "T"]
        focal_counts = [0, 0, 0, 0]

        # instantiate counts for outgroups. This will be a dict, where key is
        # the outgroup index, and value the count array
        outgroup_counts = {}
        for i in range(len(outgroups)):
            outgroup_counts[i] = [0, 0, 0, 0]

        # process all focal samples and count alleles
        for focal_sample in focal_samples:
            # I suppose that my focal samples are always phased
            genotype = genotypes[focal_sample].split("|")

            for allele in genotype:
                try:
                    # search upper allele: reference sequence coul be soft
                    # masked
                    idx = bases.index(allele.upper())

                except ValueError as exc:
                    logger.warning(f"{variant}")
                    logger.warning(f"{genotype}")
                    raise exc

                focal_counts[idx] += 1

        # time to count for outgroup samples
        for i, outgroup in enumerate(outgroups):
            for outgroup_sample in outgroup_samples[i]:
                genotype = genotypes[outgroup_sample].split("/")

                for allele in genotype:
                    if allele == '.':
                        # I've already excluded that all my samples are missing
                        logger.debug(
                            f"skipping allele for {outgroup_sample} at "
                            f"{variant.ID} ({variant.CHROM}:{variant.POS}): "
                            f"{genotype}"
                        )
                        continue

                    try:
                        # search upper allele: reference sequence coul be soft
                        # masked
                        idx = bases.index(allele.upper())

                    except ValueError as exc:
                        logger.warning(f"{variant}")
                        logger.warning(f"{genotype}")
                        raise exc

                    outgroup_counts[i][idx] += 1

            # get the most common allele for outgroup, since outgroup
            # alleles need to have only one count for ancestor alleles,
            # not the total count as samples
            most_common_idx = max(
                enumerate(outgroup_counts[i]), key=lambda x: x[1])[0]

            # redefine the outgroup counts
            outgroup_counts[i] = [0, 0, 0, 0]
            outgroup_counts[i][most_common_idx] = 1

        # determine the major allele in focal samples
        most_common_idx = max(
            enumerate(focal_counts), key=lambda x: x[1])[0]
        mapping_record.append(bases[most_common_idx])

        # time to define the output record
        data_record = [",".join([str(count) for count in focal_counts])]

        for i in range(len(outgroups)):
            data_record += [
                ",".join([str(count) for count in outgroup_counts[i]])]

        # print a est-sfs input file record and track mapping
        data_writer.writerow(data_record)
        mapping_writer.writerow(mapping_record)

        data_handle.flush()
        mapping_handle.flush()

    data_handle.close()
    mapping_handle.close()

    # write a config file
    with open(output_config, "w") as handle:
        handle.write(f"n_outgroup {len(outgroups)}\n")
        handle.write(f"model {model}\n")
        handle.write(f"nrandom {nrandom}\n")


@click.command()
@click.option(
    "--mapping",
    help="est-sfs mapping file",
    type=click.Path(exists=True),
    required=True
)
@click.option(
    "--pvalues",
    help="est-sfs pvalues file",
    type=click.Path(exists=True),
    required=True
)
@click.option(
    "--output",
    help="Output results file",
    type=click.Path(exists=False),
    required=True
)
@click.option(
    "--confidence",
    help="Confidence level (ex. 0.95)",
    default=0.95,
    type=float
)
def parse_est_sfs_output(
        mapping: click.Path, pvalues: click.Path, output: click.Path,
        confidence: float):
    """
    inspired from: https://github.com/Popgen48/scalepopgen_v1/blob/defb5d6a8a95b3fd84bd4312c4a42ef2ef6b9b7b/modules/local/gawk/create_anc_files/main.nf
    """

    # est.sfs return the probability that the major allele is the ancestral
    # using a two-tailed test. So:
    upper_tail = 1 - ((1 - confidence) / 2)
    lower_tail = (1 - confidence) / 2

    logger.debug(f"upper tail: {upper_tail}")
    logger.debug(f"lower tail: {lower_tail}")

    output_file = open(output, "w")
    result_writer = csv.writer(output_file, delimiter=",", lineterminator="\n")

    with open(mapping, "r") as mapping_file, open(pvalues, "r") as pvalues_file:
        mapping_reader = csv.reader(mapping_file, delimiter=",", lineterminator="\n")
        mapping_header = next(mapping_reader)

        MappingRecord = collections.namedtuple('MappingRecord', mapping_header)

        # drop 7 rows from pvalues file
        pvalues_reader = csv.reader(pvalues_file, delimiter=" ", lineterminator="\n")
        pvalues_header = next(itertools.islice(pvalues_reader, 7, 8))
        pvalues_header[3] = "pmajor_ancestral"
        del(pvalues_header[0])

        PvaluesRecord = collections.namedtuple('PvaluesRecord', pvalues_header, rename=True)

        result_header = mapping_header + ["pmajor_ancestral", "anc_allele", "der_allele"]
        ResultRecord = collections.namedtuple('ResultRecord', result_header)
        result_writer.writerow(result_header)

        for tmp1, tmp2 in zip(mapping_reader, pvalues_reader):
            mapping_record = MappingRecord(*tmp1)

            # est-sfs define up to 19 columns: for the moment I will truncate
            # all the data after the header size
            pvalues_record = PvaluesRecord(*tmp2[:len(pvalues_header)])

            logger.debug(f"processing {mapping_record.chrom}:{mapping_record.pos}: {pvalues_record}")

            # ok skip record if the falls in the confidence interval
            if not (float(pvalues_record.pmajor_ancestral) > upper_tail or
                    float(pvalues_record.pmajor_ancestral) < lower_tail):
                logger.debug(f"Discarding {mapping_record.chrom}:{mapping_record.pos}")
                continue

            # determine if major allele is ALT  or REF
            if float(pvalues_record.pmajor_ancestral) < lower_tail:
                logger.debug(f"pmajor_ancestral lower than {lower_tail}")
                if mapping_record.major == mapping_record.ref:
                    logger.debug("major allele is REF: choosing ALT as ancestral")
                    anc_allele = 1
                    der_allele = 0
                else:
                    logger.debug("major allele is ALT: choosing REF as ancestral")
                    anc_allele = 0
                    der_allele = 1

            if float(pvalues_record.pmajor_ancestral) > upper_tail:
                logger.debug(f"pmajor_ancestral greater than {upper_tail}")
                if mapping_record.major == mapping_record.ref:
                    logger.debug("major allele is REF: choosing REF as ancestral")
                    anc_allele = 0
                    der_allele = 1
                else:
                    logger.debug("major allele is ALT: choosing ALT as ancestral")
                    anc_allele = 1
                    der_allele = 0

            result_record = ResultRecord(*tmp1+[float(pvalues_record.pmajor_ancestral), anc_allele, der_allele])
            result_writer.writerow(result_record)

    output_file.close()
