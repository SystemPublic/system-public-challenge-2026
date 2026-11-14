======================================================================
MalariaGEN Pf8 data release
======================================================================

Date: 2025-02-14


======================================================================
Description
======================================================================

The Pf8 data release includes 33,325 parasite samples collected in 34 different countries in Africa, Asia, South America and Oceania. From these, 24,409 are high-quality samples with complete metadata. In total, we identified more than 12 million variant positions (SNPs and indels). 

This download includes metadata, genotyping data and drug-resistance inference for samples contributed to MalariaGEN. We include both a full genetic callset (single nucleotide polymorphisms (SNPs) and indel variants) and a SNP-only callset. To encourage specialised analyses, we additionally include the genetic distance matrix (full and SNP-only versions), measures of sample clonality (Fws), copy number variation (CNV) calls, and drug resistance inferences and rules files. Sequence alignment and genomic variant files (CRAM, gVCF, and VCF) are also included.

These data are available open access under the terms of the Creative Commons Attribution 4.0 International license (CC-BY 4.0). Publications using these data should acknowledge and cite the source of the data.

For more information on MalariaGEN P. falciparum projects, please visit: https://www.malariagen.net/parasite-observatory/

The methods used to generate the data are described in detail in "Pf8: an open dataset of Plasmodium falciparum genome variation in 33,325 worldwide samples", MalariaGEN et al., 2025, DOI: 10.12688/wellcomeopenres.24031.1


======================================================================
Citation information
======================================================================

Publications using these data should acknowledge and cite the source of the data using the following format: "This publication uses data from MalariaGEN as described in 'Pf8: An open dataset of Plasmodium falciparum genome variation in 33,325 worldwide samples', MalariaGEN et al., Wellcome Open Research, 2025; 10: 325 DOI: 10.12688/wellcomeopenres.24031.1"


======================================================================
Files in the release
======================================================================

Files in the release include:

    - metadata/Pf8_samples.txt : sample metadata file in tab-delimited format
    - Pf8_fws.tsv : Fws values in tab-delimited format
    - Pf8_mean_genotype_distance.npy: genetic distance matrix in numpy format
    - Pf8_cnv_calls.tsv: copy number variation calls in tab-delimited format
    - cnv-diagnostic-plots/: directory containing diagnostic plots of CNV regions for all samples in .png format
    - Pf8_tandem_duplication_breakpoints.tsv: breakpoint pairs used in tandem duplication CNV calling in tab-delimited format
    - Pf8_drug_resistance_marker_genotypes.tsv : drug resistance marker genotypes file in tab-delimited format
    - Pf8_inferred_resistance_status_classification.tsv : inferred resistance status classification file in tab-delimited format
    - Pf8_resistance_classification.pdf : rules used to create Pf_8_inferred_resistance_status_classification.tsv in PDF format
    - Pf8.zarr.zip : sample genotypes (SNP and indels) in zipped zarr format
    - reference/Pfalciparum.genome.fasta: a FASTA 3D7 reference file created from PlasmoDB's release 54
    - annotations/PlasmoDB-55_Pfalciparum3D7.gff.gz: a gzipped GFF file created from PlasmoDB's release 55
    - vcf/: directory containing VCF files with SNP and non-SNP variants, one per chromosome
    - cram/: directory containing compressed mapped genomic sequencing read data for all Pf8 samples
    - gvcf/: outputs of GATK HaplotypeCaller that be used for joint genotyping with user’s own data
    - snp-only/vcf/: directory containing SNP-only VCF files, one per chromosome, plus VCF index files
    - snp-only/Pf8_snp_only_clean_zarr.zip: SNP-only sample genotypes, in zipped zarr format
    - snp-only/Pf8_mean_genotype_distance_snp_only.npy: genetic distance matrix generated from SNP-only callset, in numpy format



File descriptions:

======================================================================
- Pf8_samples.txt 
======================================================================

This file includes sample metadata for all 33,325 samples collected from partners and details of sequence read data available at the European Nucleotide Archive (ENA, https://www.ebi.ac.uk/ena). It contains the following columns:

    - Sample                         Unique ID of each sample (which can be used to link to other sample information and genotypes)
    - Study                          Code of the partner study which collected this sample
    - Country                        Country in which the sample was collected (in the case of returning travellers this is the country visited)
    - Admin level 1                  First Administration level in which the sample was collected
    - Country latitude               GPS coordinate of the latitude of the Country
    - Country longitude              GPS coordinate of the longitude of the Country
    - Admin level 1 latitude         GPS coordinate of the latitude of the Admin level 1
    - Admin level 1 longitude        GPS coordinate of the longitude of the Admin level 1 
    - Year                           Year in which the sample was collected
    - ENA                            ENA run accession(s) for the sequencing read data. In some cases multiple runs of sequencing data were merged
    - All samples same case    Identifies all the sample in the data set which were collected from the same individual, either at the same of different time points
    - Population                     Population to which the sample was assigned to (SA = South America, AF-W = Africa - West, AF-C = Africa - Central, AF-NE = Africa - Northeast, AF-E = Africa - East, AS-S-E = Asia - South - East, AS-S-FE = Asia - South - Far East, AS-SE-W = Asia - Southeast - West, AS-SE-E = Asia - Southeast - East, OC-NG = Oceania - New Guinea)
)
    - % callable                     Percentage of the genome which has coverage of at least 5 reads [and less than 10% of reads with mapping quality 0
    - QC pass                        Flag indicating whether the sample passed QC (True=passed QC, False=failed QC)
    - Exclusion reason               Reason samples failed QC (High_num_singletons, Low_coverage, Lower_covered_duplicate, Mixed_species, Unverified_identity). Note that for Unverified_identity samples, we do not include spatial and temporal metadata.
    - Sample type                    Amplification technology used on the sample (MDA, gDNA or sWGA)
    - Sample was in Pf7              Flag indicating whether the sample was on the previous (Pf7) release (True=in previous release, False=not in previous release i.e. new sample)


======================================================================
- Pf8_fws.tsv
======================================================================

This file includes Fws values for 24,409 samples that passed QC. It contains the following columns:

    - Sample                         Unique ID of each sample (which can be used to link to other sample information and genotypes)
    - Fws                            Fws value


======================================================================
- Pf8_mean_genotype_distance.npy
======================================================================

This file includes the genetic distances between all 33,325 sample pairs. These are included in a numpy array, which can be easily accessed via the numpy library in python (see https://numpy.org/doc/stable/reference/generated/numpy.load.html for more details) using a command such as `np.load("Pf8_mean_genotype_distance.npy")`. Samples are ordered as per the Pf8_samples.txt file. 


======================================================================
- Pf8_cnv_calls.tsv
======================================================================

This file contains copy number variation (CNV) for 6 genes: CRT, GCH1, MDR1, PM2/3, HRP2 and HRP3, for 24,409 samples that passed QC. For each gene the “final” call should be used for downstream analysis. For amplifications calls 1=amplified, 0=not amplified, -1=missing/uncallable. For deletion calls 1=deleted, 0=not deleted, -1=missing/uncallable. Details of tandem duplication breakpoints can be found in Pf8_tandem_duplication_breakpoints.tsv. The file contains the following columns:

    - Sample                         Unique ID of each sample (which can be used to link to other sample information and genotypes)
    - CRT_uncurated_coverage_only    Amplification call as output by coverage pipeline, before any manual curation, for gene CRT
    - CRT_curated_coverage_only      Amplification coverage call, after manual curation, for gene CRT
    - CRT_breakpoint                 Breakpoints of tandem duplication, identified by “faceaway” read evidence, for CRT
    - CRT_faceaway_only              Tandem duplication breakpoint call, identified by “faceaway” read evidence, for CRT
    - CRT_final_amplification_call   Final call, created by combining coverage and faceaway read evidence, for CRT
    - GCH1_uncurated_coverage_only   Amplification call output by coverage pipeline, before any manual curation, for gene GCH1
    - GCH1_curated_coverage_only     Amplification coverage call, after manual curation, for gene GCH1
    - GCH1_breakpoint                Breakpoints of tandem duplication, identified by “faceaway” read evidence, for GCH1
    - GCH1_faceaway_only             Tandem duplication breakpoint call, identified by “faceaway” read evidence, for GCH1
    - GCH1_final_amplification_call  Final call, created by combining coverage and faceaway read evidence, for GCH1
    - MDR1_uncurated_coverage_only   Amplification call as output by coverage pipeline, before any manual curation, for gene MDR1
    - MDR1_curated_coverage_only     Amplification coverage call, after manual curation, for gene MDR1
    - MDR1_breakpoint                Breakpoints of tandem duplication, identified by “faceaway” read evidence, for MDR1
    - MDR1_faceaway_only             Tandem duplication breakpoint call, identified by “faceaway” read evidence, for MDR1
    - MDR1_final_amplification_call  Final call, created by combining coverage and faceaway read evidence, for MDR1
    - PM2_PM3_uncurated_coverage_only    Amplification call as output by coverage pipeline, before any manual curation, for genes PM2 and PM3
    - PM2_PM3_curated_coverage_only      Amplification coverage call, after manual curation, for genes PM2 and PM3
    - PM2_PM3_breakpoint                 Breakpoints of tandem duplication, identified by “faceaway” read evidence, for PM2 and PM3
    - PM2_PM3_faceaway_only              Tandem duplication breakpoint call, identified by “faceaway” read evidence, for PM2 and PM3
    - PM2_PM3_final_amplification_call   Final call, created by combining coverage and faceaway read evidence, for PM2 and PM3
    - HRP2_uncurated_coverage_only   Deletion call as output by coverage pipeline, before any manual curation, for gene HRP2
    - HRP2_breakpoint                Breakpoint of deletion, identified by manual inspection of reads, for HRP2
    - HRP2_deletion_type             Type of deletion, identified by manual inspection of reads, for HRP2.
    - HRP2_final_deletion_call       Final call, after manual curation, for HRP2
    - HRP3_uncurated_coverage_only   Deletion call as output by coverage pipeline, before any manual curation, for gene HRP3
    - HRP3_breakpoint                Breakpoint of deletion, identified by manual inspection of reads, for HRP3
    - HRP3_deletion_type             Type of deletion, identified by manual inspection of reads, for HRP3
    - HRP3_final_deletion_call       Final call, after manual curation, for HRP3


======================================================================
- cnv-diagnostic-plots/
======================================================================

This directory contains six sub-directories, one for each gene. Within these sub-directories there is a diagnostic plot for each of the 24,409 samples that passed QC


======================================================================
- Pf8_tandem_duplication_breakpoints.tsv
======================================================================

Details of 65 pairs of breakpoints assessed for evidence of faceaway reads suggesting tandem duplications. Note that each row represents two breakpoints, but in most cases the exact location of each breakpoint can not be given (for example because we only know that the breakpoint is somewhere within a long homopolymer run. As such for each of the two breakpoints, we give both a start and end coordinate, so 4 coordinates in total. The file contains the following columns:

    - chrom                          Contig (chromosome) on which the breakpoints are found
    - first_breakpoint_start         Genomic coordinate of the 5’ end of the 5’ breakpoint
    - first_breakpoint_end           Genomic coordinate of the 3’ end of the 5’ breakpoint
    - second_breakpoint_start        Genomic coordinate of the 5’ end of the 3’ breakpoint
    - second_breakpoint_end          Genomic coordinate of the 3’ end of the 3’ breakpoint
    - start_gene_id                  Gene ID of gene closest to the first breakpoint. This is not populated for all rows, and is not used, so can be ignored
    - end_gene_id                    Gene ID of gene closest to the second breakpoint. This is not populated for all rows, and is not used, so can be ignored
    - breakpoint_name                A breakpoint pair name that is not used and can be ignored
    - breakpoint_id                  The is the breakpoint pair ID that is used in the breakpoint columns of the CNV calls file Pf8_cnv_calls.tsv
    - target_gene                    Target gene in which these breakpoints are used in the CNV calling pipeline
    - use                            Flag saying whether this breakpoint pair was used in the faceaway read calling (0 - not used, 1=used)
    - note                           Other notes about the breakpoint pair


======================================================================
- Pf8_drug_resistance_marker_genotypes.tsv
======================================================================

This file contains genotypes at drug resistance markers for all QC pass 24,409 samples derived from analysis of sequence data. It contains the following columns:

    - Sample                         Unique ID of each sample (which can be used to link to other sample information and genotypes)
    - crt_76[K]                      Amino acid at crt position 76. For explanation see below.
    - crt_72-76[CVMNK]               Amino acids at crt positions 72 to 76. For explanation see below.
    - dhfr_51[N]                     Amino acid at dhfr position 51. For explanation see below.
    - dhfr_59[C]                     Amino acid at dhfr position 59. For explanation see below.
    - dhfr_108[S]                    Amino acid at dhfr position 108. For explanation see below.
    - dhfr_164[I]                    Amino acid at dhfr position 164. For explanation see below.
    - dhps_437[G]                    Amino acid at dhps position 437. For explanation see below.
    - dhps_540[K]                    Amino acid at dhps position 540. For explanation see below.
    - dhps_581[A]                    Amino acid at dhps position 581. For explanation see below.
    - dhps_613[A]                    Amino acid at dhps position 613. For explanation see below.
    - kelch13_349-726_ns_changes     Non-synonymous mutations at Kelch13 positions 349-726. For explanation see below.  
    - mdr1_dup_call                  1.0=mdr1 duplicated, 0.0=mdr1 not duplicated, -1.0=duplication status of mdr1 undetermined
    - mdr1_breakpoint                Tandem duplication breakpoints around mdr1.
    - pm2_dup_call                   1.0=plasmepsin 2-3 duplicated, 0.0=plasmepsin 2-3 not duplicated, -1.0=duplication status of plasmepsin 2-3 undetermined
    - pm2_breakpoint                 Tandem duplication breakpoints around plasmepsin 2-3.

Explanation of amino acid columns in crt, dhfr and dhps:

Each value can have a single haplotype if homozygous or two haplotypes separated by a comma if heterozygous
It is possible to have heterozygous calls where both amino acid haplotypes are the same. The heterozygosity here is at the nucleotide level. These could perhaps be considered homozygous alt.
- represents missing (missing genotype in at least one of the positions)
* represents an unphased het followed by another het. Because hets are unphased it is not possible to resolve the two haplotypes. These are perhaps best considered missing.
! represents a frame-shift in the haplotype. These are perhaps best considered missing.

Explanation of non-synonymous changes (ns_changes): 
Non-synonymous mutations are shown in the form: <REF><POS><ALT>. Homozygous mutations are shown in upper case and heterozygous in lower case. The nomenclature for amino acids described above is also used in this field. 


======================================================================
- Pf8_inferred_resistance_status_classification.tsv
======================================================================

This file includes sample phenotype data for 24,409 samples that passed QC derived from the data in Pf_8_drug_resistance_marker_genotypes.txt, using the rules outlined in "Pf8 mapping genetic markers to inferred resistance status classification.docx", together with deletion genotypes for HRP2 and HRP3 that can be used to determine resistance to rapid diagnostic tests (RDTs). It contains the following columns:

    - Sample                         Unique ID of each sample (which can be used to link to other sample information and genotypes)
    - Chloroquine                    Chloroquine resistance status. Resistant/Sensitive/Undetermined
    - Pyrimethamine                  Pyrimethamine resistance status. Resistant/Sensitive/Undetermined
    - Sulfadoxine                    Sulfadoxine resistance status. Resistant/Sensitive/Undetermined
    - Mefloquine                     Mefloquine resistance status. Resistant/Sensitive/Undetermined
    - Artemisinin                    Artemisinin resistance status. Resistant/Sensitive/Undetermined
    - Piperaquine                    Piperaquine resistance status. Resistant/Sensitive/Undetermined
    - SP (uncomplicated)             Sulfadoxine-Pyrimethamine treatment resistance status. Samples carrying the dhfr triple mutant, which is strongly associated with SP failure. Resistant/Sensitive/Undetermined
    - SP (IPTp)                      Sulfadoxine-Pyrimethamine intermittent preventive treatment in pregnancy resistance status. Samples carrying the dhfr/dhps sextuple mutant, which confers a higher level of SP resistance. Resistant/Sensitive/Undetermined
    - AS-MQ                          Artesunate-mefloquine resistance status. Resistant/Sensitive/Undetermined
    - DHA-PPQ                        Dihydroartemisinin-piperaquine resistance status. Resistant/Sensitive/Undetermined
    - HRP2                           Deletions at HRP2 associated with failure of rapid diagnostic tests. del=HRP2 deleted, nodel=HRP2 not deleted, uncallable
    - HRP3                           Deletions at HRP3 associated with failure of rapid diagnostic tests. del=HRP3 deleted, nodel=HRP3 not deleted
    - HRP2 and HRP3                  Deletions at HRP2 and HRP3 associated with failure of rapid diagnostic tests. del=both HRP2 and HRP3 deleted, nodel=either HRP2, HRP3 or both not deleted, uncallable


======================================================================
- Pf8_resistance_classification.pdf
======================================================================

This file describes the rules used to create Pf8_inferred_resistance_status_classification.txt


======================================================================
- Pf8.zarr.zip
======================================================================

This file contains the information that is encoded in the VCF files, but in zipped zarr format.

The description of the zarr attributes can be found in the header of the VCFs described above.

We recommend analysing data using the scikit-allel package with the zarr file. For more details
on using scikit-allel, please see https://scikit-allel.readthedocs.io/en/stable/


======================================================================
- Pfalciparum.genome.fasta
======================================================================

3D7 reference genome sequence used for mapping, in fasta format.


======================================================================
- PlasmoDB-55_Pfalciparum3D7.gff.gz
======================================================================

Genomic features file used for annotating variants. This was downloaded from https://plasmodb.org/common/downloads/release-55/Pfalciparum3D7/gff/data/PlasmoDB-55_Pfalciparum3D7.gff and subsequently gzipped.


======================================================================
- vcf/
======================================================================

This directory contains vcf files, one per chromosome, containing genotype calls for all 33,325 samples. Each file is in bgzip format (.vcf.gz) and has an associated tabix index file (.vcf.gz.tbi). There are sixteen files in total, fourteen for each of the autosomes (Pf3D7_01_v3 - Pf3D7_14_v3), one for the mitochondrial sequence (Pf3D7_MIT_v3) and one for the apicoplast sequence (Pf3D7_API_v3).

The files, once unzipped, are tab-separated text files, but may be too large to open in Excel.

The VCF format is described in https://github.com/samtools/hts-specs

Tools to assist in handling VCF files are freely available from
http://samtools.github.io/bcftools/

The VCF files contain details of 12,493,205 discovered variant genome positions.
These variants were discovered amongst all samples from the release.
4,411,457 of these variant positions are SNPs, with the remainder being either
short insertion/deletions (indels), or a combination of SNPs and indels. It is
important to note that many of these variants are considered low quality. Only
the variants for which the FILTER column is set to PASS should be considered of
reasonable quality. There are 8,097,456 such PASS variants of which 3,019,934
are SNPs and 5,077,522 indels.

The FILTER column is based on two types of information. Firstly certain regions
of the genome are considered "non-core". This includes sub-telomeric regions,
centromeres and internal VAR gene regions on chromosomes 4, 6, 7, 8 and 12. All
variants within non-core regions are considered to be low quality, and hence
will not have the FILTER column set to PASS. The regions which are core and
non-core can be found in the file
ftp://ngs.sanger.ac.uk/production/malaria/pf-crosses/1.0/regions-20130225.onebased.txt.

Secondly, variants are filtered out based on a quality score called VQSLOD. All
variants with a VQSLOD score below 2 are filtered out, i.e. will have a value of
Low_VQSLOD in the FILTER column, rather than PASS. The VQSLOD score for each
variant can be found in the INFO field of the VCF file. It is possible to use
the VQSLOD score to define a more or less stringent set of variants (see next
section for further details).

It is also important to note that many variants have more than two alleles. For
example, amongst the 3,019,934 PASS SNP variants, 2,190,026 are biallelic. The
remaining 829,908 PASS SNP variants have 3 or more alleles. The maximum number of
alternative alleles represented is 6. Note that some positions can in truth have
more than 6 alternative alleles, particularly those at the start of short tandem
repeats. In such cases, some true alternative alleles will be missing.

In addition to alleles representing SNPs and indels, some variants have an
alternative allele denoted by the * symbol. This is used to denote a "spanning
deletion". For samples that have this allele, the base at this position has been
deleted. Note that this is not the same as a missing call - the * denotes that
there are reads spanning across this position, but that the reads have this
position deleted yet map on either side of the deletion. For further details see
https://software.broadinstitute.org/gatk/guide/article?id=6926

In addition to the VQSLOD score mentioned above, The INFO field contains many
other variant-level metrics. The metrics QD, FS, SOR, DP are all measures
related to the quality of the variant. The VQSLOD score is derived from these
five metrics.

AC contains the number of non-reference alleles amongst the samples in the file.
Because the file contains diploid genotype calls, homozygous non-reference calls
will be counted as two non-reference alleles, whereas heterozygous calls will be
counted as one non-reference allele. Where a variant position has more than one
one non-reference allele, counts of each different non-reference allele are
given. AN contains the total number of called alleles, including reference
alleles. A simple non-reference allele frequency can be calculated as AC/AN.
AC and AN values are all specific to the samples in the study the VCF was created
for.

Various functional annotations are held in the the SNPEFF variables of the INFO
field. Where appropriate, the amino acid change caused by the variant can be
found in SNPEFF_AMINO_ACID_CHANGE. Note that for multi-allelic variants, only
one annotation is given, and therefore this should not be relied on for non-
biallelic variants. SNPEFF_AMINO_ACID_CHANGE also does not take account of
nearby variants, so if two SNPs are present in the same codon, the
amino acid change given is likely to be wrong. Similarly, if two coding indels
are found in the same exon, the SNPEFF annotations are likely to be wrong. This
situation occurs at the CRT locus (see next section for further details).

Coding variants are identified using the CDS flag in the INFO field.

Columns 10 and onwards of the VCF contain the information for each sample.
The first component of this (GT) is always the diploid genotype call as
determined by GATK. A value of 0/0 indicates a homozygous reference call. A
value of 1/1 indicates a homozygous alternative allele call. 0/1 indicates a
heterozygous call. A value of 2 indicates the sample has the second alternative
allele, i.e. the second value in the ALT column. For example 2/2 would mean the
sample is homozygous the the second alternative allele, 0/2 would mean the
sample is heterozygous for the reference and second alternative alleles, and 1/2
would mean the sample is heterozygous for the first and second alternative
alleles. A value of ./. indicates a missing genotype call, usually because there
are no reads mapping at this position in that sample.


Recommendations regarding sets of variants to use in analyses
-------------------------------------------------------------

Variants are filtered using the VQSLOD metric. VQSLOD is log(p/q) where p is the
probability of being true and q is the probability of being false. Theoretically,
when VQSLOD > 0, p is greater than q, and therefore the variant is more likely
true than false. Conversely, when VQSLOD < 0, the variant is theoretically more
like false than true. This is why we have chosen 0 as the threshold to use to
declare that variants have passed the filters: all PASS variants are
theoretically more likely true than false. Of course, for variants where VQSLOD
is only slightly above 0, there is only a slightly greater probability of being
true than of being false. Therefore, for example, many of the variants with
values between 0 and 1 are likely to be false.

Empirically we have found that SNPs tend to be more accurate than indels, coding
variants tend to be more accurate than non-coding variants, and bi-allelic
variants tend to be more accurate than multi-allelic variants. If you require a
very reliable set of variants for genome-wide analysis, and don't mind if you
miss some real variants, we recommend using only bi-allelic coding SNPs in the
core genome with a VQSLOD score > 6. We include a command below to create such a set of variants.

If instead you would like to know of all likely variation within a certain
region, even if this means including a few false variants, we recommend using
all PASS variants. Finally, if you want to ensure you miss as little as possible
of the true variation, at the risk of including large numbers of false positives,
you could ignore the FILTER column and use all variants in the VCF.

In general, we recommend caution in analysing indels. For any given sample, the
majority of differences from the reference genome are likely to be due to indels
in low-complexity non-coding regions, e.g. in length polymorphisms of short
tandem repeats (STRs), such as homopolymer runs or AT repeats. In general, it is
difficult to map short reads reliably in such regions, and this is compounded by
the fact that these regions tend to have high AT content, and in general we
typically have much lower coverage in high AT regions. Indels also tend to be
multi-allelic, making analysis much more challenging than for (typically
bi-allelic) SNPs.

Extracting data from the VCF file
-----------------------------

We recommend the use of bcftools. To install bcftools, follow the instructions
at: https://github.com/samtools/bcftools/wiki/HOWTOs

The following are some commands which you might find useful for extracting data
from the vcf.gz files. We've used an example the vcf for chromosome 5
(Pf3D7_05_v3.filt.vcf.gz), but similar commands should work on all vcf files.

To extract sample IDs and put into a file, one per line:
bcftools query --list-samples Pf3D7_05_v3.filt.vcf.gz > samples.txt

To extract chromosome, position, reference allele, all alternate alleles,
filter value and VQSLOD for all variants into a tab-delimited file:
bcftools query -f \
'%CHROM\t%POS\t%REF\t%ALT{0}\t%ALT{1}\t%ALT{2}\t%ALT{3}\t%ALT{4}\t%ALT{5}\t%FILTER\t%VQSLOD\n' \
Pf3D7_05_v3.filt.vcf.gz > all_variants.txt

To extract chromosome, position, reference allele, all alternate alleles and
VQSLOD for PASS SNPs only into a tab-delimited file:
bcftools query -f \
'%CHROM\t%POS\t%REF\t%ALT{0}\t%ALT{1}\t%ALT{2}\t%ALT{3}\t%ALT{4}\t%ALT{5}\t%VQSLOD\n' \
--include 'FILTER="PASS" && TYPE="snp"' \
Pf3D7_05_v3.filt.vcf.gz > pass_snps.txt

To extract chromosome, position, reference allele, alternate allele and VQSLOD
for biallelic PASS SNPs only into a tab-delimited file:
bcftools query -f \
'%CHROM\t%POS\t%REF\t%ALT{0}\t%VQSLOD\n' \
--include 'FILTER="PASS" && TYPE="snp" && N_ALT=1' \
Pf3D7_05_v3.filt.vcf.gz > biallelic_pass_snps.txt

To extract chromosome, position, reference allele, alternate allele and VQSLOD
for biallelic PASS SNPs that are segregating within the study into a
tab-delimited file:
bcftools query -f \
'%CHROM\t%POS\t%REF\t%ALT{0}\t%VQSLOD\n' \
--include 'FILTER="PASS" && TYPE="snp" && N_ALT=1 && AC>0' \
Pf3D7_05_v3.filt.vcf.gz > biallelic_segregating_pass_snps.txt

To create a vcf file which contains only PASS bi-allelic coding SNPs with
VQSLOD > 6:
bcftools view \
--include 'FILTER="PASS" && N_ALT=1 && CDS==1 && TYPE="snp" && VQSLOD>6.0' \
--output-type z \
--output-file output_filename.vcf.gz \
Pf3D7_05_v3.filt.vcf.gz
bcftools index --tbi output_filename.vcf.gz

To extract diploid genotype calls for biallelic PASS SNPs in gene MDR1 into a
tab-delimited text file, including the chromosome, position, ref and alt
alleles, VQSLOD score and amino acid substitution, and a header containing
sample names:
bcftools query \
-f '%CHROM\t%POS\t%REF\t%ALT{0}\t%VQSLOD\t%SNPEFF_AMINO_ACID_CHANGE[\t%GT]\n' \
--regions Pf3D7_05_v3:957890-962149 \
--include 'FILTER="PASS" && TYPE="snp" && N_ALT=1' \
--print-header \
Pf3D7_05_v3.filt.vcf.gz > mdr1_genotypes.txt

To extract ref allele depths for biallelic PASS SNPs in gene MDR1 into a
tab-delimited text file, including the chromosome, position, ref and alt
alleles, VQSLOD score and amino acid substitution, and a header containing
sample names:
bcftools query \
-f '%CHROM\t%POS\t%REF\t%ALT{0}\t%VQSLOD\t%SNPEFF_AMINO_ACID_CHANGE[\t%AD{0}]\n' \
--regions Pf3D7_05_v3:957890-962149 \
--include 'FILTER="PASS" && TYPE="snp" && N_ALT=1' \
--print-header \
Pf3D7_05_v3.filt.vcf.gz > mdr1_ref_allele_depth.txt

To extract alt allele depths for biallelic PASS SNPs in gene MDR1 into a
tab-delimited text file, including the chromosome, position, ref and alt
alleles, VQSLOD score and amino acid substitution, and a header containing
sample names:
bcftools query \
-f '%CHROM\t%POS\t%REF\t%ALT{0}\t%VQSLOD\t%SNPEFF_AMINO_ACID_CHANGE[\t%AD{1}]\n' \
--regions Pf3D7_05_v3:957890-962149 \
--include 'FILTER="PASS" && TYPE="snp" && N_ALT=1' \
--print-header \
Pf3D7_05_v3.filt.vcf.gz > mdr1_alt_allele_depth.txt


======================================================================
- cram/
======================================================================

This directory contains compressed files containing the sequencing data for each of the 33,325 samples in Pf8. 

CRAM files contain information on read sequences, their alignment to the reference genome, alignment and read quality scores, and other positional information for reads.

CRAM files are similar to BAM files, and may be converted using the samtools command:
samtools view -b -T <reference_genome_file_name> -o output.bam input.cram


======================================================================
- gvcf/
======================================================================

This directory contains genomic VCF (gVCF) files for Pf8. There are 16 gVCFs per 33,325 samples (one per chromosome), resulting in 533,200 files in this directory. 

gVCFs are similar to VCF files, but also contain non-variant positions instead of only variant positions. See https://gatk.broadinstitute.org/hc/en-us/articles/360035531812-GVCF-Genomic-Variant-Call-Format for further details. These gVCF files can be combined with other gVCF files for users who are interested in carrying out joint genotyping across their own data and Pf8.


======================================================================
- snp-only/vcf/
======================================================================

This directory contains SNP-only VCF files. These files are filtered versions of vcf files contained in Pf8_vcf/. SNP-only VCFs have had all non-SNP positions removed. 

As with the vcf/ directory, there is one SNP-only VCF per chromosome. Each file is in bgzip format (.vcf.gz) and has an associated tabix index file (.vcf.gz.tbi). There are sixteen files in total, fourteen for each of the autosomes (Pf3D7_01_v3 - Pf3D7_14_v3), one for the mitochondrial sequence (Pf3D7_MIT_v3) and one for the apicoplast sequence (Pf3D7_API_v3).

The SNP-only VCF files contain details of 10,821,552 discovered SNPs.
It is important to note that many of these variants are considered low quality. Only
the variants for which the FILTER column is set to PASS should be considered of
reasonable quality. There are 6,820,626 such PASS SNPs.

Guidance for using VCF files are as described in the vcf/ section of this README. 


======================================================================
- Pf8_snp_only_zarr.zip
======================================================================

This file contains the information that is encoded in the SNP-only VCF files, but in zipped zarr format.

The description of the zarr attributes can be found in the header of the VCFs described above.

We recommend analysing data using the scikit-allel package with the zarr file. For more details
on using scikit-allel, please see https://scikit-allel.readthedocs.io/en/stable/


======================================================================
- Pf8_mean_genotype_distance_snp_only.npy
======================================================================

This file includes the genetic distances between all 33,325 sample pairs using the SNP-only genetic callset. These are included in a numpy array, which can be easily accessed via the numpy library in python (see https://numpy.org/doc/stable/reference/generated/numpy.load.html for more details) using a command such as `np.load("Pf8_mean_genotype_distance_snp_only.npy")`. Samples are ordered as per the Pf8_samples.txt file. 


======================================================================
Release notes:
======================================================================

Data excluded from release:
Sequence read data on samples collected in Indonesia cannot be made publicly available because of national export restrictions.

