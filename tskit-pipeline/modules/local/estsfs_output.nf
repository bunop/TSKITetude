
process ESTSFS_OUTPUT {
    tag "$meta.id"
    label 'process_single'

    input:
    tuple val(meta), path(mapping), path(pvalues)

    // output:
    // tuple val(meta), path("*.txt"),     emit: input
    // tuple val(meta), path("*.config"),  emit: config
    // tuple val(meta), path("*.mapping"), emit: mapping

    when:
    task.ext.when == null || task.ext.when

    script:
    def prefix = task.ext.prefix ?: "${meta.id}"
    """
    parse_est_sfs_output \\
        --mapping ${mapping} \\
        --pvalues ${pvalues}
    """
}
