#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Unit tests for helper.py functions, especially testing sample order consistency
between CSV metadata and VCF genotypes.
"""

import json
import tempfile
import traceback

import pytest
import tskit
import tsinfer
import tszip

from click.testing import CliRunner

from tskitetude.helper import (
    add_populations,
    add_diploid_individuals,
    add_diploid_sites,
    create_tstree,
)


@pytest.fixture
def temp_csv_same_order(tmp_path):
    """Create a CSV file with samples in the same order as VCF"""
    csv_file = tmp_path / "samples_same_order.csv"
    csv_file.write_text("PopA,Sample1\nPopB,Sample2\nPopA,Sample3\n")
    return str(csv_file)


@pytest.fixture
def temp_csv_different_order(tmp_path):
    """Create a CSV file with samples in different order than VCF"""
    csv_file = tmp_path / "samples_different_order.csv"
    csv_file.write_text("PopA,Sample3\nPopB,Sample2\nPopA,Sample1\n")
    return str(csv_file)


@pytest.fixture
def temp_vcf_file(tmp_path):
    """
    Create a minimal VCF file with 3 samples in a specific order: Sample1, Sample2, Sample3
    """
    vcf_file = tmp_path / "test.vcf"
    vcf_content = """##fileformat=VCFv4.2
##contig=<ID=chr1,length=1000>
##FORMAT=<ID=GT,Number=1,Type=String,Description="Genotype">
#CHROM	POS	ID	REF	ALT	QUAL	FILTER	INFO	FORMAT	Sample1	Sample2	Sample3
chr1	100	.	A	T	.	PASS	.	GT	0|0	0|1	1|1
chr1	200	.	C	G	.	PASS	.	GT	0|1	1|1	0|0
chr1	300	.	G	A	.	PASS	.	GT	1|1	0|0	0|1
"""
    vcf_file.write_text(vcf_content)
    return str(vcf_file)


@pytest.fixture
def temp_vcf_file_extended(tmp_path):
    """
    Create a VCF file with more SNPs for full pipeline testing (to avoid tsdate errors)
    """
    vcf_file = tmp_path / "test_extended.vcf"
    vcf_content = """##fileformat=VCFv4.2
##contig=<ID=chr1,length=10000>
##FORMAT=<ID=GT,Number=1,Type=String,Description="Genotype">
#CHROM	POS	ID	REF	ALT	QUAL	FILTER	INFO	FORMAT	Sample1	Sample2	Sample3
chr1	100	.	A	T	.	PASS	.	GT	0|0	0|1	1|1
chr1	500	.	C	G	.	PASS	.	GT	0|1	1|1	0|0
chr1	1000	.	G	A	.	PASS	.	GT	1|1	0|0	0|1
chr1	1500	.	T	C	.	PASS	.	GT	0|0	1|1	0|1
chr1	2000	.	A	G	.	PASS	.	GT	1|0	0|1	1|1
chr1	2500	.	C	T	.	PASS	.	GT	1|1	0|0	1|0
chr1	3000	.	G	C	.	PASS	.	GT	0|1	1|0	0|0
chr1	3500	.	T	A	.	PASS	.	GT	1|1	1|1	0|1
chr1	4000	.	A	C	.	PASS	.	GT	0|0	0|1	1|1
chr1	4500	.	C	A	.	PASS	.	GT	1|0	1|1	0|0
"""
    vcf_file.write_text(vcf_content)
    return str(vcf_file)


def test_sample_order_consistency_same_order(temp_csv_same_order, temp_vcf_file):
    """
    Test that when CSV order matches VCF order, samples are correctly assigned to populations.
    VCF order: Sample1, Sample2, Sample3
    CSV order: Sample1, Sample2, Sample3
    """
    import cyvcf2

    with tempfile.NamedTemporaryFile(suffix=".samples") as tmp:
        with tsinfer.SampleData(path=tmp.name, sequence_length=1000) as samples:
            pop_lookup = add_populations(temp_csv_same_order, samples)
            indv_lookup = add_diploid_individuals(
                temp_csv_same_order, pop_lookup, samples
            )

            # Read VCF
            vcf = cyvcf2.VCF(temp_vcf_file)
            try:
                add_diploid_sites(
                    vcf, samples, {}, indv_lookup, ancestral_method="reference"
                )
            finally:
                vcf.close()

        # Re-open to read the data
        samples = tsinfer.load(tmp.name)

        # Check that we have the correct number of samples and sites
        assert samples.num_samples == 6  # 3 individuals * 2 (diploid)
        assert samples.num_individuals == 3
        assert samples.num_sites == 3

        # Verify that each individual has the correct population assignment
        # Individual 0 should be Sample1 (PopA)
        ind0_meta = samples.individual(0).metadata
        assert ind0_meta["name"] == "Sample1"
        assert (
            samples.population(samples.individual(0).population).metadata["name"]
            == "PopA"
        )

        # Individual 1 should be Sample2 (PopB)
        ind1_meta = samples.individual(1).metadata
        assert ind1_meta["name"] == "Sample2"
        assert (
            samples.population(samples.individual(1).population).metadata["name"]
            == "PopB"
        )

        # Individual 2 should be Sample3 (PopA)
        ind2_meta = samples.individual(2).metadata
        assert ind2_meta["name"] == "Sample3"
        assert (
            samples.population(samples.individual(2).population).metadata["name"]
            == "PopA"
        )


def test_sample_order_consistency_different_order(
    temp_csv_different_order, temp_vcf_file
):
    """
    CRITICAL TEST: Check if genotypes are correctly assigned when CSV order differs from VCF.
    VCF order: Sample1, Sample2, Sample3
    CSV order: Sample3, Sample2, Sample1
    """
    import cyvcf2

    with tempfile.NamedTemporaryFile(suffix=".samples") as tmp:
        with tsinfer.SampleData(path=tmp.name, sequence_length=1000) as samples:
            pop_lookup = add_populations(temp_csv_different_order, samples)
            indv_lookup = add_diploid_individuals(
                temp_csv_different_order, pop_lookup, samples
            )

            # Read VCF
            vcf = cyvcf2.VCF(temp_vcf_file)
            try:
                add_diploid_sites(
                    vcf, samples, {}, indv_lookup, ancestral_method="reference"
                )
            finally:
                vcf.close()

        # Re-open to read the data
        samples = tsinfer.load(tmp.name)

        # The individuals are added in CSV order: Sample3, Sample2, Sample1
        # But genotypes are in VCF order: Sample1, Sample2, Sample3

        # Individual 0 in samples should be Sample3 (from CSV)
        ind0_meta = samples.individual(0).metadata
        assert ind0_meta["name"] == "Sample3"

        # Get the genotypes for site 0 (position 100)
        # VCF has: Sample1=0|0, Sample2=0|1, Sample3=1|1
        site0_genotypes = samples.sites_genotypes[0]

        # If order is correct, individual 0 (Sample3) should have genotypes [1, 1]
        sample3_genotypes = site0_genotypes[0:2]  # First individual (2 alleles)

        # Expected: Sample3's genotypes from VCF = [1, 1]
        assert list(sample3_genotypes) == [1, 1], (
            f"Expected Sample3 genotypes [1,1] but got {list(sample3_genotypes)}. "
            f"This indicates genotypes are taken from VCF order, not CSV order."
        )


def test_genotype_data_integrity(temp_csv_same_order, temp_vcf_file):
    """
    Test that genotype data is correctly stored when order matches.
    VCF site 0 (pos 100): Sample1=0|0, Sample2=0|1, Sample3=1|1
    """
    import cyvcf2

    with tempfile.NamedTemporaryFile(suffix=".samples") as tmp:
        with tsinfer.SampleData(path=tmp.name, sequence_length=1000) as samples:
            pop_lookup = add_populations(temp_csv_same_order, samples)
            indv_lookup = add_diploid_individuals(
                temp_csv_same_order, pop_lookup, samples
            )

            vcf = cyvcf2.VCF(temp_vcf_file)
            try:
                add_diploid_sites(
                    vcf, samples, {}, indv_lookup, ancestral_method="reference"
                )
            finally:
                vcf.close()

        samples = tsinfer.load(tmp.name)

        # Site 0 genotypes should be: [0,0, 0,1, 1,1] for Sample1, Sample2, Sample3
        site0_genotypes = list(samples.sites_genotypes[0])
        assert site0_genotypes == [0, 0, 0, 1, 1, 1]

        # Site 1 (pos 200): Sample1=0|1, Sample2=1|1, Sample3=0|0
        site1_genotypes = list(samples.sites_genotypes[1])
        assert site1_genotypes == [0, 1, 1, 1, 0, 0]

        # Site 2 (pos 300): Sample1=1|1, Sample2=0|0, Sample3=0|1
        site2_genotypes = list(samples.sites_genotypes[2])
        assert site2_genotypes == [1, 1, 0, 0, 0, 1]


def test_create_tstree_no_errors(temp_csv_same_order, temp_vcf_file_extended, tmp_path):
    """
    Test tree creation with create_tstree script
    """

    # Define output paths in temporary directory
    output_samples = tmp_path / "output.samples"
    output_trees = tmp_path / "output.trees"

    runner = CliRunner()

    result = runner.invoke(
        create_tstree,
        [
            "--vcf",
            temp_vcf_file_extended,
            "--focal",
            temp_csv_same_order,
            "--ancestral_as_reference",
            "--output_samples",
            str(output_samples),
            "--output_trees",
            str(output_trees),
            "--tsdate_method",
            "inside_outside",  # required to avoid tsdate errors with few variants
        ],
    )

    # Check that command succeeded
    if result.exit_code != 0:
        # Capture and display stdout/stderr for debugging
        print("\n=== STDOUT ===")
        print(result.output)
        print("\n=== STDERR ===")
        print(result.stderr if hasattr(result, "stderr") else "No stderr available")
        print("\n=== Exception ===")
        if result.exception:
            print(
                "".join(
                    traceback.format_exception(
                        type(result.exception),
                        result.exception,
                        result.exception.__traceback__,
                    )
                )
            )

    assert result.exit_code == 0, (
        f"Command failed with exit code {result.exit_code}. Output: {result.output}"
    )

    # Verify output files were created
    assert output_samples.exists(), "Output samples file was not created"
    assert output_trees.exists(), "Output trees file was not created"

    # Load the resulting tree sequence
    ts = tszip.load(str(output_trees))

    # Basic checks on the tree sequence
    assert ts.num_individuals == 3, "Unexpected number of individuals in tree sequence"

    # test that populations and individuals have correct metadata schemas
    assert isinstance(ts.tables.populations.metadata_schema, tskit.MetadataSchema)
    assert isinstance(ts.tables.individuals.metadata_schema, tskit.MetadataSchema)

    # Verify population metadata
    pop_breeds = set()
    for pop in ts.populations():
        if pop.metadata:
            # currently metadata is stored as bytes, decode it
            # TODO: support custom POPULATION_METADATA_SCHEMA
            metadata = json.loads(pop.metadata.decode())
            pop_breeds.add(metadata.get("name"))

    assert "PopA" in pop_breeds
    assert "PopB" in pop_breeds

    # Verify individual metadata
    sample_ids = set()
    for ind in ts.individuals():
        if ind.metadata:
            # currently metadata is stored as bytes, decode it
            # TODO: support custom INDIVIDUAL_METADATA_SCHEMA
            metadata = json.loads(ind.metadata.decode())
            sample_ids.add(metadata.get("name"))

    assert "Sample1" in sample_ids
    assert "Sample2" in sample_ids
    assert "Sample3" in sample_ids
