"""
NSM Selection — Single Reproducible Analysis Entry Point
========================================================

One command regenerates every number cited in the manuscript:

    python run_analysis.py

Pipeline
--------
1. Literature-derived BWM weights (primary baseline).
2. Survey-derived BWM weights from the expert panel (n taken from the CSV;
   currently n=30: per-respondent linear BWM, Rezaei 2016 -> AIP arithmetic
   mean; geometric mean reported as robustness check).
3. Universal TOPSIS under BOTH weight sets (dual-weight robustness).
4. Segmented TOPSIS for the three business-model archetypes (literature weights).
5. One-at-a-time +/-10% and +/-20% weight sensitivity (rank-reversal count).

Outputs: console tables + outputs/analysis_results.json (machine-readable bundle).

The decision-matrix scores are literature-derived proxies, carried verbatim from
nsm_framework.py / nsm_segmented_topsis.py so this file fully supersedes them as
the analysis source of truth. Survey weights are a VALIDATION layer; literature
weights remain the primary baseline (the two are never averaged into a hybrid).

References
----------
Rezaei, J. (2015). Best-worst multi-criteria decision-making. Omega, 53, 49-57.
Rezaei, J. (2016). Best-worst MCDM: a linear model. Omega, 64, 126-130.
Hwang, C.L., & Yoon, K. (1981). Multiple Attribute Decision Making. Springer.
"""

from __future__ import annotations

import csv
import json
import os
from pathlib import Path

import numpy as np
from scipy.optimize import linprog

REPO = Path(__file__).resolve().parents[1]
SURVEY_CSV = REPO / "data" / "survey_responses.csv"
OUT_JSON = REPO / "outputs" / "analysis_results.json"

# ── Criteria / alternatives (C1..C8 column order is canonical everywhere) ─────────
CRITERIA = ["C1 Value Alignment", "C2 Measurability", "C3 Actionability",
            "C4 Predictive Power", "C5 Team Alignment", "C6 Gaming Resistance",
            "C7 Experiment Sensitivity", "C8 Strategic Fit"]
ALTERNATIVES = ["DAU", "Retention (D30)", "Revenue/MRR", "NPS",
                "Feature Adoption", "CLV"]

# Literature-derived BWM weights (CR=0.06). Primary baseline.
LIT_WEIGHTS = np.array([0.18, 0.12, 0.14, 0.15, 0.10, 0.08, 0.07, 0.16])

# Survey JSON keys -> canonical C1..C8 index. Used to align BWM responses.
JSONKEY_ORDER = ["valuealignment", "measurability", "actionability", "predictivepower",
                 "teamalignment", "gamingresistance", "experimentsensitivity", "strategicfit"]
D1_TO_KEY = {"value_alignment": "valuealignment", "measurability": "measurability",
             "actionability": "actionability", "predictive_power": "predictivepower",
             "team_alignment": "teamalignment", "gaming_resistance": "gamingresistance",
             "experiment_sensitivity": "experimentsensitivity", "strategic_fit": "strategicfit"}


# ── Decision matrices (literature-derived proxy scores, 1-10 benefit scale) ───────
def universal_matrix() -> np.ndarray:
    """Baseline 6x8 matrix (verbatim from nsm_framework.build_decision_matrix)."""
    return np.array([
        # C1 C2 C3 C4 C5 C6 C7 C8
        [6, 9, 7, 7, 7, 4, 9, 6],   # DAU
        [8, 8, 7, 9, 7, 7, 6, 9],   # Retention
        [9, 9, 6, 8, 6, 7, 5, 8],   # MRR
        [7, 6, 5, 6, 8, 6, 4, 7],   # NPS
        [7, 8, 9, 7, 8, 5, 8, 7],   # Feature Adoption
        [9, 7, 6, 9, 6, 8, 3, 9],   # CLV
    ], dtype=float)


def bm1_saas() -> np.ndarray:
    m = universal_matrix()
    m[1, [0, 1, 3, 7]] += 1   # Retention up
    m[2, [0, 1, 7]] += 1      # MRR up
    m[5, [3, 7]] += 1         # CLV up
    m[4, [2, 6]] += 1         # Feature up
    m[3, [2, 6]] -= 1         # NPS down
    return np.clip(m, 1, 10)


def bm2_marketplace() -> np.ndarray:
    m = universal_matrix()
    m[2, [0, 7]] -= 1         # MRR down (GMV-driven)
    m[1, [1]] -= 1            # Retention measurability down
    m[0, [2, 4]] += 1         # DAU up
    m[5, [3]] += 1            # CLV predictive up
    m[5, [6]] -= 1            # CLV experiment-sensitivity down
    m[4, [2]] += 1            # Feature actionability up
    return np.clip(m, 1, 10)


def bm3_b2b() -> np.ndarray:
    m = universal_matrix()
    m[5, [0, 3, 7]] += 1      # CLV up
    m[4, [0, 2, 7]] += 1      # Feature up
    m[2, [0, 7]] += 1         # MRR up
    m[0, [0, 7]] -= 1         # DAU down
    m[3, [4]] += 1            # NPS team-alignment up
    return np.clip(m, 1, 10)


SEGMENT_MATRICES = {"BM1": bm1_saas(), "BM2": bm2_marketplace(), "BM3": bm3_b2b()}
SEGMENT_NAMES = {"BM1": "SaaS / Subscription", "BM2": "Marketplace / Transactional",
                 "BM3": "B2B / Enterprise"}


# ── TOPSIS (Hwang & Yoon 1981; all criteria benefit-type) ────────────────────────
def topsis(matrix: np.ndarray, weights: np.ndarray) -> dict:
    norm = matrix / np.sqrt((matrix ** 2).sum(axis=0))
    weighted = norm * weights
    pis, nis = weighted.max(axis=0), weighted.min(axis=0)
    d_pos = np.sqrt(((weighted - pis) ** 2).sum(axis=1))
    d_neg = np.sqrt(((weighted - nis) ** 2).sum(axis=1))
    cc = d_neg / (d_pos + d_neg)
    ranks = cc.argsort()[::-1].argsort() + 1   # rank 1 = highest CC
    return {"cc": cc, "ranks": ranks}


# ── Survey BWM: per-respondent linear model, then AIP aggregation ─────────────────
def solve_linear_bwm(best: str, worst: str, a_bo: dict, a_ow: dict) -> tuple[np.ndarray, float]:
    """
    Linear BWM (Rezaei 2016): min xi s.t. |w_B - a_Bj*w_j| <= xi and
    |w_j - a_jW*w_W| <= xi for all j, sum(w)=1, w>=0.
    Returns (weight vector in C1..C8 order, consistency xi).
    """
    n = len(JSONKEY_ORDER)
    nv, xi_col = n + 1, n
    bi, wi = JSONKEY_ORDER.index(best), JSONKEY_ORDER.index(worst)
    A_ub, b_ub = [], []

    def add_abs(plus_idx, minus_idx, coeff):
        # |w[plus_idx] - coeff*w[minus_idx]| <= xi  -> two inequalities
        for sign in (1, -1):
            row = [0.0] * nv
            row[plus_idx] += sign
            row[minus_idx] -= sign * coeff
            row[xi_col] -= 1
            A_ub.append(row)
            b_ub.append(0.0)

    for j, key in enumerate(JSONKEY_ORDER):
        if key != best and key in a_bo:
            add_abs(bi, j, a_bo[key])
        if key != worst and key in a_ow:
            add_abs(j, wi, a_ow[key])

    res = linprog(c=[0.0] * n + [1.0], A_ub=A_ub, b_ub=b_ub,
                  A_eq=[[1.0] * n + [0.0]], b_eq=[1.0],
                  bounds=[(0, None)] * nv, method="highs")
    return res.x[:n], float(res.x[xi_col])


def survey_weights(csv_path: Path) -> dict:
    rows = list(csv.DictReader(open(csv_path)))
    per_resp, xis = [], []
    for r in rows:
        try:
            best = D1_TO_KEY[r["d1_best_criterion"]]
            worst = D1_TO_KEY[r["d2_worst_criterion"]]
            a_bo = {k: float(v) for k, v in json.loads(r["d3_best_to_others"]).items()
                    if v not in ("na", None)}
            a_ow = {k: float(v) for k, v in json.loads(r["d4_others_to_worst"]).items()
                    if v not in ("na", None)}
        except (KeyError, json.JSONDecodeError):
            continue
        w, xi = solve_linear_bwm(best, worst, a_bo, a_ow)
        per_resp.append(w)
        xis.append(xi)
    W = np.array(per_resp)
    aip = W.mean(axis=0)
    geo = np.exp(np.log(np.clip(W, 1e-9, None)).mean(axis=0))
    geo /= geo.sum()
    return {"n": len(W), "aip": aip, "geom": geo, "mean_xi": float(np.mean(xis)),
            "per_respondent": W}


# ── Sensitivity: one-at-a-time +/-10% and +/-20%, redistribute proportionally ─────
def oat_sensitivity(matrix: np.ndarray, weights: np.ndarray, base_ranks: np.ndarray) -> list:
    scenarios = []
    for pct in (0.10, 0.20):
        for i in range(len(weights)):
            for sign in (+1, -1):
                w = weights.copy()
                delta = w[i] * pct * sign
                w[i] += delta
                others = [k for k in range(len(w)) if k != i]
                w[others] -= delta * (w[others] / w[others].sum())
                w = np.clip(w, 1e-9, None)
                w /= w.sum()
                ranks = topsis(matrix, w)["ranks"]
                reversed_n = int((ranks != base_ranks).sum())
                scenarios.append({"criterion": CRITERIA[i], "pct": sign * pct,
                                  "rank_reversals": reversed_n})
    return scenarios


# ── Reporting helpers ────────────────────────────────────────────────────────────
def spearman(a: np.ndarray, b: np.ndarray) -> float:
    def ranks(x):
        order = np.argsort(-x)
        rk = np.empty_like(order)
        rk[order] = np.arange(len(x))
        return rk
    d = ranks(a) - ranks(b)
    n = len(a)
    return 1 - 6 * np.sum(d ** 2) / (n * (n ** 2 - 1))


def print_ranking(title: str, cc: np.ndarray, ranks: np.ndarray):
    print(f"\n{title}")
    order = np.argsort(ranks)
    for pos in order:
        print(f"  {ranks[pos]}. {ALTERNATIVES[pos]:18} CC={cc[pos]:.4f}")


def main():
    bundle: dict = {}

    # 1+2 — weights
    sw = survey_weights(SURVEY_CSV)
    rho = spearman(LIT_WEIGHTS, sw["aip"])
    print("=" * 64)
    print("WEIGHTS — literature baseline vs survey expert panel (n=%d)" % sw["n"])
    print("=" * 64)
    print(f"{'criterion':28}{'lit':>7}{'survey_AIP':>12}{'geom':>8}{'Δ':>8}")
    for i, c in enumerate(CRITERIA):
        print(f"{c:28}{LIT_WEIGHTS[i]:7.2f}{sw['aip'][i]:12.3f}{sw['geom'][i]:8.3f}"
              f"{sw['aip'][i] - LIT_WEIGHTS[i]:+8.3f}")
    print(f"\nmean consistency xi = {sw['mean_xi']:.3f} (<0.10 acceptable)")
    print(f"Spearman rho (lit vs survey rank) = {rho:.3f}")
    bundle["weights"] = {"literature": LIT_WEIGHTS.tolist(), "survey_aip": sw["aip"].tolist(),
                         "survey_geom": sw["geom"].tolist(), "mean_xi": sw["mean_xi"],
                         "n": sw["n"], "spearman_rho": rho}

    # 3 — universal TOPSIS, dual weights
    print("\n" + "=" * 64)
    print("UNIVERSAL TOPSIS — dual-weight robustness")
    print("=" * 64)
    bundle["universal"] = {}
    for name, w in [("literature weights", LIT_WEIGHTS), ("survey AIP weights", sw["aip"])]:
        res = topsis(universal_matrix(), w)
        print_ranking(f"[{name}]", res["cc"], res["ranks"])
        bundle["universal"][name] = {"cc": res["cc"].tolist(), "ranks": res["ranks"].tolist()}

    # 4 — segmented TOPSIS (literature weights)
    print("\n" + "=" * 64)
    print("SEGMENTED TOPSIS (literature weights)")
    print("=" * 64)
    bundle["segmented"] = {}
    for code, matrix in SEGMENT_MATRICES.items():
        res = topsis(matrix, LIT_WEIGHTS)
        print_ranking(f"[{code} — {SEGMENT_NAMES[code]}]", res["cc"], res["ranks"])
        bundle["segmented"][code] = {"cc": res["cc"].tolist(), "ranks": res["ranks"].tolist()}

    # 5 — sensitivity on the universal matrix (literature weights)
    base = topsis(universal_matrix(), LIT_WEIGHTS)["ranks"]
    sens = oat_sensitivity(universal_matrix(), LIT_WEIGHTS, base)
    n_stable = sum(1 for s in sens if s["rank_reversals"] == 0)
    print("\n" + "=" * 64)
    print("SENSITIVITY — universal, one-at-a-time ±10%/±20%")
    print("=" * 64)
    print(f"  {n_stable}/{len(sens)} perturbations preserve the full ranking.")
    worst = [s for s in sens if s["rank_reversals"] > 0]
    for s in sorted(worst, key=lambda x: -x["rank_reversals"])[:8]:
        print(f"  {s['criterion']:28} {s['pct']:+.0%}  -> {s['rank_reversals']} reversal(s)")
    bundle["sensitivity"] = {"n_perturbations": len(sens), "n_stable": n_stable,
                             "scenarios": sens}

    OUT_JSON.parent.mkdir(exist_ok=True)
    OUT_JSON.write_text(json.dumps(bundle, indent=2))
    print(f"\nResults bundle written: {OUT_JSON.relative_to(REPO)}")


if __name__ == "__main__":
    main()
