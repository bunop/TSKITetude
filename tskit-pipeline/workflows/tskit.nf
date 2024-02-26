/*
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    PRINT PARAMS SUMMARY
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
*/

include { paramsSummaryLog; paramsSummaryMap } from 'plugin/nf-validation'

def logo = NfcoreTemplate.logo(workflow, params.monochrome_logs)
def citation = '\n' + WorkflowMain.citation(workflow) + '\n'
def summary_params = paramsSummaryMap(workflow)

// Print parameter summary log to screen
log.info logo + paramsSummaryLog(workflow) + citation

/*
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    VALIDATE INPUTS
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
*/

WorkflowTskit.initialise(params, log)

/*
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    CONFIG FILES
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
*/

// ch_multiqc_config          = Channel.fromPath("$projectDir/assets/multiqc_config.yml", checkIfExists: true)
// ch_multiqc_custom_config   = params.multiqc_config ? Channel.fromPath( params.multiqc_config, checkIfExists: true ) : Channel.empty()
// ch_multiqc_logo            = params.multiqc_logo   ? Channel.fromPath( params.multiqc_logo, checkIfExists: true ) : Channel.empty()
// ch_multiqc_custom_methods_description = params.multiqc_methods_description ? file(params.multiqc_methods_description, checkIfExists: true) : file("$projectDir/assets/methods_description_template.yml", checkIfExists: true)

/*
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    IMPORT LOCAL MODULES/SUBWORKFLOWS
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
*/

//
// SUBWORKFLOW: Consisting of a mix of local and nf-core/modules
//
// include { INPUT_CHECK } from '../subworkflows/local/input_check'

/*
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    IMPORT NF-CORE MODULES/SUBWORKFLOWS
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
*/

//
// MODULE: Installed directly from nf-core/modules
//
include {
    PLINK_SUBSET as FOCAL_SUBSET;
    PLINK_SUBSET as ANCIENT_SUBSET          } from '../modules/local/plink_subset.nf'
include {
    PLINK_RECODE as FOCAL_RECODE;
    PLINK_RECODE as ANCIENT_RECODE          } from '../modules/nf-core/plink/recode/main'
include {
    BCFTOOLS_NORM as FOCAL_NORM;
    BCFTOOLS_NORM as ANCIENT_NORM           } from '../modules/nf-core/bcftools/norm/main'
include {
    BCFTOOLS_SPLIT as FOCAL_SPLIT;
    BCFTOOLS_SPLIT as ANCIENT_SPLIT         } from '../modules/nf-core/bcftools/split/main'
include { BEAGLE5_BEAGLE as FOCAL_BEAGLE    } from '../modules/nf-core/beagle5/beagle/main'
include { SAMTOOLS_FAIDX                    } from '../modules/nf-core/samtools/faidx/main'
include { BCFTOOLS_REHEADER                 } from '../modules/nf-core/bcftools/reheader/main'
include {
    TABIX_TABIX as FOCAL_TABIX;
    TABIX_TABIX as ANCIENT_TABIX;
    TABIX_TABIX as REHEADER_TABIX;
    TABIX_TABIX as ANCIENT_SPLIT_TABIX      } from '../modules/nf-core/tabix/tabix/main'
include { BCFTOOLS_MERGE                    } from '../modules/nf-core/bcftools/merge/main'
include { ESTSFS_INPUT                      } from '../modules/local/estsfs_input'
include { ESTSFS                            } from '../modules/cnr-ibba/estsfs/main'
include { ESTSFS_OUTPUT                     } from '../modules/local/estsfs_output'
include { TSINFER                           } from '../modules/local/tsinfer'
include { CUSTOM_DUMPSOFTWAREVERSIONS       } from '../modules/nf-core/custom/dumpsoftwareversions/main'

/*
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    RUN MAIN WORKFLOW
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
*/

// Info required for completion email and summary
def multiqc_report = []


process GENERATE_SEED {
    output:
    path 'seedfile.txt'

    '''
    echo $RANDOM > seedfile.txt
    '''
}


workflow TSKIT {
    ch_versions = Channel.empty()

    // getting plink input files
    bed =  Channel.fromPath( "${params.plink_bfile}.bed" )
    bim =  Channel.fromPath( "${params.plink_bfile}.bim" )
    fam =  Channel.fromPath( "${params.plink_bfile}.fam" )

    focal_input_ch = bed.concat(bim, fam)
        .collect()
        .map{ it -> [[ id: "${it[0].getBaseName(1)}.focal" ], it[0], it[1], it[2]] }
        // .view()

    // getting focal samples to keep
    samples_ch = Channel.fromPath( params.plink_keep, checkIfExists: true )

    // extract the samples I want. See modules.confing for other options
    FOCAL_SUBSET(focal_input_ch, samples_ch)
    ch_versions = ch_versions.mix(FOCAL_SUBSET.out.versions)

    // collect the outgroup sample list files. At least one outgroup
    outgroup1 = Channel.fromPath( params.outgroup1, checkIfExists: true)
    outgroup2 = params.outgroup2 ? Channel.fromPath(params.outgroup2, checkIfExists: true): Channel.empty()
    outgroup3 = params.outgroup3 ? Channel.fromPath(params.outgroup3, checkIfExists: true): Channel.empty()
    outgroup_files_ch = outgroup1
        .concat(outgroup2)
        .concat(outgroup3)
    outgroups_ch = outgroup_files_ch
        .splitCsv(header: ["breed", "sample_id"], sep: "\t", strip: true)
        .map{ it -> "${it.breed}\t${it.sample_id}" }
        .collectFile(name: 'outgroups.txt', newLine: true)
        // .view()

    ancient_input_ch = focal_input_ch
        .map{ meta, bed, bim, fam -> [[id: "${bed.getBaseName(1)}.ancient"], bed, bim, fam] }
        // .view()

    // extract the ancient samples
    ANCIENT_SUBSET(ancient_input_ch, outgroups_ch)
    ch_versions = ch_versions.mix(ANCIENT_SUBSET.out.versions)

    // transform the plink files to vcf
    FOCAL_RECODE(FOCAL_SUBSET.out.bed.join(FOCAL_SUBSET.out.bim).join(FOCAL_SUBSET.out.fam))
    ch_versions = ch_versions.mix(FOCAL_RECODE.out.versions)

    // transform the plink files to vcf
    ANCIENT_RECODE(ANCIENT_SUBSET.out.bed.join(ANCIENT_SUBSET.out.bim).join(ANCIENT_SUBSET.out.fam))
    ch_versions = ch_versions.mix(ANCIENT_RECODE.out.versions)

    // need to define a genome channel
    genome_ch = Channel.fromPath(params.genome, checkIfExists: true)
        .map{ it -> [[ id: "${it.getBaseName()}" ], it]}
        // .view()

    // Normalize focal VCF
    FOCAL_NORM(
        FOCAL_RECODE.out.vcfgz.map{ meta, vcf -> [meta, vcf, []] },
        genome_ch
    )
    ch_versions = ch_versions.mix(FOCAL_NORM.out.versions)

    // Normalize ancient VCF
    ANCIENT_NORM(
        // the third element of the input channel is a tbi
        ANCIENT_RECODE.out.vcfgz.map{ meta, vcf -> [meta, vcf, []] },
        genome_ch
    )
    ch_versions = ch_versions.mix(ANCIENT_NORM.out.versions)

    // index focal vcf
    FOCAL_TABIX(FOCAL_NORM.out.vcf)
    ch_versions = ch_versions.mix(FOCAL_TABIX.out.versions)

    // index ancient vcf
    ANCIENT_TABIX(ANCIENT_NORM.out.vcf)
    ch_versions = ch_versions.mix(ANCIENT_TABIX.out.versions)

    // split data by chromosomes for focal
    FOCAL_SPLIT(FOCAL_NORM.out.vcf.join(FOCAL_TABIX.out.tbi))
    ch_versions = ch_versions.mix(FOCAL_SPLIT.out.versions)

    // split data by chromosomes for ancestor
    ANCIENT_SPLIT(ANCIENT_NORM.out.vcf.join(ANCIENT_TABIX.out.tbi))
    ch_versions = ch_versions.mix(ANCIENT_SPLIT.out.versions)

    // index the splitted ancestor
    ANCIENT_SPLIT_TABIX(ANCIENT_SPLIT.out.split_vcf.transpose())
    ch_versions = ch_versions.mix(ANCIENT_SPLIT_TABIX.out.versions)

    // get the chromosome name from the vcf file name
    beagle_in_ch = FOCAL_SPLIT.out.split_vcf
        .transpose()
        .map{ meta, vcf ->
            chrom = vcf.name.tokenize(".")[-3]
            [[id: "${meta.id}.${chrom}", chrom: chrom], vcf]
        }
        // .view()

    // phase and inpute with beagle5
    FOCAL_BEAGLE(beagle_in_ch, [], [], [], [])
    ch_versions = ch_versions.mix(FOCAL_BEAGLE.out.versions)

    // index genome sequence
    SAMTOOLS_FAIDX(genome_ch, [[], []])
    ch_versions = ch_versions.mix(SAMTOOLS_FAIDX.out.versions)

    // when I have two queues of different size, I can use the first() method
    // to transform the queue in a value channel
    // https://training.nextflow.io/basic_training/channels/#value-channels
    BCFTOOLS_REHEADER(
        FOCAL_BEAGLE.out.vcf.map{ meta, vcf -> [meta, vcf, [], []] },
        SAMTOOLS_FAIDX.out.fai.first()
    )
    ch_versions = ch_versions.mix(BCFTOOLS_REHEADER.out.versions)

    // index beagle genotype
    REHEADER_TABIX(BCFTOOLS_REHEADER.out.vcf)
    ch_versions = ch_versions.mix(FOCAL_TABIX.out.versions)

    // merge the ancient and focal vcf
    vcf_ch = BCFTOOLS_REHEADER.out.vcf
        .map{ meta, it -> [[id: "samples-merged.${meta.chrom}"], it] }
        .concat(
            ANCIENT_SPLIT.out.split_vcf
                .transpose()
                .map{ meta, vcf ->
                    chrom = vcf.name.tokenize(".")[-3]
                    [[id: "samples-merged.${chrom}"], vcf]
                }
        )
        .groupTuple()
        // .view()

    // merge the ancient and focal tbi
    tbi_ch = REHEADER_TABIX.out.tbi
        .map{ meta, it -> [[id: "samples-merged.${meta.chrom}"], it] }
        .concat(
            ANCIENT_SPLIT_TABIX.out.tbi
                .map{ meta, tbi ->
                    chrom = tbi.name.tokenize(".")[-4]
                    [[id: "samples-merged.${chrom}"], tbi]
                }
        )
        .groupTuple()
        // .view()

    bcftools_input_ch = vcf_ch.join(tbi_ch)
        // .view()

    BCFTOOLS_MERGE(bcftools_input_ch, [[], []], [[], []], [])
    ch_versions = ch_versions.mix(BCFTOOLS_MERGE.out.versions)

    // calculate ancestral alleles. I need to use the first() method to transform
    // the queue in a value channel
    ESTSFS_INPUT(
        BCFTOOLS_MERGE.out.merged_variants,
        samples_ch.first(),
        outgroup_files_ch.collect()
    )

    // determine a seedfile
    seedfile = GENERATE_SEED()

    // call custom est-sfs
    ESTSFS(
        ESTSFS_INPUT.out.config
            .join(ESTSFS_INPUT.out.input)
            .combine(seedfile)
    )
    ch_versions = ch_versions.mix(ESTSFS.out.versions)

    ESTSFS_OUTPUT(ESTSFS_INPUT.out.mapping.join(ESTSFS.out.pvalues_out))

    tsinfer_in_ch = BCFTOOLS_REHEADER.out.vcf
        .map{ meta, vcf -> [meta.chrom, meta, vcf] }
        .join(
            ESTSFS_OUTPUT.out.ancestral
                .map{ meta, ancestral ->
                        chrom = ancestral.name.tokenize(".")[-3]
                        [chrom, ancestral]
                },
            by: [0],
            failOnMismatch: true
        ).map{ chrom, meta, vcf, ancestral -> [[id: meta.id], vcf, ancestral]}
        // .view()

    // now create a tstree file
    TSINFER(
        tsinfer_in_ch,
        samples_ch.first()
    )

    CUSTOM_DUMPSOFTWAREVERSIONS (
        ch_versions.unique().collectFile(name: 'collated_versions.yml')
    )

    //
    // MODULE: MultiQC
    //
    // workflow_summary    = WorkflowTskit.paramsSummaryMultiqc(workflow, summary_params)
    // ch_workflow_summary = Channel.value(workflow_summary)

    // methods_description    = WorkflowTskit.methodsDescriptionText(workflow, ch_multiqc_custom_methods_description, params)
    // ch_methods_description = Channel.value(methods_description)

    // ch_multiqc_files = Channel.empty()
    // ch_multiqc_files = ch_multiqc_files.mix(ch_workflow_summary.collectFile(name: 'workflow_summary_mqc.yaml'))
    // ch_multiqc_files = ch_multiqc_files.mix(ch_methods_description.collectFile(name: 'methods_description_mqc.yaml'))
    // ch_multiqc_files = ch_multiqc_files.mix(CUSTOM_DUMPSOFTWAREVERSIONS.out.mqc_yml.collect())

    // MULTIQC (
    //     ch_multiqc_files.collect(),
    //     ch_multiqc_config.toList(),
    //     ch_multiqc_custom_config.toList(),
    //     ch_multiqc_logo.toList()
    // )
    // multiqc_report = MULTIQC.out.report.toList()
}

/*
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    COMPLETION EMAIL AND SUMMARY
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
*/

workflow.onComplete {
    if (params.email || params.email_on_fail) {
        NfcoreTemplate.email(workflow, params, summary_params, projectDir, log, multiqc_report)
    }
    NfcoreTemplate.dump_parameters(workflow, params)
    NfcoreTemplate.summary(workflow, params, log)
    if (params.hook_url) {
        NfcoreTemplate.IM_notification(workflow, params, summary_params, projectDir, log)
    }
}

/*
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    THE END
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
*/
