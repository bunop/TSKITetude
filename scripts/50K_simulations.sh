#!/bin/bash
set -euxo pipefail

# define some variables
BREED_SIZES=(1 2 5 10 15 20)
REPEATS=5

# turn of nextflow console logging
export NXF_OFFLINE='true'
export NXF_ANSI_LOG='false'

for size in "${BREED_SIZES[@]}"; do
    for ((i=0; i<REPEATS; i++)); do
        echo "Running simulation for ${size} breeds, repeat ${i}"
        plink_keep="data/${size}_breeds-${i}-50K.csv"
        nextflow run cnr-ibba/nf-treeseq -r issue-6 -profile singularity -params-file config/50K_simulations.json -resume \
            --plink_keep $plink_keep --outdir "results-reference/50K_simulations/${size}_breeds-${i}-50K" --reference_ancestor
    done
done
