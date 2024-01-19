
import pathlib

def get_project_dir() -> pathlib.PosixPath:
    mypath = pathlib.Path(__file__)
    return mypath.parents[1]
