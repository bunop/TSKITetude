
process ESTSFS_INPUT {
    tag "$meta.id"
    label 'process_single'

    input:
    tuple val(meta), path(vcf)
    path(sample_file)
    path(outgroup_files)

    output:
    tuple val(meta), path("*.txt"), emit: estsfs_input

    when:
    task.ext.when == null || task.ext.when

    script:
    def prefix = task.ext.prefix ?: "${meta.id}"
    def outgroup_opts = outgroup_files.join('--outgroup ')
    """
    make_est_sfs_input \\
        --vcf ${vcf} \\
        --focal ${sample_file} \\
        --outgroup ${outgroup_opts} \\
        > ${prefix}.txt
    """
}
