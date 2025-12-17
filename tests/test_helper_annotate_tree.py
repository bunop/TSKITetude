"""
Unit tests for the annotate_tree function in helper.py
"""

import json
import pytest
import tskit
import tszip
from pathlib import Path
from click.testing import CliRunner

from tskitetude.helper import annotate_tree


# Minimal VCF content for testing
MINIMAL_VCF = """##fileformat=VCFv4.2
##contig=<ID=1,length=1000>
#CHROM\tPOS\tID\tREF\tALT\tQUAL\tFILTER\tINFO\tFORMAT\tsample1\tsample2
1\t100\t.\tA\tG\t.\t.\t.\tGT\t0|0\t1|1
"""

# Sample metadata file (breed sample_id format)
SAMPLE_METADATA = """breed1\tsample1
breed2\tsample2
"""

# Sample metadata with extra columns
SAMPLE_METADATA_EXTRA_COLS = """breed1\tsample1\textra_info
breed2\tsample2\tmore_data
"""

# Malformed sample metadata (only one column)
MALFORMED_SAMPLE_METADATA = """breed1
breed2
"""

# Sample metadata with mismatch
MISMATCH_SAMPLE_METADATA = """breed1\tsample3
breed2\tsample4
"""


def create_minimal_tree_sequence(num_samples=2):
    """Create a minimal tree sequence for testing"""
    tables = tskit.TableCollection(sequence_length=1000)

    # Add nodes/samples (2 per individual for diploid)
    for i in range(num_samples):
        tables.nodes.add_row(flags=tskit.NODE_IS_SAMPLE, time=0)
        tables.nodes.add_row(flags=tskit.NODE_IS_SAMPLE, time=0)

    # Add a site
    site_id = tables.sites.add_row(position=100, ancestral_state="A")

    # Add mutations for the site
    for node_id in range(2 * num_samples):
        tables.mutations.add_row(site=site_id, node=node_id, derived_state="G")

    return tables.tree_sequence()


@pytest.fixture
def tmp_files(tmp_path):
    """Create temporary test files"""
    vcf_path = tmp_path / "test.vcf"
    sample_path = tmp_path / "samples.txt"
    input_tsz = tmp_path / "input.tsz"
    output_tsz = tmp_path / "output.tsz"

    # Write VCF
    vcf_path.write_text(MINIMAL_VCF)

    # Write sample metadata
    sample_path.write_text(SAMPLE_METADATA)

    # Create and save tree sequence
    ts = create_minimal_tree_sequence(num_samples=2)
    tszip.compress(ts, str(input_tsz))

    return {
        "vcf": str(vcf_path),
        "sample": str(sample_path),
        "input_tsz": str(input_tsz),
        "output_tsz": str(output_tsz),
        "tmp_path": tmp_path,
    }


def test_annotate_tree_success(tmp_files):
    """Test successful annotation of tree sequence"""
    runner = CliRunner()

    result = runner.invoke(
        annotate_tree,
        [
            "--input_tsz",
            tmp_files["input_tsz"],
            "--input_vcf",
            tmp_files["vcf"],
            "--sample_file",
            tmp_files["sample"],
            "--output_tsz",
            tmp_files["output_tsz"],
            "--software_name",
            "test_software",
            "--software_version",
            "1.0.0",
        ],
    )

    assert result.exit_code == 0, f"Command failed: {result.output}"
    assert Path(tmp_files["output_tsz"]).exists()

    # Load and verify the annotated tree sequence
    ts = tszip.load(tmp_files["output_tsz"])

    # Check populations were added
    assert ts.num_populations == 2

    # Check individuals were added
    assert ts.num_individuals == 2

    # Check metadata schemas are set
    assert isinstance(ts.tables.populations.metadata_schema, tskit.MetadataSchema)
    assert isinstance(ts.tables.individuals.metadata_schema, tskit.MetadataSchema)

    # Verify population metadata
    pop_breeds = set()
    for pop in ts.populations():
        if pop.metadata:
            pop_breeds.add(pop.metadata.get("name"))
    assert "breed1" in pop_breeds
    assert "breed2" in pop_breeds

    # Verify individual metadata
    sample_ids = set()
    for ind in ts.individuals():
        if ind.metadata:
            sample_ids.add(ind.metadata.get("name"))
    assert "sample1" in sample_ids
    assert "sample2" in sample_ids

    # Verify provenance was added
    provenances = [json.loads(p.record) for p in ts.provenances()]
    assert len(provenances) > 0
    assert any("test_software" in json.dumps(p) for p in provenances)


def test_annotate_tree_with_extra_columns(tmp_files):
    """Test annotation handles extra columns in sample file"""
    sample_path = Path(tmp_files["tmp_path"]) / "samples_extra.txt"
    sample_path.write_text(SAMPLE_METADATA_EXTRA_COLS)

    runner = CliRunner()
    result = runner.invoke(
        annotate_tree,
        [
            "--input_tsz",
            tmp_files["input_tsz"],
            "--input_vcf",
            tmp_files["vcf"],
            "--sample_file",
            str(sample_path),
            "--output_tsz",
            tmp_files["output_tsz"],
            "--software_name",
            "test",
            "--software_version",
            "1.0",
        ],
    )

    assert result.exit_code == 0
    assert Path(tmp_files["output_tsz"]).exists()


def test_annotate_tree_malformed_sample_file(tmp_files):
    """Test error handling for malformed sample file"""
    sample_path = Path(tmp_files["tmp_path"]) / "malformed.txt"
    sample_path.write_text(MALFORMED_SAMPLE_METADATA)

    runner = CliRunner()
    result = runner.invoke(
        annotate_tree,
        [
            "--input_tsz",
            tmp_files["input_tsz"],
            "--input_vcf",
            tmp_files["vcf"],
            "--sample_file",
            str(sample_path),
            "--output_tsz",
            tmp_files["output_tsz"],
            "--software_name",
            "test",
            "--software_version",
            "1.0",
        ],
    )

    assert result.exit_code != 0
    # Check that a ValueError was raised (sample file parsing or VCF mismatch)
    assert result.exception is not None
    assert isinstance(result.exception, ValueError)


def test_annotate_tree_sample_vcf_mismatch(tmp_files):
    """Test error handling when sample file doesn't match VCF samples"""
    sample_path = Path(tmp_files["tmp_path"]) / "mismatch.txt"
    sample_path.write_text(MISMATCH_SAMPLE_METADATA)

    runner = CliRunner()
    result = runner.invoke(
        annotate_tree,
        [
            "--input_tsz",
            tmp_files["input_tsz"],
            "--input_vcf",
            tmp_files["vcf"],
            "--sample_file",
            str(sample_path),
            "--output_tsz",
            tmp_files["output_tsz"],
            "--software_name",
            "test",
            "--software_version",
            "1.0",
        ],
    )

    assert result.exit_code != 0
    # Check that a ValueError was raised for sample/VCF mismatch
    assert result.exception is not None
    assert isinstance(result.exception, ValueError)


def test_annotate_tree_missing_input_file(tmp_files):
    """Test error handling for missing input files"""
    runner = CliRunner()
    result = runner.invoke(
        annotate_tree,
        [
            "--input_tsz",
            "nonexistent.tsz",
            "--input_vcf",
            tmp_files["vcf"],
            "--sample_file",
            tmp_files["sample"],
            "--output_tsz",
            tmp_files["output_tsz"],
            "--software_name",
            "test",
            "--software_version",
            "1.0",
        ],
    )

    assert result.exit_code != 0


def test_annotate_tree_node_population_assignment(tmp_files):
    """Test that nodes are correctly assigned to populations"""
    runner = CliRunner()
    result = runner.invoke(
        annotate_tree,
        [
            "--input_tsz",
            tmp_files["input_tsz"],
            "--input_vcf",
            tmp_files["vcf"],
            "--sample_file",
            tmp_files["sample"],
            "--output_tsz",
            tmp_files["output_tsz"],
            "--software_name",
            "test",
            "--software_version",
            "1.0",
        ],
    )

    assert result.exit_code == 0

    ts = tszip.load(tmp_files["output_tsz"])

    # Verify each node has a population assigned
    for node in ts.nodes():
        if node.flags & tskit.NODE_IS_SAMPLE:
            assert node.population != tskit.NULL
            assert node.individual != tskit.NULL


def test_annotate_tree_provenance_content(tmp_files):
    """Test that provenance record contains expected information"""
    software_name = "MyTestSoftware"
    software_version = "2.3.4"

    runner = CliRunner()
    result = runner.invoke(
        annotate_tree,
        [
            "--input_tsz",
            tmp_files["input_tsz"],
            "--input_vcf",
            tmp_files["vcf"],
            "--sample_file",
            tmp_files["sample"],
            "--output_tsz",
            tmp_files["output_tsz"],
            "--software_name",
            software_name,
            "--software_version",
            software_version,
        ],
    )

    assert result.exit_code == 0

    ts = tszip.load(tmp_files["output_tsz"])
    provenances = [json.loads(p.record) for p in ts.provenances()]

    # Find our provenance record
    our_prov = None
    for p in provenances:
        if p.get("software", {}).get("name") == software_name:
            our_prov = p
            break

    assert our_prov is not None
    assert our_prov["software"]["version"] == software_version
    assert "timestamp" in our_prov
    assert "parameters" in our_prov
    assert our_prov["parameters"]["populations_added"] == 2
    assert our_prov["parameters"]["individuals_added"] == 2
