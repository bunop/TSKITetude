#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Create a fake FASTA file from a VCF file: the problem is that I couldn't have
# a ##contig=<ID=<ID>,length=<length>> line in the VCF header, so I create a fake FASTA
# with 'N's for each chromosome present in the VCF, and using REF allele if any.
# This could be used with bcftools reheader to add a contig line to the VCF header.


import argparse
from collections import OrderedDict

import os
import math
import cyvcf2
import Bio.Seq
import Bio.bgzf
import Bio.SeqIO
import Bio.SeqRecord


def compute_maxpos(vcf: cyvcf2.VCF) -> OrderedDict:
    maxpos = OrderedDict()

    for rec in vcf:
        chrom = rec.CHROM
        pos = rec.POS
        if chrom not in maxpos or pos > maxpos[chrom]:
            maxpos[chrom] = pos

    return maxpos


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Create a fake FASTA file from a VCF file"
    )
    parser.add_argument(
        "-v",
        "--vcf",
        required=True,
        type=argparse.FileType("r"),
        help="Input VCF file",
    )
    parser.add_argument(
        "-o",
        "--output",
        required=True,
        help="Output FASTA file",
    )

    args = parser.parse_args()

    if not args.output.endswith(".fa.gz"):
        print("Error: output file must have .fa.gz extension")
        exit(1)

    if os.path.exists(args.output):
        print(f"Error: output file '{args.output}' already exists")
        exit(1)

    # deal with file handles
    vcf_file = args.vcf
    vcf = cyvcf2.VCF(vcf_file.name)

    # compute the chromosome lengths from max positions in VCF
    chr_lengths = compute_maxpos(vcf)

    seq_records = []

    for chrom, length in chr_lengths.items():
        # round up to nearest million
        rounded_length = int(math.ceil(length / 1_000_000) * 1_000_000)
        seq = Bio.Seq.MutableSeq("N" * rounded_length)

        # fill in REF alleles from VCF
        for snp in vcf(chrom):
            pos = snp.POS - 1  # convert to 0-based
            ref_allele = snp.REF
            seq[pos : pos + len(ref_allele)] = ref_allele

        seq_record = Bio.SeqRecord.SeqRecord(
            id=chrom,
            name=chrom,
            seq=seq,
            description=f"Fake sequence for {chrom} of length {length}",
        )

        seq_records.append(seq_record)

    # write to output FASTA file
    with Bio.bgzf.open(args.output, "wb") as output_handle:
        Bio.SeqIO.write(seq_records, output_handle, "fasta")
