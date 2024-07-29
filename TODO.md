# TODO

## 2024-07-15

- [ ] call the *reference* pipeline on smarter background sheep
- [ ] call the *compara* pipeline on smarter background sheep
- [ ] call the *est-sfs* pipeline on smarter background sheep
- [ ] same stuff as above but with all 50k samples from smarter
- [ ] compare the three different approaches and check if the dataset dimension
      is implied in *trees* size and number of *mutations*.
- [ ] update `README.md`

## Phasing

* [Phasing WIKI](https://isogg.org/wiki/Phasing)
* Phasing with [shapeit5](https://odelaneau.github.io/shapeit5/)
* [Phasing comparison](https://www.ncbi.nlm.nih.gov/pmc/articles/PMC1380287/)
* [trioPhaser](https://github.com/dmiller903/trioPhaser)
* [trioPhaser paper](https://bmcbioinformatics.biomedcentral.com/articles/10.1186/s12859-021-04470-4)
* Beagle (currently used)

## Ancestral sequences

* [tskit discussion](https://github.com/tskit-dev/tsinfer/discussions/523)
* [paper ancestral](https://academic.oup.com/genetics/article/209/3/897/5930981?login=false)
* [est-sfs](https://sourceforge.net/projects/est-usfs/) software for determining
  ancestral allele (used in Keightley and Jackson 2018 - Inferring the Probability
  of the Derived vs. the Ancestral Allelic State at a Polymorphic Site)
* [ts-date](https://tskit.dev/software/tsdate.html) estimate age of ancestral node
* collect ancestral alleles from *ensembl compara* (see
  [ancestral sequences](https://www.ensembl.org/info/genome/compara/ancestral_sequences.html))

## Pipeline hypothesis

* Collect public sample genotypes from SMARTER. Include ancient samples.
* Attempt to phase genotypes
* Develop a custom script to create a *tsinfer data object* specifying samples
  with ancient reference allele (should ancient sample be removed?)
* Create a `tstree` object
* Use `ts-date`
* Use [tszip](https://pypi.org/project/tszip/)

## Comparing

* [TileDB-VCF](https://docs.tiledb.com/main/integrations-and-extensions/genomics/population-genomics)
