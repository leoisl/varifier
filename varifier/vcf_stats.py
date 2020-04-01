import copy
from operator import itemgetter

from cluster_vcf_records import vcf_file_read


def _frs_from_vcf_record(record, cov_key="COV"):
    """Gets the FRS from a VCF record, if it exists. This tag is made by
    minos. If FRS tag not there, infers it from key given by cov_key, where
    the value should be alist of coverages for each allele.
    e.g. if COV=1,3 and GT=0/0, then FRS = 1/4"""

    if "FRS" in record.FORMAT:
        if record.FORMAT["FRS"] == ".":
            return "NA"
        else:
            return float(record.FORMAT["FRS"])

    if cov_key not in record.FORMAT:
        return "NA"

    genotypes = set(record.FORMAT["GT"].split("/"))
    if "." in genotypes or len(genotypes) != 1:
        return "NA"

    allele_index = int(genotypes.pop())
    coverages = [int(x) for x in record.FORMAT[cov_key].split(",")]
    total_cov = sum(coverages)
    if total_cov == 0:
        return 0
    else:
        return coverages[allele_index] / total_cov


def per_record_stats_from_vcf_file(infile):
    """Gathers stats for each record in a VCF file.
    Returns a list of dictionaries of stats. One dict per VCF line.
    List is sorted by ref seq name (CHROM), then position (POS)"""
    stats = []
    used_keys = set()
    wanted_keys = [
        "DP",
        "DPF",
        "FRS",
        "GT_CONF",
        "GT_CONF_PERCENTILE",
        "VFR_EDIT_DIST",
        "VFR_FILTER",
        "VFR_ALLELE_LEN",
        "VFR_ALLELE_MATCH_COUNT",
        "VFR_ALLELE_MATCH_FRAC",
        "VFR_RESULT",
    ]
    key_types = {
        "DP": int,
        "DPF": float,
        "GT_CONF": float,
        "GT_CONF_PERCENTILE": float,
        "FRS": float,
        "VFR_EDIT_DIST": int,
        "VFR_ALLELE_MATCH_FRAC": float,
        "VFR_ALLELE_LEN": int,
        "VFR_ALLELE_MATCH_COUNT": int,
    }
    header_lines, vcf_records = vcf_file_read.vcf_file_to_list(infile)
    for record in vcf_records:
        record_stats = {x: record.FORMAT.get(x, "NA") for x in wanted_keys}
        record_stats["FRS"] = _frs_from_vcf_record(record)
        record_stats["CHROM"] = record.CHROM
        record_stats["POS"] = record.POS + 1
        for key, key_type in key_types.items():
            try:
                record_stats[key] = key_type(record_stats[key])
            except:
                pass

        stats.append(record_stats)

    stats.sort(key=itemgetter("CHROM", "POS"))
    return stats


def summary_stats_from_per_record_stats(per_record_stats):
    """Given a list of stats made by per_record_stats_from_vcf_file(),
    returns a dictionary of summary stats"""
    default_counts = {k: 0 for k in ("Count", "SUM_ALLELE_MATCH_FRAC", "SUM_EDIT_DIST")}
    stats = {"UNUSED": 0}
    for key in "ALL", "FILT":
        stats[key] = {"TP": copy.copy(default_counts), "FP": copy.copy(default_counts)}

    for d in per_record_stats:
        if d["VFR_FILTER"] not in ["PASS", "FAIL_BUT_TEST"]:
            stats["UNUSED"] += 1
        else:
            if d["VFR_RESULT"] == "TP":
                result = "TP"
            else:
                result = "FP"
            keys_to_update = ["ALL"]
            if d["VFR_FILTER"] == "PASS":
                keys_to_update.append("FILT")

            for key in keys_to_update:
                try:
                    stats[key][result]["SUM_ALLELE_MATCH_FRAC"] += d[
                        "VFR_ALLELE_MATCH_FRAC"
                    ]
                except TypeError:  # the value could be "NA"
                    pass

                stats[key][result]["SUM_EDIT_DIST"] += d["VFR_EDIT_DIST"]
                stats[key][result]["Count"] += 1

    return stats