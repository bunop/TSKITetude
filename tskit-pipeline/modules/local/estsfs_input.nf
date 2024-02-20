
process ESTSFS_INPUT {
    tag "$meta.id"
    label 'process_single'

    input:
    tuple val(meta), path(vcf)
    path(sample_file)
    path(outgroup_files)

    output:
    tuple val(meta), path("*.txt"),     emit: input
    tuple val(meta), path("*.config"),  emit: config
    tuple val(meta), path("*.mapping"), emit: mapping

    when:
    task.ext.when == null || task.ext.when

    script:
    def prefix = task.ext.prefix ?: "${meta.id}"
    def outgroup_opts = outgroup_files.join('--outgroup ')
    def model = "${params.estsfs_model}"
    def nrandom = "${params.estsfs_nrandom}"
    """
    make_est_sfs_input \\
        --vcf ${vcf} \\
        --focal ${sample_file} \\
        --outgroup ${outgroup_opts} \\
        --output_data ${prefix}.txt \\
        --output_config ${prefix}.config \\
        --output_mapping ${prefix}.mapping \\
        --model ${model} \\
        --nrandom ${nrandom}
    """
}
