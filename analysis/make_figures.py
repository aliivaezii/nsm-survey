"""
Generate the manuscript figures from the frozen analysis bundle.

Reads outputs/analysis_results.json (run_analysis.py) and writes publication
figures (PNG + PDF) to outputs/figures/.

Design principle: color carries identity on screen, but every figure must also
survive black-and-white print. Series are therefore distinguished by a
CVD-validated palette (Okabe-Ito-class separation, checked with the dataviz
palette validator) AND by a redundant channel: hatch pattern, line style,
marker shape, luminance step, and direct labels. Statistics shown inside
figures (rho, n) are read from the bundle, never hardcoded, so figures can
never drift from the analysis.

Run order: python run_analysis.py  &&  python make_figures.py
"""

import json
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.colors import LinearSegmentedColormap

REPO = Path(__file__).resolve().parents[1]
BUNDLE = json.loads((REPO / "outputs" / "analysis_results.json").read_text())
FIGDIR = REPO / "outputs" / "figures"
FIGDIR.mkdir(parents=True, exist_ok=True)

N = BUNDLE["weights"]["n"]
RHO = BUNDLE["weights"]["spearman_rho"]

# CVD-validated categorical slots (light surface) + a sequential blue ramp.
# Luminance is deliberately staggered (violet dark, blue mid, yellow light)
# so the categorical set stays distinct in grayscale print.
BLUE = "#2A78D6"
YELLOW = "#EDA100"
VIOLET = "#4A3AA7"
RED = "#E34948"
GREY_DK = "#52514E"
GREY_LT = "#898781"
SEQ = ["#CDE2FB", "#86B6EF", "#2A78D6", "#104281"]   # light -> dark blue ramp
BLUES_CMAP = LinearSegmentedColormap.from_list("seqblue", ["#F5F9FE"] + SEQ)

CRITERIA = ["C1 Value\nAlign.", "C2 Measur.", "C3 Action.", "C4 Predict.",
            "C5 Team\nAlign.", "C6 Gaming\nRes.", "C7 Exp.\nSens.", "C8 Strat.\nFit"]
ALTS = ["DAU", "Retention", "MRR", "NPS", "Feature\nAdoption", "CLV"]

# Journal style: no in-figure titles (the caption names the figure), hairline
# y-grid behind the marks, recessive axes.
plt.rcParams.update({"font.size": 10, "axes.spines.top": False, "axes.spines.right": False,
                     "hatch.linewidth": 0.8, "axes.axisbelow": True,
                     "grid.color": "#E1E0D9", "grid.linewidth": 0.7})


def save(fig, name):
    for ext in ("png", "pdf"):
        fig.savefig(FIGDIR / f"{name}.{ext}", dpi=300, bbox_inches="tight")
    plt.close(fig)


def fig1_weights():
    """Two series: solid blue vs white-with-blue-hatch. Dark/white in grayscale.
    Value labels on every bar so the exact weights are readable without the table."""
    lit = np.array(BUNDLE["weights"]["literature"])
    aip = np.array(BUNDLE["weights"]["survey_aip"])
    x = np.arange(len(CRITERIA))
    w = 0.38
    fig, ax = plt.subplots(figsize=(9, 4.3))
    b1 = ax.bar(x - w / 2, lit, w, label="Literature baseline",
                facecolor=BLUE, edgecolor="black", linewidth=0.6)
    b2 = ax.bar(x + w / 2, aip, w, label=f"Expert panel, AIP (n = {N})",
                facecolor="white", edgecolor=BLUE, linewidth=0.9, hatch="////")
    for bars in (b1, b2):
        for rect in bars:
            ax.annotate(f"{rect.get_height():.2f}".lstrip("0"),
                        (rect.get_x() + rect.get_width() / 2, rect.get_height()),
                        xytext=(0, 2), textcoords="offset points",
                        ha="center", va="bottom", fontsize=7.5, color="#0B0B0B")
    ax.set_xticks(x); ax.set_xticklabels(CRITERIA)
    ax.set_ylabel("Criterion weight")
    ax.set_ylim(0, 0.205)
    ax.yaxis.grid(True)
    ax.legend(frameon=False, ncol=2, loc="upper center", bbox_to_anchor=(0.5, 1.06))
    save(fig, "fig1_weights_lit_vs_survey")


def fig2_segmented():
    """Three archetypes: staggered-luminance hues + hatch so grayscale still separates."""
    seg = BUNDLE["segmented"]
    codes = ["BM1", "BM2", "BM3"]
    names = {"BM1": "SaaS/Subscription", "BM2": "Marketplace/Transactional", "BM3": "B2B/Enterprise"}
    styles = {"BM1": dict(facecolor=BLUE, hatch=""),
              "BM2": dict(facecolor=YELLOW, hatch="////"),
              "BM3": dict(facecolor=VIOLET, hatch="xxxx")}
    x = np.arange(len(ALTS))
    w = 0.26
    fig, ax = plt.subplots(figsize=(9, 4.7))
    for i, code in enumerate(codes):
        cc = np.array(seg[code]["cc"])
        ax.bar(x + (i - 1) * w, cc, w, label=f"{code}: {names[code]}",
               edgecolor="black", linewidth=0.6, **styles[code])
    ax.set_xticks(x); ax.set_xticklabels(ALTS)
    ax.set_ylabel("TOPSIS closeness coefficient (CC$_i$)")
    ax.yaxis.grid(True)
    ax.legend(frameon=False, fontsize=9)
    save(fig, "fig2_segmented_cc")


def fig3_sensitivity_heatmap():
    """Single-hue sequential ramp (monotonic luminance) with cell counts for B&W safety."""
    scen = BUNDLE["sensitivity"]["scenarios"]
    crit_order = ["C1 Value Alignment", "C2 Measurability", "C3 Actionability",
                  "C4 Predictive Power", "C5 Team Alignment", "C6 Gaming Resistance",
                  "C7 Experiment Sensitivity", "C8 Strategic Fit"]
    pcts = [-0.20, -0.10, 0.10, 0.20]
    M = np.zeros((len(crit_order), len(pcts)))
    for s in scen:
        M[crit_order.index(s["criterion"]), pcts.index(round(s["pct"], 2))] = s["rank_reversals"]
    fig, ax = plt.subplots(figsize=(7, 5.5))
    im = ax.imshow(M, cmap=BLUES_CMAP, aspect="auto", vmin=0, vmax=M.max())
    ax.set_xticks(range(len(pcts))); ax.set_xticklabels(["-20%", "-10%", "+10%", "+20%"])
    ax.set_yticks(range(len(crit_order)))
    ax.set_yticklabels([c.replace(" ", "\n", 1) for c in crit_order])
    ax.set_xlabel("Weight perturbation")
    for i in range(len(crit_order)):
        for j in range(len(pcts)):
            v = int(M[i, j])
            ax.text(j, i, v, ha="center", va="center",
                    color="white" if v > M.max() * 0.55 else "black", fontsize=10)
    cbar = fig.colorbar(im, ax=ax, shrink=0.8)
    cbar.set_label("# rank reversals vs. baseline")
    save(fig, "fig3_sensitivity_heatmap")


def fig_litgap():
    """Three-stream positioning. Soft translucent tints (overlaps blend naturally),
    stream names OUTSIDE the lobes with a one-line descriptor, center chip for
    the study. Luminance-distinct tints + direct labels keep it print-safe."""
    from matplotlib.patches import Circle
    fig, ax = plt.subplots(figsize=(8.6, 7.2))
    ax.set_xlim(0, 10.6); ax.set_ylim(0.4, 10); ax.axis("off")
    ax.set_aspect("equal")
    r = 2.55
    circ = [((3.9, 6.35), BLUE,
             "NSM and\ngrowth-metric theory", "what a North Star is for",
             (0.35, 9.35), "left", 0.85),
            ((6.7, 6.35), YELLOW,
             "KPIs by\nbusiness model", "which metrics fit which model",
             (10.25, 9.35), "right", 0.85),
            ((5.3, 4.05), VIOLET,
             "MCDM methods (BWM, TOPSIS)", "how to weight and rank formally",
             (5.3, 0.95), "center", 0.5)]
    for (x, y), col, _, _, _, _, _ in circ:
        ax.add_patch(Circle((x, y), r, facecolor=col, edgecolor="none", alpha=0.28, zorder=1))
        ax.add_patch(Circle((x, y), r, facecolor="none", edgecolor=col, linewidth=1.8, zorder=4))
    for (x, y), col, name, desc, (lx, ly), halign, dgap in circ:
        ax.text(lx, ly, name, ha=halign, va="center", fontsize=11,
                fontweight="bold", color=col, zorder=5)
        ax.text(lx, ly - dgap, desc, ha=halign, va="center", fontsize=9,
                style="italic", color="#52514E", zorder=5)
    ax.text(5.3, 5.6, "This study:\ncontext-aware, validated\nNSM selection",
            ha="center", va="center", fontsize=10.5, fontweight="bold", color="white",
            bbox=dict(boxstyle="round,pad=0.4", fc="#104281", ec="black", lw=1.1), zorder=6)
    save(fig, "fig_litgap")


def fig_framework():
    """Vertical three-phase pipeline; validation rail entries aligned with their arrows."""
    from matplotlib.patches import FancyBboxPatch, FancyArrowPatch
    fig, ax = plt.subplots(figsize=(9, 8.6))
    ax.set_xlim(0, 10); ax.set_ylim(0, 10.2); ax.axis("off")

    LX, LW, BH = 0.5, 5.0, 1.65
    # (y_bottom, head, body, facecolor, textcolor) -- sequential blue ramp
    phases = [
        (8.2, "Phase 1   Criteria derivation",
         "Gioia coding of literature and expert input\n$\\Rightarrow$ eight criteria (C1 to C8)", SEQ[0], "black"),
        (5.75, "Phase 2   Criterion weighting",
         "Best-Worst Method (linear model)\n$\\Rightarrow$ criterion weight vector", SEQ[1], "black"),
        (3.3, "Phase 3   Alternative ranking",
         "TOPSIS over six candidate NSMs\n$\\Rightarrow$ closeness coefficient and universal rank", SEQ[2], "white"),
        (0.85, "Segmentation",
         "Re-run per archetype BM1 / BM2 / BM3\n$\\Rightarrow$ context-specific rankings", SEQ[3], "white"),
    ]
    centers = []
    for yb, head, body, fc, tc in phases:
        ax.add_patch(FancyBboxPatch((LX, yb), LW, BH, boxstyle="round,pad=0.04,rounding_size=0.12",
                                    fc=fc, ec="black", lw=1.0))
        ax.text(LX + LW / 2, yb + BH - 0.34, head, ha="center", va="top", color=tc,
                fontsize=11, fontweight="bold")
        ax.text(LX + LW / 2, yb + BH - 0.92, body, ha="center", va="top", color=tc, fontsize=9)
        centers.append(yb + BH / 2)
    # downward arrows between phases
    for a, b in zip(phases[:-1], phases[1:]):
        ax.add_patch(FancyArrowPatch((LX + LW / 2, a[0]), (LX + LW / 2, b[0] + BH),
                                     arrowstyle="-|>", mutation_scale=18, color="black", lw=1.6))

    # validation rail (right); every entry sits exactly at the y of its arrow
    RX, RW = 6.6, 3.0
    ax.add_patch(FancyBboxPatch((RX, 0.85), RW, 9.0, boxstyle="round,pad=0.04,rounding_size=0.12",
                                fc="white", ec="black", lw=1.0))
    ax.text(RX + RW / 2, 9.55, "Validation and\nrobustness", ha="center", va="top",
            fontsize=10.5, fontweight="bold", color="black")
    rail = [(centers[1], f"Expert-panel BWM weights\n(n = {N}, rho = {RHO:.3f})"),
            (centers[2], "Survey-derived decision\nmatrix (same endpoints)"),
            (centers[3] + 0.45, "Dual-weight TOPSIS"),
            (centers[3] - 0.45, "Sensitivity sweep\n($\\pm$10% / $\\pm$20%)")]
    for y, txt in rail:
        ax.text(RX + RW / 2, y, txt, ha="center", va="center", fontsize=8.6, color="black")
    # one horizontal arrow per validated phase, at the exact y of its rail entry
    for y in (centers[1], centers[2], centers[3]):
        ax.add_patch(FancyArrowPatch((RX, y), (LX + LW, y), arrowstyle="-|>",
                                     mutation_scale=14, color="black", lw=1.1,
                                     linestyle=(0, (4, 2))))
    save(fig, "fig_framework")


def fig_rankflow():
    """Bump chart. The two protagonists get validated hues; the rest recede in gray.
    Line style + marker + direct labels keep it legible in grayscale print."""
    ctx = ["Universal", "BM1\nSaaS", "BM2\nMarketplace", "BM3\nB2B"]
    uni = BUNDLE["universal"]["literature weights"]["ranks"]
    seg = BUNDLE["segmented"]
    order = ["DAU", "Retention (D30)", "Revenue/MRR", "NPS", "Feature Adoption", "CLV"]
    short = {"DAU": "DAU", "Retention (D30)": "Retention", "Revenue/MRR": "MRR",
             "NPS": "NPS", "Feature Adoption": "Feature Adoption", "CLV": "CLV"}
    ranks = {nm: [uni[i], seg["BM1"]["ranks"][i], seg["BM2"]["ranks"][i], seg["BM3"]["ranks"][i]]
             for i, nm in enumerate(order)}
    # (linestyle, marker, linewidth, color)
    style = {"Retention (D30)": ("-", "o", 3.0, BLUE),
             "Feature Adoption": ("--", "s", 3.0, RED),
             "Revenue/MRR": ("-.", "^", 1.8, GREY_DK),
             "CLV": (":", "D", 1.8, GREY_DK),
             "DAU": ("-", "v", 1.5, GREY_LT),
             "NPS": ("--", "*", 1.5, GREY_LT)}
    fig, ax = plt.subplots(figsize=(9, 5.6))
    x = list(range(4))
    for nm in order:
        ls, mk, lw, col = style[nm]
        y = ranks[nm]
        ax.plot(x, y, linestyle=ls, marker=mk, color=col, lw=lw, ms=8,
                markerfacecolor="white" if lw < 2 else col, markeredgecolor=col,
                zorder=3 if lw >= 3 else 2)
        ax.text(-0.08, y[0], short[nm], ha="right", va="center", fontsize=9.5, color=col)
        ax.text(3.08, y[3], short[nm], ha="left", va="center", fontsize=9.5,
                fontweight="bold" if lw >= 3 else "normal", color=col)
    ax.set_yticks(range(1, 7)); ax.set_yticklabels(range(1, 7))
    ax.invert_yaxis()
    ax.set_xticks(x); ax.set_xticklabels(ctx)
    ax.set_xlim(-1.15, 4.05); ax.set_ylabel("TOPSIS rank (1 = best)")
    ax.spines["left"].set_visible(False); ax.tick_params(left=False)
    save(fig, "fig_rankflow")


def graphical_abstract():
    """Elsevier-proportioned (13:5) schematic. Column flow inputs -> methods ->
    segmentation -> one arrow per outcome box; bold border marks the key result."""
    from matplotlib.patches import FancyBboxPatch, FancyArrowPatch
    fig, ax = plt.subplots(figsize=(13, 5))
    ax.set_xlim(0, 13); ax.set_ylim(0, 5); ax.axis("off")
    ax.text(6.5, 4.88, "A Context-Aware Framework for North Star Metric Selection",
            ha="center", va="top", fontsize=16, fontweight="bold", color="black")

    def box(x, y, w, h, text, fc, tc, fs=10, lw=1.0):
        ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.04,rounding_size=0.1",
                                    fc=fc, ec="black", lw=lw))
        ax.text(x + w / 2, y + h / 2, text, ha="center", va="center",
                color=tc, fontsize=fs, fontweight="bold")

    def arrow(x1, y1, x2, y2):
        ax.add_patch(FancyArrowPatch((x1, y1), (x2, y2), arrowstyle="-|>",
                                     mutation_scale=15, color="black", lw=1.5,
                                     shrinkA=0, shrinkB=0))

    # column 1: inputs
    box(0.3, 2.45, 2.4, 1.15, "8 criteria (C1 to C8)\nGioia coding", SEQ[0], "black", 9.5)
    box(0.3, 0.85, 2.4, 1.15, "6 candidate NSMs\nDAU to CLV", SEQ[0], "black", 9.5)
    # column 2: methods
    box(3.4, 2.45, 2.5, 1.15, f"BWM criterion weights\nn = {N}, rho = {RHO:.3f}",
        SEQ[1], "black", 9.5)
    box(3.4, 0.85, 2.5, 1.15, "TOPSIS\nrank by CC$_i$", SEQ[1], "black", 9.5)
    # column 3: segmentation hub
    seg_x, seg_y, seg_w, seg_h = 6.6, 1.62, 2.15, 1.2
    box(seg_x, seg_y, seg_w, seg_h, "Segment by\nbusiness model\nBM1 / BM2 / BM3", SEQ[2], "white", 9.5)
    # column 4: one outcome box per arrow, evenly stacked
    out_x, out_w, out_h = 9.6, 3.1, 0.78
    outcomes = [
        (3.42, "SaaS: Retention", SEQ[0], "black", 1.0),
        (2.47, "Marketplace: Retention", SEQ[1], "black", 1.0),
        (1.52, "B2B: Feature Adoption", SEQ[3], "white", 2.4),
        (0.57, "NPS: last in every model", "white", "black", 1.0),
    ]
    for yb, txt, fc, tc, lw in outcomes:
        box(out_x, yb, out_w, out_h, txt, fc, tc, 10, lw)

    # flow arrows: inputs -> methods (level), methods -> hub (converging)
    arrow(2.7, 3.02, 3.4, 3.02)
    arrow(2.7, 1.42, 3.4, 1.42)
    arrow(5.9, 3.02, seg_x, seg_y + seg_h * 0.75)
    arrow(5.9, 1.42, seg_x, seg_y + seg_h * 0.25)
    # hub -> outcomes: one arrow per box, fanning from the hub's right edge
    hub_cy = seg_y + seg_h / 2
    for yb, *_ in outcomes:
        arrow(seg_x + seg_w, hub_cy, out_x, yb + out_h / 2)

    ax.text(4.65, 0.32, "The optimal North Star Metric is context-dependent",
            ha="center", va="center", fontsize=11, style="italic", color="black")
    save(fig, "graphical_abstract")


if __name__ == "__main__":
    fig1_weights()
    fig2_segmented()
    fig3_sensitivity_heatmap()
    fig_litgap()
    fig_framework()
    fig_rankflow()
    graphical_abstract()
    print("Figures written to", FIGDIR.relative_to(REPO))
    for f in sorted(FIGDIR.glob("*.png")):
        print("  ", f.name)
