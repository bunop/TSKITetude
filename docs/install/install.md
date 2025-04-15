
# Setting up the project

This project is mainly a python project managed using poetry, however there are
also `config` folder and `data` folder which are used for configuration and data
analysis using the [cnr-ibba/nf-treeseq](https://github.com/cnr-ibba/nf-treeseq)
nextflow pipeline. Files and folders are structured as follow:

```text
TSKITetude/
├── config
├── data
├── docs
├── experiments
├── poetry.lock
├── pyproject.toml
├── README.md
├── results-*
├── scripts
├── tests
├── TODO.md
├── tskitetude
└── work
```

* `config`: configuration directory for analyses with nextflow
* `data`: data folder (not tracked)
* `docs`: documentation folder (using `jupyter-book`)
  * `notebooks`: ipython notebooks folder
* `experiments`: experiments folder (not tracked)
* `poetry.lock`: managed by Poetry during installation. Don't touch
* `pyproject.toml`: required to manage this project with poetry. Dependencies
  can be managed using poetry (see [Managing dependencies](https://python-poetry.org/docs/managing-dependencies/))
* `README.md`: a general description of the project
* `results-*`: results folders (not tracked). Usually is the nextflow *results*
  folder
* `test`: test code for `tskitetude` python module
* `TODO.md`: TODO file
* `tskitetude`: source code of this project
* `work`: nextflow work folder (not tracked)

This folder is managed using git, and to avoid committing every *IPython notebook*
output you require the [nbstripout](https://github.com/kynan/nbstripout) software
installed, which will be called every time you do a `git add` or `git status`
command: this will strip out notebook results on the fly without erasing the
outputs of your local notebooks (and without requiring you to strip out results
before committing with Git, like `git-hooks` does).

## Install poetry

You require poetry to work with this project.
Install poetry with <https://python-poetry.org/docs/#installing-with-the-official-installer>. Then
install [poetry-bumpversion](https://pypi.org/project/poetry-bumpversion/) plugin
(*globally*) with:

```bash
poetry self add poetry-bumpversion
```

## Install from git repository

Simply clone this project with

```bash
git clone https://github.com/bunop/TSKITetude.git
```

## Set-Up

This project can be installed either as a minimal package or with all dependencies
required to execute Jupyter notebooks and build documentation. Please choose the
installation type that best suits your needs.

### Install TSKITetude Binaries

This option installs only the executables required to create Tree Sequence objects.
These executables are the same as those used in the
[cnr-ibba/nf-treeseq](https://github.com/cnr-ibba/nf-treeseq) Nextflow pipeline.
To install, navigate to the cloned repository folder and run:

```bash
poetry install
```

### Install the Full Project

To set up a complete environment with all dependencies required for documentation
and Jupyter notebooks, navigate to the cloned repository folder and run:

```bash
poetry install --with docs
```

This command installs all dependencies specified in Poetry, including `nbstripout`.

## Activate Poetry Environment

To activate the Poetry environment, navigate to your `TSKITetude` folder and run:

```bash
poetry shell
```

### Install nbstripout

If you plan to work with Jupyter notebooks and documentation, you should configure
Git to use the `nbstripout` tool to remove notebook output before committing.
This can be done by running:

```bash
nbstripout --install
```

from within a Poetry shell, or:

```bash
poetry run nbstripout --install
```

This will configure the filters in your local `.git/config` file.

## Install nextflow

Despite not being a python package, this project uses nextflow to run the
`cnr-ibba/nf-treeseq` pipeline. To install nextflow simply follow the steps
described in [Getting started](https://www.nextflow.io/#GetStarted) documentation,
or read the full [Installation](https://www.nextflow.io/docs/latest/install.html)
instructions in nextflow documentation.

## Poetry shell or Poetry run?

All the code within this project is installed using poetry. You have mainly two
options to run the code and interact with this repository contents:

1. `poetry shell`: this command will activate the poetry environment and you can
    run the code directly from the command line: a new shell will be opened with
    the poetry environment activated. To deactivate the environment, simply type
    `exit` or `Ctrl+D` to return to the previous shell.
2. `poetry run`: this command will run the code directly from the command line
    without activating the poetry environment. This is useful when you want to
    run a single command without activating the environment.

## Update poetry dependencies

There are two ways to update poetry dependencies: the first updates only the dependencies
and the `poetry.lock` file, the second updates the dependencies with both `pyproject.toml`
and `poetry.lock` file. The difference between the two is that the first command
will not force the requirement of a specific version of a package, while the second
will force the requirement of a specific version of a package.
To update only the dependencies, type:

```bash
poetry update [package1 package2 ...]
```

This will update the dependencies and the `poetry.lock` file. To update the
`pyproject.toml` file instead, type:

```bash
poetry add [package1 package2 ...]
```

or manually edit the `pyproject.toml` file and run `poetry lock [--no-update]`
to update the `poetry.lock` file. This will force the requirement of a specific
version of a package. Remember to call `poetry install` to ensure that the
dependencies are installed in the poetry environment.
