"""
Deeper survey analysis for the Results section.

Reads the frozen survey CSV and writes Outputs/survey_deepdive.json with:
  - sample profile (role / industry / region / stage / experience / archetype counts)
  - direct criterion-importance ratings (1-7): mean and SD
  - best/worst criterion frequencies
  - a SURVEY-DERIVED decision matrix from per-metric ratings (e_metric_ratings),
    and the TOPSIS ranking it produces under the literature weights.

This provides a second, independent practitioner validation: not only do the
survey BWM weights agree with the literature baseline (Spearman rho reported
in Outputs/analysis_results.json, see run_analysis.py), but a decision matrix
built from practitioners' own per-metric scoring reproduces the framework's
endpoints (Retention first, NPS last).
"""

import csv
import json
import statistics as st
from collections import Counter
from pathlib import Path

import numpy as np

REPO = Path(__file__).resolve().parents[1]
CSV = REPO / "data" / "survey_responses.csv"
OUT = REPO / "outputs" / "survey_deepdive.json"

CRIT_COLS = ["c1_value_alignment", "c2_measurability", "c3_actionability", "c4_predictive_power",
             "c5_team_alignment", "c6_gaming_resistance", "c7_experiment_sensitivity", "c8_strategic_fit"]
C_KEYS = ["valuealignment", "measurability", "actionability", "predictivepower",
          "teamalignment", "gamingresistance", "experimentsensitivity", "strategicfit"]
ALTS = ["dau", "retention", "mrr", "nps", "featureadoption", "clv"]
ALT_NAME = {"dau": "DAU", "retention": "Retention", "mrr": "MRR",
            "nps": "NPS", "featureadoption": "Feature Adoption", "clv": "CLV"}
LIT_W = np.array([0.18, 0.12, 0.14, 0.15, 0.10, 0.08, 0.07, 0.16])


def topsis(M, w):
    r = M / np.sqrt((M ** 2).sum(0))
    v = r * w
    pis, nis = v.max(0), v.min(0)
    dp = np.sqrt(((v - pis) ** 2).sum(1))
    dn = np.sqrt(((v - nis) ** 2).sum(1))
    cc = dn / (dp + dn)
    return cc, cc.argsort()[::-1].argsort() + 1


def main():
    rows = list(csv.DictReader(open(CSV)))
    out = {"n": len(rows)}

    out["profile"] = {col: dict(Counter(r[col] for r in rows))
                      for col in ["role", "industry", "region", "lifecycle_stage",
                                  "experience_years", "bm_archetype"]}

    out["direct_ratings"] = {}
    for c in CRIT_COLS:
        vals = [int(r[c]) for r in rows if r[c] not in ("", "null")]
        out["direct_ratings"][c] = {"mean": round(st.mean(vals), 2),
                                    "sd": round(st.pstdev(vals), 2), "n": len(vals)}

    out["best_freq"] = dict(Counter(r["d1_best_criterion"] for r in rows))
    out["worst_freq"] = dict(Counter(r["d2_worst_criterion"] for r in rows))

    # survey-derived decision matrix from per-metric ratings
    acc = {a: {c: [] for c in C_KEYS} for a in ALTS}
    for r in rows:
        try:
            d = json.loads(r["e_metric_ratings"])
        except (json.JSONDecodeError, KeyError):
            continue
        for a in ALTS:
            if isinstance(d.get(a), dict):
                for c in C_KEYS:
                    v = d[a].get(c)
                    if v not in ("na", None, ""):
                        try:
                            acc[a][c].append(float(v))
                        except ValueError:
                            pass
    M = np.array([[st.mean(acc[a][c]) if acc[a][c] else np.nan for c in C_KEYS] for a in ALTS])
    col_means = np.nanmean(M, axis=0)
    nan_idx = np.where(np.isnan(M))
    M[nan_idx] = np.take(col_means, nan_idx[1])
    cc, rank = topsis(M, LIT_W)
    out["survey_matrix"] = {ALT_NAME[a]: [round(x, 2) for x in M[i]] for i, a in enumerate(ALTS)}
    out["survey_matrix_topsis"] = {ALT_NAME[ALTS[i]]: {"cc": round(float(cc[i]), 4),
                                                       "rank": int(rank[i])} for i in range(len(ALTS))}

    OUT.write_text(json.dumps(out, indent=2))
    print(f"Wrote {OUT.relative_to(REPO)}")
    print("Survey-derived-matrix TOPSIS ranking (literature weights):")
    for a_i in np.argsort([out["survey_matrix_topsis"][ALT_NAME[a]]["rank"] for a in ALTS]):
        nm = ALT_NAME[ALTS[a_i]]
        print(f"  {out['survey_matrix_topsis'][nm]['rank']}. {nm:16} CC={out['survey_matrix_topsis'][nm]['cc']}")


if __name__ == "__main__":
    main()
