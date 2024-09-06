# TSKITetude

This project is an attempt to analyze SMARTER data using [tskit](https://tskit.dev/).
Most of the analyses are done using [cnr-ibba/nf-treeseq](https://github.com/cnr-ibba/nf-treeseq)
*nextflow* pipeline able which is able to transform SMARTER data in
[tskit](https://tskit.dev/tskit/docs/stable/introduction.html) *TreeSequence*
files. Within this project, there's the `tskitetude` python library which does
data conversion and is then used in the nextflow pipeline. There's also
a `notebook` folder with some example code useful for analysis.
Files and folders are structured as follow:

```text
TSKITetude/
├── config
├── data
├── Dockerfile
├── docs
├── experiments
├── Makefile
├── poetry.lock
├── pyproject.toml
├── README.md
├── results-*
├── scripts
├── tests
├── TODO.md
├── tskitetude
└── tskit-pipeline
```

* `config`: configuration directory for analyses with nextflow
* `data`: data folder (not tracked)
* `Dockerfile`: create a docker image with all `TSKITetude` dependencies. Required
* `docs`: `jupyter-book` documentation folder
  * `notebooks`: folder with *IPython notebooks* files
* `experiments`: testing stuff folder. Not tracked
* `Makefile`: automate some boring stuff
* `poetry.lock`: managed by Poetry during installation. Don't touch
* `pyproject.toml`: required to manage this project with poetry. Dependencies
  can be managed using poetry (see [Managing dependencies](https://python-poetry.org/docs/managing-dependencies/))
* `README.md`: this file
* `results-*`: results folders not tracked with Git. Usually is the nextflow *results* folder
* `scripts`: scripts used to perform analyses
* `test`: test code for `tskitetude` python module
* `TODO.md`: TODO file
* `tskitetude`: source code of this project

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
mget SMARTER-OA-OAR3-top-0.4.10.*
```

### Convert into *forward* coding

SMARTER data is stored in *illumina top*. It is possible to convert data into
forward coordinates with `plink`: This could be a more fast alternative to
`SNPconvert.py` coming from [SMARTER-database](https://github.com/cnr-ibba/SMARTER-database)
project. First, crate a TSV file with the SNP ids, the old allele codes and the
new allele codes. This could be done using this script:

```bash
python scripts/top2forward.py > data/OAR3_top2forward.csv
```
Next, you can convert the data with `plink`:

```bash
plink --chr-set 26 no-xy no-mt --allow-no-sex --bfile data/SMARTER-OA-OAR3-top-0.4.10 \
    --update-alleles data/OAR3_top2forward.csv --make-bed --out data/SMARTER-OA-OAR3-forward-0.4.10
```

## The tskit-pipeline

The proposed pipeline is supposed to work starting from the entire SMARTER
database: all the required samples are selected by the pipeline relying on
a list of samples (like the one required by the `--keep` option of `plink`).
Then there are three different approaches to genereate *TreeSequences* object
using the nextflow pipeline: the `est-sfs` approach, the `reference` approach
and the `compara` approach.

### The est-sfs approach

This approach requires to select a list of samples from the SMARTER
including the samples required to estimate ancestor alleles: the former
samples will be referred as *focal* samples, the latter *ancient*.
The two groups will be processed separately: data will be converted into VCF
and normalized against the reference sequence. Focal samples will be *phased* and
*imputed* using [Beagle](https://faculty.washington.edu/browning/beagle/b5_2.html)
before being joined with ancient samples to determine ancestor alleles
using [est-sfs](https://sourceforge.net/projects/est-usfs/) software
(see [Keightley and Jackson 2018](https://academic.oup.com/genetics/article/209/3/897/5930981)).
Then the output will be used to define *samples* and *TreeSequences*
using [tsinfer](https://tskit.dev/tsinfer/docs/stable/). Ages
will be finally estimated with [tsdate](https://tskit.dev/software/tsdate.html)

This approach was superseded by the *compara* and *reference* allele extraction,
since we are not sure that those ancient samples can be considered as ancestors
instead of just *outgroups*, since they are living in the same time frame of the
*focal* samples.

### The reference approach

This approach requires to select a list of samples from the SMARTER database,
like the `est-sfs` approach: however no ancient samples are required and the
ancestral alleles are extracted from a reference sequence.

This approach should be the reference approach against other methods, since
no assumptions are made on ancestors.

### The compara approach

Even this approach requires to select a list of samples from the SMARTER database.
In addition, you require a CSV file in which the *ancestral* alleles are stored.
This file can be generated using the `collect_compara_ancestors` script:

```bash
collect_compara_ancestors --assembly oar3 --chip_name IlluminaOvineSNP50 --output data/ancestors-OAR3-50K.csv
```

With this approach, the *ancestral* alleles are extracted from the *ensembl compara*
database, when an alignment between sheep and goat assemblies is available. This
datafile is specific to the assembly and the chip used to genotype the samples,
in this case we can call the analysis on *OAR3* for the *IlluminaOvineSNP50* (50K)
chip.

## Compare background samples with three different approaches

### Select background samples

Background samples can be selected by using the `notebooks/03-smarter_database.ipynb`
notebook: this notebook was used to select only *Ovis aries* background samples from
the SMARTER database. The output is a list of samples to be used in the pipeline
mainly by plink with the `--keep` option. In addition, three different lists
(`european_mouflon`, `sardinian_mouflon`, `spanish_mouflon`) are then created
to extract *ancestor alleles* using `est-sfs`.

### Call pipeline on background samples

Call the pipeline with `est-sfs` on background samples:

```bash
nextflow run cnr-ibba/nf-treeseq -r v0.2.1 -profile singularity -params-file config/smarter-sheeps.json -resume \
    --outdir "results-estsfs/background_samples" --with_estsfs
```

Call the pipeline using reference alleles (the outgroup samples are not used):

```bash
nextflow run cnr-ibba/nf-treeseq -r v0.2.1 -profile singularity -params-file config/smarter-sheeps.json -resume \
    --outdir "results-reference/background_samples" --reference_ancestor
```

Call the pipeline using the *compara* reference alleles (the outgroup samples are not used):

```bash
nextflow run cnr-ibba/nf-treeseq -r v0.2.1 -profile singularity -params-file config/smarter-sheeps.json -resume \
    --outdir "results-compara/background_samples" --compara_ancestor data/ancestors-OAR3-50K.csv
```
## Compare 50K samples with repetitions

In order to do a fair simulation, we need to extract all `50K` SNPs from the
SMARTER dataset: this will avoid the particular case when I extract all *HD* samples,
which will results in a *HD* subset. By extracting only the `50K` dataset, all
simulations should be comparable. Let's collect SNP names for `50K` SNPs:

```bash
python scripts/getSNPnames.py --chip_name IlluminaOvineSNP50 > data/50k_snp_ids.txt
```

Next, we can extract the `50K` dataset from the whole *forward* file using `plink`:

```bash
plink --chr-set 26 no-xy no-mt --allow-no-sex --bfile data/SMARTER-OA-OAR3-forward-0.4.10 \
    --extract data/50k_snp_ids.txt --make-bed --out data/SMARTER-OA-OAR3-forward-0.4.10-50K
```

To test the effect of the number of samples / breed when creating *TreeSequence*
objects, we select randomly `[1, 2, 5, 10, 15, 20]` breeds having each one a
number of samples between 20 and 30 (see `notebooks/09-smarter_50k.ipynb` for
details) and we repeat this random extraction (without repetition) 5 times.
For each combination, a input file is created inside `data` folder, and the pipeline
can be called called with:

```bash
bash scripts/50K_simulations_reference.sh
```
To call the pipeline using the *reference* approach. In order to call the pipeline
with the *compara* approach, you can use the following script:

```bash
bash scripts/50K_simulations_compara.sh
```

The `est-sfs` approach is not used in this case, since we cannot define the
output groups that can be used to estimate the *ancestral* alleles.
