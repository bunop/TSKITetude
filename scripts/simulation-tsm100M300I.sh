#!/bin/bash
#SBATCH --job-name=simulation-tsm100M300I                       # Job name
#SBATCH --ntasks=1                                              # Run on a single task
#SBATCH --cpus-per-task=16                                      # Declare 4 CPUs per task
#SBATCH --mem=32gb                                              # Job memory request
#SBATCH --output=simulation-tsm100M300I.log                     # Standard output and error log
#SBATCH --chdir=/home/core/TSKITetude/data/sheepTSsimMilano     # working directory

poetry run create_tstree --vcf tsm100M300I.vcf.gz --focal tsm100M300I.sample_names_fid.csv \
    --ancestral_as_reference --output_samples tsm100M300I.inferred.samples \
    --output_trees tsm100M300I.inferred.trees --num_threads ${SLURM_CPUS_PER_TASK} \
    --mutation_rate 5.87e-9 --ne 34500
