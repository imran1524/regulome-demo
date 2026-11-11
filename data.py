"""Synthetic demo data for the Regulome AI prototype.

EVERYTHING HERE IS INVENTED. Gene names, coordinates and scores are placeholders
chosen to show the workflow. None of it is real patient data, real AlphaGenome
output or a real benchmark result.

To use real inputs, replace CASES/SNAPSHOTS with loaders that read:
  - Exomiser/Genomiser results (open source),
  - the permissively licensed AVI static download (check the current terms),
and keep every other source out unless its licence permits commercial use.
"""

CELL_TYPES = ["Cortical neuron", "Cardiomyocyte", "T cell"]

SNAPSHOTS = {
    "snapshot-A": {
        "label": "Snapshot A (earlier score release)",
        "baseline_tool": "Genomiser (synthetic stand-in) v-A",
        "avi_release": "AVI synthetic release A",
    },
    "snapshot-B": {
        "label": "Snapshot B (later score release)",
        "baseline_tool": "Genomiser (synthetic stand-in) v-B",
        "avi_release": "AVI synthetic release B",
    },
}

# Per variant: baseline (0-1), avi (Phred-like, 0-60), pheno (0-1), cell (dict 0-1).
# Snapshot B changes a few baseline/avi values to mimic a new score release.
_V = [
    # case, id, gene, region, A: baseline, avi | B: baseline, avi | pheno | cell relevance
    ("CASE-1", "chr1:1000100 G>A", "SYN-GENE-01", "enhancer", 0.62, 31, 0.62, 31, 0.80, {"Cortical neuron": 0.90, "Cardiomyocyte": 0.20, "T cell": 0.10}),
    ("CASE-1", "chr1:1000450 C>T", "SYN-GENE-01", "promoter", 0.71, 27, 0.55, 22, 0.80, {"Cortical neuron": 0.70, "Cardiomyocyte": 0.30, "T cell": 0.20}),
    ("CASE-1", "chr2:2200310 A>G", "SYN-GENE-02", "deep intronic", 0.40, 44, 0.48, 52, 0.55, {"Cortical neuron": 0.85, "Cardiomyocyte": 0.10, "T cell": 0.10}),
    ("CASE-1", "chr3:3300777 T>C", "SYN-GENE-03", "5' UTR", 0.58, 18, 0.58, 18, 0.30, {"Cortical neuron": 0.40, "Cardiomyocyte": 0.40, "T cell": 0.30}),
    ("CASE-1", "chr4:4400020 G>T", "SYN-GENE-04", "intergenic", 0.35, 12, 0.35, 12, 0.20, {"Cortical neuron": 0.20, "Cardiomyocyte": 0.20, "T cell": 0.20}),
    ("CASE-1", "chr5:5500660 C>G", "SYN-GENE-05", "enhancer", 0.66, 38, 0.60, 36, 0.35, {"Cortical neuron": 0.30, "Cardiomyocyte": 0.80, "T cell": 0.10}),
    ("CASE-1", "chr6:6600905 A>C", "SYN-GENE-06", "splice region", 0.80, 20, 0.80, 20, 0.45, {"Cortical neuron": 0.50, "Cardiomyocyte": 0.30, "T cell": 0.30}),
    ("CASE-1", "chr7:7700141 T>A", "SYN-GENE-07", "promoter", 0.30, 25, 0.30, 25, 0.25, {"Cortical neuron": 0.25, "Cardiomyocyte": 0.25, "T cell": 0.60}),
    ("CASE-2", "chr8:8800220 G>C", "SYN-GENE-08", "enhancer", 0.55, 40, 0.57, 46, 0.85, {"Cortical neuron": 0.10, "Cardiomyocyte": 0.92, "T cell": 0.10}),
    ("CASE-2", "chr9:9900880 C>A", "SYN-GENE-09", "promoter", 0.74, 29, 0.74, 29, 0.60, {"Cortical neuron": 0.20, "Cardiomyocyte": 0.75, "T cell": 0.20}),
    ("CASE-2", "chr10:1010100 A>T", "SYN-GENE-10", "deep intronic", 0.38, 33, 0.38, 33, 0.40, {"Cortical neuron": 0.30, "Cardiomyocyte": 0.50, "T cell": 0.20}),
    ("CASE-2", "chr11:1111500 T>G", "SYN-GENE-11", "3' UTR", 0.62, 15, 0.50, 11, 0.30, {"Cortical neuron": 0.20, "Cardiomyocyte": 0.35, "T cell": 0.20}),
    ("CASE-2", "chr12:1212700 G>A", "SYN-GENE-12", "intergenic", 0.28, 10, 0.28, 10, 0.15, {"Cortical neuron": 0.10, "Cardiomyocyte": 0.10, "T cell": 0.10}),
    ("CASE-3", "chr13:1313010 C>T", "SYN-GENE-13", "enhancer", 0.50, 36, 0.50, 36, 0.78, {"Cortical neuron": 0.10, "Cardiomyocyte": 0.10, "T cell": 0.88}),
    ("CASE-3", "chr14:1414320 A>G", "SYN-GENE-14", "promoter", 0.69, 24, 0.69, 24, 0.65, {"Cortical neuron": 0.20, "Cardiomyocyte": 0.20, "T cell": 0.70}),
    ("CASE-3", "chr15:1515600 G>T", "SYN-GENE-15", "deep intronic", 0.33, 41, 0.41, 49, 0.50, {"Cortical neuron": 0.15, "Cardiomyocyte": 0.15, "T cell": 0.80}),
    ("CASE-3", "chr16:1616800 T>C", "SYN-GENE-16", "splice region", 0.77, 19, 0.77, 19, 0.35, {"Cortical neuron": 0.30, "Cardiomyocyte": 0.30, "T cell": 0.40}),
    ("CASE-3", "chr17:1717450 C>G", "SYN-GENE-17", "intergenic", 0.30, 9, 0.30, 9, 0.10, {"Cortical neuron": 0.10, "Cardiomyocyte": 0.10, "T cell": 0.10}),
]

CASES = {
    "CASE-1": {
        "title": "Synthetic case 1: neurodevelopmental presentation",
        "hpo": ["HP:0001250 Seizure", "HP:0001263 Global developmental delay"],
        "inheritance": "de novo (synthetic)",
        "default_cell": "Cortical neuron",
    },
    "CASE-2": {
        "title": "Synthetic case 2: cardiac presentation",
        "hpo": ["HP:0001638 Cardiomyopathy"],
        "inheritance": "autosomal dominant (synthetic)",
        "default_cell": "Cardiomyocyte",
    },
    "CASE-3": {
        "title": "Synthetic case 3: immune presentation",
        "hpo": ["HP:0002721 Immunodeficiency"],
        "inheritance": "autosomal recessive (synthetic)",
        "default_cell": "T cell",
    },
}


def variants(case_id, snapshot):
    """Return the raw per-variant component values for one case and snapshot."""
    out = []
    for (cid, vid, gene, region, bA, aA, bB, aB, pheno, cell) in _V:
        if cid != case_id:
            continue
        base, avi = (bA, aA) if snapshot == "snapshot-A" else (bB, aB)
        out.append(
            {"variant": vid, "gene": gene, "region": region,
             "baseline": base, "avi": avi, "pheno": pheno, "cell": cell}
        )
    return out


def score_rows(case_id, snapshot, cell_type, weights):
    """Score and rank variants. Returns a list of dicts sorted by rank."""
    rows = []
    for v in variants(case_id, snapshot):
        comps = {
            "baseline": v["baseline"],
            "avi": min(v["avi"] / 40.0, 1.0),  # normalise Phred-like score to 0-1
            "pheno": v["pheno"],
            "cell": v["cell"][cell_type],
        }
        contrib = {k: weights[k] * comps[k] for k in comps}
        total_w = sum(weights.values()) or 1.0
        score = sum(contrib.values()) / total_w
        spread = max(comps.values()) - min(comps.values())
        agreement = "High agreement" if spread < 0.35 else ("Mixed" if spread < 0.6 else "Conflicting")
        rows.append(
            {"variant": v["variant"], "gene": v["gene"], "region": v["region"],
             "score": round(score, 3), "agreement": agreement,
             "components": {k: round(x, 3) for k, x in comps.items()},
             "contrib": {k: round(x / total_w, 3) for k, x in contrib.items()}}
        )
    rows.sort(key=lambda r: -r["score"])
    for i, r in enumerate(rows, 1):
        r["rank"] = i
    return rows


def top_k_recall(df, k=10, setup_col="setup", rank_col="rank", hit_col="is_causal"):
    """Top-k recall per setup from a long table of ranked candidates.

    Expected columns: setup, case_id, rank, is_causal (bool). One causal variant
    per case is the simplest layout; multiple per case are counted individually.
    """
    res = {}
    for setup, g in df.groupby(setup_col):
        causal = g[g[hit_col]]
        if len(causal) == 0:
            continue
        res[setup] = float((causal[rank_col] <= k).mean())
    return res
