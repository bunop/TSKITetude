"""
TSKITetude

An helper library to deal with tskit objects
"""

import pathlib

import tskit

__version__ = "0.5.3"
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
        "additionalProperties": True,
        "properties": {
            "name": {"type": "string", "description": "The name of the population"},
            "description": {
                "type": "string",
                "description": "A description of the population",
            },
        },
        "required": ["name"],
        "type": "object",
    }
)


INDIVIDUAL_METADATA_SCHEMA = tskit.MetadataSchema(
    {
        "codec": "json",
        "additionalProperties": True,
        "properties": {
            "name": {"type": "string", "description": "The name of the individual"},
        },
        "required": ["name"],
        "type": "object",
    }
)
