
process TSINFER {
    tag "$meta.id"
    label 'process_medium'

    container "docker.io/bunop/tskitetude:0.2.1"

    input:
    tuple val(meta), path(vcf)
    tuple val(meta2), path(ancestral)
    path(sample_file)

    output:
    tuple val(meta), path("*.samples"),     emit: samples
    tuple val(meta), path("*.trees"),       emit: trees

    when:
    task.ext.when == null || task.ext.when

    script:
    def prefix = task.ext.prefix ?: "${meta.id}"
    def args = task.ext.args ?: ''
    """
    create_tstree \\
        --vcf ${vcf} \\
        --focal ${sample_file} \\
        --ancestral ${ancestral} \\
        --output_samples ${prefix}.samples \\
        --output_trees ${prefix}.trees \\
        --num_threads $task.cpus \\
        $args
    """
}
