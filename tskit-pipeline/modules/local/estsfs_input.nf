
process ESTSFS_INPUT {
    tag "$meta.id"
    label 'process_single'

    input:
    tuple val(meta), path(vcf_focal)
    tuple val(meta), path(tbi_focal)
    path(outgroup_files)

    when:
    task.ext.when == null || task.ext.when

    script:
    def prefix = task.ext.prefix ?: "${meta.id}"
    """
    echo ${vcf_focal} : ${outgroup_files}
    """
}
