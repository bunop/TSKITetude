"""
TSKITetude

An helper library to deal with tskit objects
"""

import pathlib

__version__ = "0.3.1"
__author__ = "Paolo Cozzi"


def get_project_dir() -> pathlib.PosixPath:
    mypath = pathlib.Path(__file__)
    return mypath.parents[1]

def get_data_dir() -> pathlib.PosixPath:
    return get_project_dir() / "data"
