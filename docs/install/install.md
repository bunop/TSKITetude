
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

## Install python dependencies

Install (or update) python dependencies by entering in the cloned folder and type:

```bash
poetry install
```

This will install all poetry dependencies, including `nbstripout`.

## Install nbstripout filters

This project uses `nbstripout` to strip out notebook outputs before committing
to git. To install the filters, type:

```bash
poetry run nbstripout --install
```

This will install the filters in your local `.git/config` file.

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
