"""
Generate figures from results/phase2/*.json.
  • If matplotlib is available → PNG/PDF files in figures/
  • Always → ASCII text versions in figures/ (for reference / debugging)

Usage: python -m scripts.make_figures
"""
import json
import pathlib
import os

ROOT    = pathlib.Path(__file__).parent.parent
RES     = ROOT / "results" / "phase2"
FIG_DIR = ROOT / "figures"
FIG_DIR.mkdir(exist_ok=True)

# ── data loading ─────────────────────────────────────────────────────────────

def load(name):
    with open(RES / name) as f:
        return json.load(f)

# ── ASCII bar helpers ─────────────────────────────────────────────────────────

def ascii_bar(value, max_value, width=40, fill="█"):
    n = int(round(value / max_value * width)) if max_value else 0
    return fill * n + "░" * (width - n)

def ascii_hbar_chart(title, labels, values, unit="", width=40):
    if not values:
        return f"[{title}]\n(no data)\n"
    max_v = max(values) or 1
    lines = [f"\n{'─'*60}", f"  {title}", f"{'─'*60}"]
    max_lbl = max(len(l) for l in labels)
    for lbl, v in zip(labels, values):
        bar = ascii_bar(v, max_v, width)
        lines.append(f"  {lbl:<{max_lbl}}  {bar}  {v:.4f}{unit}")
    lines.append(f"{'─'*60}\n")
    return "\n".join(lines)

# ── Figure 2: tradeoff (pause-aligned rate vs scaffold count) ─────────────────

def fig2_tradeoff(exp):
    labels  = []
    pa_vals = []
    sc_vals = []

    # E1
    labels.append("E1 Rule baseline")
    pa_vals.append(exp["e1_rule_baseline"]["pause_aligned_rate"])
    sc_vals.append(exp["e1_rule_baseline"]["scaffold_count"])

    # E2 pause model (mean)
    e2p = [r for r in exp["e2_on_demand"] if r["model"] == "pause"]
    labels.append("E2 On-demand (pause)")
    pa_vals.append(sum(r["pause_aligned_rate"] for r in e2p) / len(e2p))
    sc_vals.append(sum(r["scaffolds_delivered"] for r in e2p) / len(e2p))

    # E3
    labels.append("E3 Full system")
    pa_vals.append(exp["e3_full_system"]["pause_aligned_rate"])
    sc_vals.append(exp["e3_full_system"]["scaffold_count"])

    # E5 ablations (non-full)
    for a in exp["e5_ablations"]:
        if a["name"] != "full_system":
            labels.append(f"  E5 {a['desc'][:25]}")
            pa_vals.append(a["pause_aligned_rate"])
            sc_vals.append(a["scaffold_count"])

    lines  = [ascii_hbar_chart("Fig 2a: Pause-aligned rate by condition",
                               labels, pa_vals, unit="")]
    lines += [ascii_hbar_chart("Fig 2b: Scaffold count by condition",
                               labels, sc_vals, unit=" scaffolds")]

    out = "\n".join(lines)
    path = FIG_DIR / "fig2_tradeoff.txt"
    path.write_text(out, encoding="utf-8")
    print(f"[make_figures] wrote {path}")
    return out

# ── Figure 3: ablation ────────────────────────────────────────────────────────

def fig3_ablation(exp):
    rows = exp["e5_ablations"]
    labels = [r["desc"] for r in rows]
    pa     = [r["pause_aligned_rate"] for r in rows]
    ir     = [r["interruption_rate"]  for r in rows]

    out  = ascii_hbar_chart("Fig 3a: Ablation — Pause-aligned rate", labels, pa)
    out += ascii_hbar_chart("Fig 3b: Ablation — Deliberation delta (s)",
                            labels, [r["deliberation_delta"] for r in rows], unit="s")

    path = FIG_DIR / "fig3_ablation.txt"
    path.write_text(out, encoding="utf-8")
    print(f"[make_figures] wrote {path}")
    return out

# ── Figure 4: transfer sensitivity ───────────────────────────────────────────

def fig4_transfer(tr):
    sens   = tr["sensitivity"]
    labels = [f"n_tasks={s['n_tasks']}" for s in sens]
    rhos   = [s["spearman_r"]           for s in sens]

    out  = ascii_hbar_chart("Fig 4: Transfer sensitivity (Spearman ρ vs n_tasks)",
                            labels, rhos)
    # Also show condition means
    cond_labels = [c["condition"]          for c in tr["conditions"]]
    cond_vals   = [c["mean_transfer_r"]    for c in tr["conditions"]]
    out += ascii_hbar_chart("Fig 4b: Transfer ρ by condition",
                            cond_labels, cond_vals)

    path = FIG_DIR / "fig4_transfer.txt"
    path.write_text(out, encoding="utf-8")
    print(f"[make_figures] wrote {path}")
    return out

# ── Figure 5: failure types ───────────────────────────────────────────────────

def fig5_failures(fa):
    fts    = fa["failure_types"]
    labels = [f"[{k}] {v['label'][:40]}" for k, v in fts.items()]
    counts = [v["count"] for v in fts.values()]

    out  = ascii_hbar_chart("Fig 5: Failure-mode distribution",
                            labels, counts, unit=" junctures")
    # Annotate total
    out += f"\n  Total junctures: {fa['total_junctures']:,}\n"

    path = FIG_DIR / "fig5_failures.txt"
    path.write_text(out, encoding="utf-8")
    print(f"[make_figures] wrote {path}")
    return out

# ── matplotlib versions (if available) ───────────────────────────────────────

def try_matplotlib(exp, tr, fa):
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
        import matplotlib.patches as mpatches
    except ImportError:
        print("[make_figures] matplotlib not installed; skipping PNG/PDF output.")
        print("[make_figures] Install with:  pip install matplotlib")
        return

    print("[make_figures] matplotlib found — generating PNG figures...")

    # --- Fig 2: tradeoff scatter ---
    fig, ax = plt.subplots(figsize=(6, 4))
    colors = {"E1": "tab:red", "E2": "tab:orange", "E3": "tab:green", "E5": "tab:blue"}
    pts = {
        "E1 Rule baseline":    (exp["e1_rule_baseline"]["scaffold_count"],
                                exp["e1_rule_baseline"]["pause_aligned_rate"]),
        "E3 Full system":      (exp["e3_full_system"]["scaffold_count"],
                                exp["e3_full_system"]["pause_aligned_rate"]),
    }
    e2p = [r for r in exp["e2_on_demand"] if r["model"] == "pause"]
    pts["E2 On-demand (pause)"] = (
        sum(r["scaffolds_delivered"] for r in e2p) / len(e2p),
        sum(r["pause_aligned_rate"]  for r in e2p) / len(e2p),
    )
    for abl in exp["e5_ablations"]:
        if abl["name"] != "full_system":
            pts[f"E5 {abl['desc'][:20]}"] = (
                abl["scaffold_count"], abl["pause_aligned_rate"])

    for label, (x, y) in pts.items():
        prefix = label[:2]
        c = colors.get(prefix, "tab:gray")
        ax.scatter(x, y, color=c, s=80, zorder=3)
        ax.annotate(label, (x, y), textcoords="offset points",
                    xytext=(5, 3), fontsize=6)

    ax.set_xlabel("Scaffold count")
    ax.set_ylabel("Pause-aligned rate")
    ax.set_title("Fig 2: Interruption-coverage trade-off")
    ax.grid(True, alpha=0.3)
    fig.tight_layout()
    fig.savefig(FIG_DIR / "fig2_tradeoff.png", dpi=150)
    plt.close(fig)
    print(f"[make_figures] wrote {FIG_DIR / 'fig2_tradeoff.png'}")

    # --- Fig 3: ablation bar chart ---
    rows   = exp["e5_ablations"]
    names  = [r["desc"][:28] for r in rows]
    pa_vals = [r["pause_aligned_rate"] for r in rows]
    fig, ax = plt.subplots(figsize=(8, 4))
    ax.barh(names, pa_vals, color="steelblue")
    ax.set_xlabel("Pause-aligned rate")
    ax.set_title("Fig 3: Ablation — pause-aligned rate (E5)")
    ax.set_xlim(0, 1.05)
    fig.tight_layout()
    fig.savefig(FIG_DIR / "fig3_ablation.png", dpi=150)
    plt.close(fig)
    print(f"[make_figures] wrote {FIG_DIR / 'fig3_ablation.png'}")

    # --- Fig 4: transfer sensitivity ---
    sens = tr["sensitivity"]
    xs   = [s["n_tasks"]    for s in sens]
    ys   = [s["spearman_r"] for s in sens]
    sds  = [s["sd"]         for s in sens]
    fig, ax = plt.subplots(figsize=(5, 4))
    ax.errorbar(xs, ys, yerr=sds, fmt="-o", color="darkorange", capsize=4)
    ax.set_xlabel("Number of tasks")
    ax.set_ylabel("Spearman ρ")
    ax.set_title("Fig 4: Transfer sensitivity (N=120 simulated learners)")
    ax.set_ylim(0.9, 1.0)
    ax.grid(True, alpha=0.3)
    fig.tight_layout()
    fig.savefig(FIG_DIR / "fig4_transfer.png", dpi=150)
    plt.close(fig)
    print(f"[make_figures] wrote {FIG_DIR / 'fig4_transfer.png'}")

    # --- Fig 5: failure types ---
    fts    = fa["failure_types"]
    labels = [f"[{k}] {v['label'][:35]}" for k, v in fts.items()]
    counts = [v["count"] for v in fts.values()]
    fig, ax = plt.subplots(figsize=(8, 4))
    ax.barh(labels, counts, color="tomato")
    ax.set_xlabel("Count")
    ax.set_title(f"Fig 5: Failure-mode distribution ({fa['total_junctures']:,} junctures)")
    fig.tight_layout()
    fig.savefig(FIG_DIR / "fig5_failures.png", dpi=150)
    plt.close(fig)
    print(f"[make_figures] wrote {FIG_DIR / 'fig5_failures.png'}")

    print("[make_figures] PNG figures complete.")

# ── main ─────────────────────────────────────────────────────────────────────

def main():
    exp = load("experiments_test.json")
    tr  = load("e4_g3_transfer.json")
    fa  = load("failure_analysis.json")

    fig2_tradeoff(exp)
    fig3_ablation(exp)
    fig4_transfer(tr)
    fig5_failures(fa)
    try_matplotlib(exp, tr, fa)

    print("\n[make_figures] Done. ASCII files (fig1-fig5) in figures/")

if __name__ == "__main__":
    main()
