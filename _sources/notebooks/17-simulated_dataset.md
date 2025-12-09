# Dataset for TS inference

Diploid, phased VCF files with varying numbers of individuals. All are BGZIP-compressed and have a CSI index. A key to the populations is in the file `popKey`.

These are for TS inference with SINGER, threads, and tskinfer/tsdate. For each file, the REF allele can be assumed to be ancestral. The imputed files with Maj in their name have the REF allele set to the major allele. This is to assess the effect of wrongly specified ancestral alleles.

- **Complete VCF**
  - `tsm100M300I.vcf.gz` (exported from msprime with ref allele = ancestral)
- **Array-density files**
  - `ts300I2k.vcf.gz`
  - `ts300I25k.vcf.gz`
- **Imputed datasets for TS inference**
  - `panelLarge25kImputed.vcf.gz`
  - `panelLarge25kMajImputed.vcf.gz`
  - `panelLarge2kImputed.vcf.gz`
  - `panelLarge2kMajImputed.vcf.gz`
  - `panelNoBLarge25kImputed.vcf.gz`
  - `panelNoBLarge25kMajImputed.vcf.gz`
  - `panelNoBLarge2kImputed.vcf.gz`
  - `panelNoBLarge2kMajImputed.vcf.gz`
  - `panelSmall25kImputed.vcf.gz`
  - `panelSmall25kMajImputed.vcf.gz`
  - `panelSmall2kImputed.vcf.gz`
  - `panelSmall2kMajImputed.vcf.gz`
  - `panelNoBSmall25kImputed.vcf.gz`
  - `panelNoBSmall25kMajImputed.vcf.gz`
  - `panelNoBSmall2kImputed.vcf.gz`
  - `panelNoBSmall2kMajImputed.vcf.gz`

## Fix file names

Files have been downloaded and extracted in `data/toInfer/` folder: there's a
repetition of "vcf" in the file names. You can fix this by creating a simple script
like this in the `data/toInfer/` folder:

```bash
#!/bin/bash
# replace .vcf.vcf extensions with .vcf
# ex. panelLarge25kImputed.vcf.vcf.gz -> panelLarge25kImputed.vcf.gz
set -euo pipefail

for file in $(ls *.vcf.vcf.*); do
    newname=$(echo "$file" | sed 's/\.vcf\.vcf/\.vcf/')
    mv "$file" "$newname"
done
```

Make the script executable with `chmod +x fix_filenames.sh` and run it with
`./fix_filenames.sh`.

## Create a TSV file with sample information

Those files are a simulation of 1600 individuals from the original 2405 individuals
in the msprime simulation. We need to create a TSV file with sample information
using `FID` and `IID` columns: you can create it with an utility script in this
folder:

```bash
python scripts/createFID-IID.py \
    --indiv-list data/toInfer/popKey \
    --directory data/toInfer
```

## Create a fake FASTA file

We need to create a fake FASTA in order to exploit `bcftools reheader` to add
contig length information to the VCF files: this is required by `create_tstree`
script installed in this project (and to be used by the <https://github.com/cnr-ibba/nf-treeseq>
Nextflow pipeline). This can be done again with an utility script in this folder:

```bash
python scripts/fakeFastaFromVCF.py \
    --vcf data/toInfer/tsm100M300I.vcf.gz \
    --output data/toInfer/tsm100M300I.fa.gz
```

## Call nextflow pipeline (tskit reference approach)

You can create two nextflow configuration files for running the `cnr-ibba/nf-treeseq`
pipeline: see `config/samples_toInfer.csv` and `config/samples_toInfer-reference.json` to
see how to set it up. Then you can call the pipeline with:

```bash
nextflow run cnr-ibba/nf-treeseq -r dev \
    -profile ibba,core -resume \
    -params-file config/samples_toInfer-reference.json
```

## Call nextflow pipeline (threads approach)

You need also two configuration files for running the `cnr-ibba/nf-treeseq`
pipeline, the `config/samples_toInfer.csv` file is the same as before, but you
need to create a new JSON configuration file: see `config/samples_toInfer-threads.json` to
see how to set it up. You need also a demography file with two columns, one for
generation and one for population size: for simplicity will will use a value for
all generations (see `config/samples_toInfer.demo`). You can call the pipeline with:

```bash
nextflow run cnr-ibba/nf-treeseq -r dev \
    -profile ibba,core -resume \
    -params-file config/samples_toInfer-threads.json
```

## Call nextflow pipeline (threads with fit to data)

You need to create another JSON configuration file for running the `cnr-ibba/nf-treeseq`
pipeline with threads and fit to data option enabled:
see `config/samples_toInfer-threads-fit.json` to
see how to set it up. You can call the pipeline with:

```bash
nextflow run cnr-ibba/nf-treeseq -r dev \
    -profile ibba,core -resume -c config/custom.config \
    -params-file config/samples_toInfer-threads-fit.json
```
