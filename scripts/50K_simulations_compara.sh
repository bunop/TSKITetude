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
        nextflow run cnr-ibba/nf-treeseq -r v0.2.1 -profile singularity -params-file config/50K_simulations.json -resume \
            --plink_keep $plink_keep --outdir "results-compara/50K_simulations/${size}_breeds-${i}-50K" --compara_ancestor "data/ancestors-OAR3-50K.csv"
    done
done
