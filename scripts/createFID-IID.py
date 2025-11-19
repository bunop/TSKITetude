#!/usr/bin/env python
# -*- coding: utf-8 -*-
# For a file like
# tsk_0	MM
# tsk_1	MM
# tsk_2	MM
# tsk_3	MM
# tsk_4	MM
# create a FID-IID TSV file like
# MM	tsk_0
# MM	tsk_1
# MM	tsk_2
# MM	tsk_3
# MM	tsk_4
# But using only individuals present in a given VCF file. Scan
# for VCF files inside a folder and create the corresponding
# FID-IID TSV file.

import os
import csv
import argparse
import cyvcf2
import pathlib
import logging

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Create a FID-IID TSV file from a list of individuals and a VCF file"
    )
    parser.add_argument(
        "-i",
        "--indiv-list",
        required=True,
        help="Input individual list file",
    )
    parser.add_argument(
        "-d",
        "--directory",
        required=True,
        type=pathlib.Path,
        help="Input directory containing VCF files",
    )

    args = parser.parse_args()

    # need to open list of individuals
    with open(args.indiv_list, "r") as f:
        reader = csv.reader(f, delimiter="\t")
        indivs = {row[0]: row[1] for row in reader}

    vcf_files = [f for f in os.listdir(args.directory) if f.endswith(".vcf.gz")]

    logging.info(
        f"Found {len(vcf_files)} VCF files in directory '{args.directory}': {vcf_files}"
    )

    for vcf_file in vcf_files:
        vcf_path = args.directory / vcf_file

        logging.info(f"Processing VCF file: {vcf_path}")

        vcf = cyvcf2.VCF(str(vcf_path))
        vcf_indivs = set(vcf.samples)

        outfile = args.directory / vcf_file.replace(
            ".vcf.gz", ".sample_names.txt"
        )

        logging.info(f"Output file: {outfile}")

        with open(outfile, "w") as f:
            writer = csv.writer(f, delimiter="\t", lineterminator="\n")
            for iid in vcf_indivs:
                if iid in indivs:
                    fid = indivs[iid]
                    writer.writerow([fid, iid])
                else:
                    raise Exception(
                        f"Individual ID '{iid}' found in VCF but not in '{args.indiv_list}'"
                    )

        logging.info(f"Written {len(vcf_indivs)} individuals to {outfile}")
