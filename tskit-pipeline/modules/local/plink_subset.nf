process PLINK_SUBSET {
    tag "$meta.id"
    label 'process_low'

    conda "bioconda::plink=1.90b6.21"
    container "${ workflow.containerEngine == 'singularity' && !task.ext.singularity_pull_docker_container ?
        'https://depot.galaxyproject.org/singularity/plink:1.90b6.21--h779adbc_1':
        'biocontainers/plink:1.90b6.21--h779adbc_1' }"

    input:
    tuple val(meta), path(bed), path(bim), path(fam)
    path(samples)

    output:
    tuple val(meta), path("*.bed"), emit: bed
    tuple val(meta), path("*.bim"), emit: bim
    tuple val(meta), path("*.fam"), emit: fam
    path "versions.yml"           , emit: versions

    when:
    task.ext.when == null || task.ext.when

    script:
    def args = task.ext.args ?: ''
    def prefix = task.ext.prefix ?: "${meta.id}"
    def bfile = "${bed.getBaseName()}"
    def species_opt = "${params.plink_species}"
    if( "$bed" == "${prefix}.bed" ) error "Input and output names are the same, use \"task.ext.prefix\" to disambiguate!"
    """
    plink \\
        ${species_opt} \\
        --bfile ${bfile} \\
        --threads $task.cpus \\
        $args \\
        --keep ${samples} \\
        --make-bed \\
        --out $prefix
    cat <<-END_VERSIONS > versions.yml
    "${task.process}":
        plink: \$(echo \$(plink --version) | sed 's/^PLINK v//;s/64.*//')
    END_VERSIONS
    """

    stub:
    def prefix = task.ext.prefix ?: "${meta.id}"
    """
    touch ${prefix}.bed
    touch ${prefix}.bim
    touch ${prefix}.fam
    touch versions.yml
    """
}
