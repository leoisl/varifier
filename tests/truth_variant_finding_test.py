import filecmp
import os
import pytest
import subprocess

from cluster_vcf_records import vcf_file_read

from varifier import truth_variant_finding, utils

this_dir = os.path.dirname(os.path.abspath(__file__))
data_dir = os.path.join(this_dir, "data", "truth_variant_finding")


def test_check_dependencies_in_path():
    truth_variant_finding._check_dependencies_in_path()


def test_truth_using_minimap2_paftools():
    ref_fasta = os.path.join(data_dir, "truth_using_minimap2_paftools.ref.fa")
    truth_fasta = os.path.join(data_dir, "truth_using_minimap2_paftools.truth.fa")
    truth_revcomp_fasta = os.path.join(
        data_dir, "truth_using_minimap2_paftools.truth.revcomp.fa"
    )

    # test truth_variant_finding._truth_using_minimap2_paftools
    tmp_vcf = "tmp.truth_using_minimap2_paftools.vcf"
    subprocess.check_output(f"rm -f {tmp_vcf}", shell=True)
    truth_variant_finding._truth_using_minimap2_paftools(
        ref_fasta, truth_fasta, tmp_vcf, snps_only=False
    )
    expect_vcf = os.path.join(data_dir, "truth_using_minimap2_paftools.expect.vcf")
    assert filecmp.cmp(tmp_vcf, expect_vcf, shallow=False)
    os.unlink(tmp_vcf)

    # now with snps only
    tmp_vcf = "tmp.truth_using_minimap2_paftools.vcf"
    subprocess.check_output(f"rm -f {tmp_vcf}", shell=True)
    truth_variant_finding._truth_using_minimap2_paftools(
        ref_fasta, truth_fasta, tmp_vcf, snps_only=True
    )
    expect_vcf = os.path.join(data_dir, "truth_using_minimap2_paftools.expect.snps_only.vcf")
    assert filecmp.cmp(tmp_vcf, expect_vcf, shallow=False)
    os.unlink(tmp_vcf)
    tmp_discarded_not_snps = "tmp.truth_using_minimap2_paftools.vcf.discarded_not_snps.vcf"
    expect_discarded_not_snps = os.path.join(data_dir, "truth_using_minimap2_paftools.expect.discarded_not_snps.vcf")
    assert filecmp.cmp(tmp_discarded_not_snps, expect_discarded_not_snps, shallow=False)
    os.unlink(tmp_discarded_not_snps)

    # now with rev comp
    # The result should be the same if we reverse complement the truth reference.
    # However, these tags: "QSTART=122;QSTRAND=-" mean that the VCF file is not
    # identical (although the CHROM, REF, ALT columns are). Hence we have a
    # different expected VCF file
    tmp_vcf_revcomp = "tmp.truth_using_minimap2_paftools.revcomp.vcf"
    truth_variant_finding._truth_using_minimap2_paftools(
        ref_fasta, truth_revcomp_fasta, tmp_vcf_revcomp, snps_only=False
    )
    expect_vcf_revcomp = os.path.join(
        data_dir, "truth_using_minimap2_paftools.expect.revcomp.vcf"
    )
    assert filecmp.cmp(tmp_vcf_revcomp, expect_vcf_revcomp, shallow=False)
    os.unlink(tmp_vcf_revcomp)


def test_merge_vcf_files_for_probe_mapping():
    vcf_files = [
        os.path.join(data_dir, "merge_vcf_files_for_probe_mapping.in.1.vcf"),
        os.path.join(data_dir, "merge_vcf_files_for_probe_mapping.in.2.vcf"),
    ]
    tmp_vcf = "tmp.merge_vcf_files_for_probe_mapping.vcf"
    subprocess.check_output(f"rm -f {tmp_vcf}", shell=True)
    ref_fasta = os.path.join(data_dir, "merge_vcf_files_for_probe_mapping.ref.fa")
    truth_variant_finding._merge_vcf_files_for_probe_mapping(
        vcf_files, ref_fasta, tmp_vcf
    )
    expect_vcf = os.path.join(data_dir, "merge_vcf_files_for_probe_mapping.expect.vcf")
    assert filecmp.cmp(tmp_vcf, expect_vcf, shallow=False)
    os.unlink(tmp_vcf)


def test_filter_fps_and_long_vars_from_probe_mapped_vcf():
    vcf_in = os.path.join(
        data_dir, "filter_fps_and_long_vars_from_probe_mapped_vcf.in.vcf"
    )
    expect_vcf = os.path.join(
        data_dir, "filter_fps_and_long_vars_from_probe_mapped_vcf.expect.vcf"
    )
    tmp_vcf = "tmp.filter_fps_and_long_vars_from_probe_mapped_vcf.vcf"
    subprocess.check_output(f"rm -f {tmp_vcf}", shell=True)
    truth_variant_finding._filter_fps_and_long_vars_from_probe_mapped_vcf(
        vcf_in, tmp_vcf, None
    )
    assert filecmp.cmp(tmp_vcf, expect_vcf, shallow=False)
    os.unlink(tmp_vcf)
    truth_variant_finding._filter_fps_and_long_vars_from_probe_mapped_vcf(
        vcf_in, tmp_vcf, 1
    )
    expect_vcf = os.path.join(
        data_dir, "filter_fps_and_long_vars_from_probe_mapped_vcf.expect.max_ref_1.vcf"
    )
    assert filecmp.cmp(tmp_vcf, expect_vcf, shallow=False)
    os.unlink(tmp_vcf)


def test_bcftools_norm():
    ref_fasta = os.path.join(data_dir, "bcftools_norm.ref.fa")
    vcf_in = os.path.join(data_dir, "bcftools_norm.in.vcf")
    expect_vcf = os.path.join(data_dir, "bcftools_norm.expect.vcf")
    tmp_vcf = "tmp.bcftools_norm.vcf"
    subprocess.check_output(f"rm -f {tmp_vcf}", shell=True)
    truth_variant_finding._bcftools_norm(ref_fasta, vcf_in, tmp_vcf)
    # Header lines get changed, so just check the variant lines
    assert utils.vcf_records_are_the_same(tmp_vcf, expect_vcf)
    os.unlink(tmp_vcf)


def test_make_truth_vcf():
    ref_fasta = os.path.join(data_dir, "make_truth_vcf.ref.fa")
    truth_fasta = os.path.join(data_dir, "make_truth_vcf.truth.fa")
    tmp_out = "tmp.truth_variant_finding.make_truth_ref"
    subprocess.check_output(f"rm -rf {tmp_out}", shell=True)
    got_vcf = truth_variant_finding.make_truth_vcf(ref_fasta, truth_fasta, tmp_out, 100)
    expect_vcf = os.path.join(data_dir, "make_truth_vcf.expect.vcf")
    assert utils.vcf_records_are_the_same(got_vcf, expect_vcf)
    subprocess.check_output(f"rm -r {tmp_out}", shell=True)
    # Test same run again, but mask a position in the truth where there's a SNP
    truth_mask = {"truth": {59}}
    got_vcf = truth_variant_finding.make_truth_vcf(
        ref_fasta, truth_fasta, tmp_out, 100, truth_mask=truth_mask
    )
    expect_vcf = os.path.join(data_dir, "make_truth_vcf.expect.masked.vcf")
    assert utils.vcf_records_are_the_same(got_vcf, expect_vcf)
    subprocess.check_output(f"rm -r {tmp_out}", shell=True)



def test_deduplicate_vcf_files():
    vcf_files = [
        os.path.join(data_dir, "deduplicate_vcf_files_for_probe_mapping.in.1.vcf"),
        os.path.join(data_dir, "deduplicate_vcf_files_for_probe_mapping.in.2.vcf"),
    ]
    tmp_vcf = "tmp.deduplicate_vcf_files_for_probe_mapping.vcf"
    subprocess.check_output(f"rm -f {tmp_vcf}", shell=True)
    ref_fasta = os.path.join(data_dir, "deduplicate_vcf_files_for_probe_mapping.ref.fa")
    truth_variant_finding._deduplicate_vcf_files_for_probe_mapping(
        vcf_files, ref_fasta, tmp_vcf
    )
    expect_vcf = os.path.join(data_dir, "deduplicate_vcf_files_for_probe_mapping.expect.vcf")
    assert filecmp.cmp(tmp_vcf, expect_vcf, shallow=False)
    os.unlink(tmp_vcf)

    tmp_disagreements_between_dnadiff_and_minimap2 = "tmp.deduplicate_vcf_files_for_probe_mapping.vcf.disagreements_between_dnadiff_and_minimap2"
    expect_disagreements_between_dnadiff_and_minimap2 = os.path.join(data_dir, "deduplicate_vcf_files_for_probe_mapping.vcf.disagreements_between_dnadiff_and_minimap2")
    assert filecmp.cmp(tmp_disagreements_between_dnadiff_and_minimap2, expect_disagreements_between_dnadiff_and_minimap2, shallow=False)
    os.unlink(tmp_disagreements_between_dnadiff_and_minimap2)
