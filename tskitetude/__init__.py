"""
TSKITetude

An helper library to deal with tskit objects
"""

import pathlib

import tskit

__version__ = "0.5.2"
__author__ = "Paolo Cozzi"


def get_project_dir() -> pathlib.PosixPath:
    mypath = pathlib.Path(__file__)
    return mypath.parents[1]


def get_data_dir() -> pathlib.PosixPath:
    return get_project_dir() / "data"


# define metadata schema for individuals and populations
POPULATION_METADATA_SCHEMA = tskit.MetadataSchema(
    {
        "codec": "json",
        "type": "object",
        "properties": {"breed": {"type": "string"}},
        "required": ["breed"],
    }
)


INDIVIDUAL_METADATA_SCHEMA = tskit.MetadataSchema(
    {
        "codec": "json",
        "type": "object",
        "properties": {"sample_id": {"type": "string"}},
        "required": ["sample_id"],
    }
)
