

# Project Setup

TSKITetude is primarily a Python project managed with Poetry. In addition to the
main codebase, the `config` and `data` folders are used for configuration and
data analysis with the [cnr-ibba/nf-treeseq](https://github.com/cnr-ibba/nf-treeseq)
Nextflow pipeline. The main files and folders are organized as follows:


```text
TSKITetude/
├── config         # Configuration files for Nextflow analyses
├── data           # Data files (not tracked by git)
├── docs           # Documentation (Jupyter Book)
│   └── notebooks  # Jupyter notebooks
├── experiments    # Experiment files (not tracked)
├── poetry.lock    # Managed by Poetry, do not edit manually
├── pyproject.toml # Poetry project configuration and dependencies
├── README.md      # Project overview
├── results-*      # Results folders (not tracked, usually Nextflow outputs)
├── scripts        # Utility scripts
├── tests          # Test code for the tskitetude Python module
├── TODO.md        # Project task list
├── tskitetude     # Main source code
└── work           # Nextflow work directory (not tracked)
```

## Notebook Output Management

This project uses Git for version control. To avoid committing outputs from
Jupyter notebooks, it is recommended to install [nbstripout](https://github.com/kynan/
nbstripout). This tool automatically strips notebook outputs when you run `git add`
or `git status`, without affecting your local files.

## Poetry Installation

Poetry is required to manage dependencies and environments for this project.
Install Poetry by following the official instructions: <https://python-poetry.org/docs/#installing-with-the-official-installer>.

Optionally, you can install the [poetry-bumpversion](https://pypi.org/project/
poetry-bumpversion/) plugin globally:

```bash
poetry self add poetry-bumpversion
```

## Clone the Repository

Clone the project using:

```bash
git clone https://github.com/bunop/TSKITetude.git
```

## Installation Options

You can install TSKITetude in two ways, depending on your needs:

### Choose a Python Version

Before installing, ensure you have the appropriate Python version installed.
TSKITetude requires Python 3.10 or higher. You can manage multiple Python versions
using tools like `pyenv` or `conda`, and set the desired version for this project
like this:

```bash
poetry env use python3.12
```

Where `python3.12` should be the executable for the Python version you want to use
(need to be in your `$PATH`).

### Minimal Installation

Installs only the executables required to create Tree Sequence objects (as used
in the Nextflow pipeline):

```bash
poetry install
```

### Full Installation

Installs all dependencies required for documentation and Jupyter notebooks:

```bash
poetry install --with docs
```

This will also install `nbstripout`, which needs to be configured separately
(see [See Configuring nbstripout](#configuring-nbstripout)).

## Activating the Poetry Environment

To activate the Poetry environment, navigate to your `TSKITetude` folder and run:

```bash
eval $(poetry env activate)
```

If you have a Poetry version older than 2.x, use:

```bash
poetry shell
```

## Configuring nbstripout

If you work with Jupyter notebooks, configure Git to use `nbstripout` to remove
notebook outputs before committing:

```bash
poetry run nbstripout --install
```

This sets up the necessary filters in your local `.git/config` file.

## Nextflow Installation

Nextflow is required to run the `cnr-ibba/nf-treeseq` pipeline, but it is not
a Python package. Install Nextflow by following the [Getting Started](https://
www.nextflow.io/#GetStarted) guide or the full [Installation documentation](
https://www.nextflow.io/docs/latest/install.html).

## Running Code: poetry shell vs poetry run

You have two main options for running code in this project:

1.  Activate the Poetry environment as described in [Activating
    the Poetry Environment](#activating-the-poetry-environment)
    to open a new shell. You can run commands directly. To exit, type `exit`
    or press `Ctrl+D` to close the shell.
2. `poetry run`: Runs a single command within the Poetry environment,
    without opening a new shell.

## Updating Poetry Dependencies

There are two ways to update dependencies:

- Display outdated packages:
  ```bash
  poetry show --outdated
  ```
- To update only the dependencies and the `poetry.lock` file:
  ```bash
  poetry update [package1 package2 ...]
  ```
- To update both `pyproject.toml` and `poetry.lock` (forcing a specific version):
  ```bash
  poetry add [package1 package2 ...]
  ```
  Alternatively, manually edit `pyproject.toml` and run:
  ```bash
  poetry lock [--no-update]
  ```
  After any changes, run `poetry install` to apply updates in your environment.

```{warning}
There are packages that can't be updated due to compatibility issues. Always check the
output of `poetry update` for any conflicts or errors.
```