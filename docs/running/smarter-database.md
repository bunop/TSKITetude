# The SMARTER-database

The [SMARTER-database](https://smarter-database.readthedocs.io/en/latest/)
is a collection of tools and scripts to standardize genomic
data and metadata mainly from SNP chips arrays on global small ruminant populations
with a focus on reproducibility. It harmonizes genotype data for approximately
12,000 sheep and 6,000 goats to a uniform coding and assembly version. The database
is designed to be easily accessible and user-friendly, and it is intended to be
used by researchers and breeders to facilitate the sharing of data and to enable
comparative analyses across different populations.

Genotype data can be collected through anonymous FTP, while metadata can be
accessed through [SMARTER-backend REST API](https://webserver.ibba.cnr.it/smarter-api/docs/).

## Collect data through FTP

We can collect genotype data from the SMARTER-database through anonymous FTP,
for example by using [lftp](https://lftp.yar.ru/):

```text
$ cd data/
$ lftp webserver.ibba.cnr.it
lftp> cd smarter/SHEEP/OAR3/
lftp> ls
lftp> mget SMARTER-OA-OAR3-top-0.4.10
lftp> exit
md5sum -c SMARTER-OA-OAR3-top-0.4.10.md5
unzip -d SMARTER-OA-OAR3-top-0.4.10.zip
cd ..
```

Or by using `wget` or `curl`, for example:

```bash
wget ftp://webserver.ibba.cnr.it/smarter/SHEEP/OAR3/SMARTER-OA-OAR3-top-0.4.10.zip
wget ftp://webserver.ibba.cnr.it/smarter/SHEEP/OAR3/SMARTER-OA-OAR3-top-0.4.10.md5
md5sum -c SMARTER-OA-OAR3-top-0.4.10.md5
unzip -d SMARTER-OA-OAR3-top-0.4.10.zip
```

## Convert data into *Illumina forward*

Data is stored in *Illumina TOP* format: to convert data into a valid `.vcf` file,
you need to transform coordinates into *Illumina forward*: the easiest way to do
it is by using `plink`, however we need to retrieve variant information from the
REST API. We can do this easily using a Python script:

```bash
poetry run python scripts/top2forward.py > data/OAR3_top2forward.csv
```

The previous script will generate an input file that can be used to convert data with `plink`:

```bash
plink --chr-set 26 no-xy no-mt --allow-no-sex --bfile data/SMARTER-OA-OAR3-top-0.4.10 \
    --update-alleles data/OAR3_top2forward.csv --make-bed --out data/SMARTER-OA-OAR3-forward-0.4.10
```

## Convert data into *VCF*

To have a valid `.vcf` file, you can use `plink` to convert data into a `.vcf` file:
you should strat from the *Illumina forward* data, however you will need to fix
ALT/REF alleles, since `plink` does not provide this information. Ideally, we can
use [bcftools norm](https://samtools.github.io/bcftools/bcftools.html#norm) to
fix alleles, and then adjust the chromosome sizes in the header with
[bcftools reheader](https://samtools.github.io/bcftools/bcftools.html#reheader). First, convert
PLINK data into a `.vcf` file:

```bash
plink --chr-set 26 no-xy no-mt --allow-no-sex --bfile data/SMARTER-OA-OAR3-forward-0.4.10 \
    --recode bgz vcf-iid --out data/SMARTER-OA-OAR3-forward-0.4.10 --threads 4 --not-chr 0
```

I's important that chromosome 0 is removed from the `.vcf` file, since it has no
positions. Next, we can fix alleles and adjust the chromosome sizes:

```bash
bcftools norm --fasta-ref Oar_v3.1_genome.fna.gz --output SMARTER-OA-OAR3-forward-0.4.10.norm.vcf.gz \
    --check-ref ws --do-not-normalize --rm-dup all --output-type z \
    --threads 4 SMARTER-OA-OAR3-forward-0.4.10.vcf.gz
bcftools reheader --fai Oar_v3.1_genome.fna.gz.fai --threads 2 SMARTER-OA-OAR3-forward-0.4.10.norm.vcf.gz \
    | bcftools view --output-type z --output SMARTER-OA-OAR3-forward-0.4.10.norm.reheader.vcf.gz
```
