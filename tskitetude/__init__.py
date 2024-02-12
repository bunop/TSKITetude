"""
TSKITetude

An helper library to deal with tskit objects
"""

import pathlib
import pkg_resources

__version__ = pkg_resources.get_distribution(__name__).version
__author__ = "Paolo Cozzi"


def get_project_dir() -> pathlib.PosixPath:
    mypath = pathlib.Path(__file__)
    return mypath.parents[1]

def get_data_dir() -> pathlib.PosixPath:
    return get_project_dir() / "data"
