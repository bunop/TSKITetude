# TSKITetude

## Install from git repository

Simply clone this project with

```bash
git clone https://github.com/bunop/TSKITetude.git
```

## Set-Up

This project is managed with [Poetry](https://python-poetry.org/). Please,
follow their instructions to install [Poetry](https://python-poetry.org/docs/#installation).
Then recover this environment by entering on the cloned folder and type:

```bash
poetry install
```

Next, set up the git filter and attributes provided by [nbstripout](https://github.com/kynan/nbstripout):

```bash
nbstripout --install
```

## Activate poetry environment

In your `TSKITetude` folder, simply type:

```bash
poetry shell
```

to activate the poetry environment

## Get SMARTER-data

## Collect SMARTER genotypes

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
