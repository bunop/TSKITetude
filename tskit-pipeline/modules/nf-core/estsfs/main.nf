process ESTSFS {
    tag "$meta.id"
    label 'process_low'

    // WARN: Version information not provided by tool on CLI. Please update version string below when bumping container versions.

    input:
    tuple val(meta), path(e_config), path(data)

    output:
    tuple val(meta), path("${prefix}_sfs.txt")   ,  emit: sfs_out
    tuple val(meta), path("${prefix}_pvalues.txt"), emit: pvalues_out
    tuple val(meta), path("${prefix}.seed"),        emit: seed
    path "versions.yml", emit: versions

    when:
    task.ext.when == null || task.ext.when

    script:
    def args = task.ext.args ?: ''
    def VERSION = '2.05' // WARN: Version information not provided by tool on CLI. Please update this string when bumping container versions.
    prefix = task.ext.prefix ?: "${meta.id}"
    """
    est-sfs ${e_config} ${data} ${prefix}.seed ${prefix}_sfs.txt ${prefix}_pvalues.txt

    cat <<-END_VERSIONS > versions.yml
    "${task.process}":
        est-sfs: $VERSION
    END_VERSIONS
    """

    stub:
    def args = task.ext.args ?: ''
    def prefix = task.ext.prefix ?: "${meta.id}"
    """
    touch ${prefix}_sfs.txt
    touch ${prefix}_pvalues.txt
    touch ${prefix}.seed

    cat <<-END_VERSIONS > versions.yml
    "${task.process}":
        est-sfs: $VERSION
    END_VERSIONS
    """
}
