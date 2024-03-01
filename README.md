# TSKITetude

This project is an attempt to analyze SMARTER background data using [tskit](https://tskit.dev/). There's a *nextflow* pipeline able to transform SMARTER data in
[tskit](https://tskit.dev/tskit/docs/stable/introduction.html) *TreeSequence*
files. There's the `tskitetude` python library which does data conversion and
a `notebook` folder with some example code useful for analysis.
Files and folders are structured as follow:

```txt
.
├── config
├── data
├── Dockerfile
├── notebooks
├── poetry.lock
├── pyproject.toml
├── README.md
├── results
├── tests
├── TODO.md
├── tskitetude
└── tskit-pipeline
```

* `config`: tskit-pipeline configuration directory
* `data`: data folder (not tracked)
* `Dockerfile`: create a docker image with all `TSKITetude` dependencies. Required
  by the pipeline
* `notebooks`: folder with *IPython notebooks* files
* `poetry.lock`: managed by Poetry during installation. Don't touch
* `pyproject.toml`: required to manage this project with poetry. Dependencies
  can be managed using poetry (see [Managing dependencies](https://python-poetry.org/docs/managing-dependencies/))
* `README.md`: this file
* `results`: a result folder not tracked with Git. Usually is the nextflow *results*
  folder
* `test`: test code for `tskitetude` python module
* `TODO.md`: TODO file
* `tskitetude`: source code of this project
* `tskit-pipeline`: the nextflow tskit pipeline

This folder is managed using git, and to avoid committing every *IPython notebook*
output you require the [nbstripout](https://github.com/kynan/nbstripout) software
installed, which will be called every time you do a `git add` or `git status`
command: this will strip out notebook results on the fly without erasing the
outputs of your local notebooks (and without requiring you to strip out results
before committing with Git).

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

Recover (or install) this environment by entering in the cloned folder and type:

```bash
poetry install
```

This will install all poetry dependencies, including `nbstripout`.

## Activate poetry environment

In your `TSKITetude` folder, simply type:

```bash
poetry shell
```

to activate the poetry environment. Next, set up the git filter and attributes
provided by [nbstripout](https://github.com/kynan/nbstripout) with:

```bash
nbstripout --install
```

This will install nbstripout in your Poetry *bin* path.

## Get SMARTER-data

### Collect SMARTER genotypes

Connect to SMARTER FTPs site and download *Sheep* and *Goat* datasets:

```lftp
cd SHEEP/OAR3
mget SMARTER-OA-OAR3-top-0.4.9.*
```

### Convert into *forward* coding

SMARTER data is stored in *illumina top*. It is possible to convert data into
forward coordinates with `SNPconvert.py` coming from [SMARTER-database](https://github.com/cnr-ibba/SMARTER-database)
project:

```bash
python src/data/SNPconvert.py --bfile ~/Projects/TSKITetude/data/SMARTER-OA-OAR3-top-0.4.9 \
    --src_coding top --dst_coding forward --assembly OAR3 --species Sheep \
    --results_dir ~/Projects/TSKITetude/data/
```

## The tskit-pipeline

The proposed pipeline is supposed to work starting from the entire SMARTER
database: all the sheep background samples will be extracted from the whole
database, including the samples required to estimate ancestor alleles: the former
samples will be referred as *focal* samples, the latter *ancient*.
The two groups will be processed separately: data will be converted into VCF
and normalized against the reference sequence. Focal samples will be *phased* and
*imputed* using [Beagle](https://faculty.washington.edu/browning/beagle/b5_2.html)
before being joined with ancient samples to determine ancestor alleles
using [est-sfs](https://sourceforge.net/projects/est-usfs/) software
(see [Keightley and Jackson 2018](https://academic.oup.com/genetics/article/209/3/897/5930981)).
Then the output will be used to define *samples* and *TreeSequences*
using [tsinfer](https://tskit.dev/tsinfer/docs/stable/). Ages
will be estimated with [tsdate](https://tskit.dev/software/tsdate.html)

### Select background samples
