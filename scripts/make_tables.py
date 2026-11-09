"""
Generate LaTeX tables from results/phase2/*.json.
Writes to paper/tables/ AND prints to stdout.
Usage: python -m scripts.make_tables
"""
import json
import pathlib
import os

ROOT = pathlib.Path(__file__).parent.parent
RES  = ROOT / "results" / "phase2"
TAB  = ROOT / "paper" / "tables"
TAB.mkdir(parents=True, exist_ok=True)

def load(name):
    with open(RES / name) as f:
        return json.load(f)

# ── helpers ──────────────────────────────────────────────────────────────────

def write(name: str, content: str):
    path = TAB / name
    path.write_text(content, encoding="utf-8")
    print(f"[make_tables] wrote {path}")
    print(content)

# ── Table 1: Main results (E1, E2 mean, E3) ──────────────────────────────────

def make_main():
    exp = load("experiments_test.json")

    e1  = exp["e1_rule_baseline"]
    e3  = exp["e3_full_system"]
    # E2: average pause model (seeds 0-2)
    e2_pause = [r for r in exp["e2_on_demand"] if r["model"] == "pause"]
    e2_sc = sum(r["scaffolds_delivered"] for r in e2_pause) / len(e2_pause)
    e2_pa = sum(r["pause_aligned_rate"]  for r in e2_pause) / len(e2_pause)
    e2_dd = sum(r["deliberation_delta"]  for r in e2_pause) / len(e2_pause)

    ci_lo = e3["bootstrap_ci"]["deliberation_delta"][0]
    ci_hi = e3["bootstrap_ci"]["deliberation_delta"][1]

    tex = r"""\begin{table}[t]
\caption{Main system results on the test split (8 learners, 726\,897 events).
$\Delta_{\text{delib}}$ = mean seconds of deliberation time before scaffold delivery;
lower is better for E3 (gate holds until pause).
Bootstrap 95\,\% CI for E3 shown in parentheses.}
\label{tab:main}
\centering
\begin{tabular}{lrrrr}
\toprule
System & Scaffolds & Pause-aligned & Interrupted & $\Delta_{\text{delib}}$ (s) \\
\midrule
""" + \
        f"E1 Rule baseline & {e1['scaffold_count']:,} & {e1['pause_aligned_rate']:.4f} & {e1['interruption_rate']:.4f} & {e1['deliberation_delta']:.1f} \\\\\n" + \
        f"E2 On-demand (pause) & {e2_sc:.0f} & {e2_pa:.4f} & 0.0000 & {e2_dd:.1f} \\\\\n" + \
        f"E3 Full system & {e3['scaffold_count']:,} & {e3['pause_aligned_rate']:.4f} & {e3['interruption_rate']:.4f} & {e3['deliberation_delta']:.1f} ({ci_lo:.1f}--{ci_hi:.1f}) \\\\\n" + \
r"""\bottomrule
\end{tabular}
\end{table}
"""
    write("main.tex", tex)

# ── Table 2: Ablation (E5) ────────────────────────────────────────────────────

def make_ablation():
    exp = load("experiments_test.json")
    rows = exp["e5_ablations"]

    tex = r"""\begin{table}[t]
\caption{Ablation study (E5): effect of removing individual components on the test split.
Full system is repeated for reference.}
\label{tab:ablation}
\centering
\begin{tabular}{lrrrr}
\toprule
Variant & Scaffolds & Pause-aligned & Interrupted & $\Delta_{\text{delib}}$ (s) \\
\midrule
"""
    for r in rows:
        name = r["desc"].replace("_", r"\_")
        tex += (f"{name} & {r['scaffold_count']:,} & "
                f"{r['pause_aligned_rate']:.4f} & "
                f"{r['interruption_rate']:.4f} & "
                f"{r['deliberation_delta']:.1f} \\\\\n")

    tex += r"""\bottomrule
\end{tabular}
\end{table}
"""
    write("ablation.tex", tex)

# ── Table 3: Efficiency (E6) ──────────────────────────────────────────────────

def make_efficiency():
    exp = load("experiments_test.json")
    e6  = exp["e6_efficiency"]
    rb  = e6["rule_baseline"]

    tex = r"""\begin{table}[t]
\caption{Runtime efficiency (E6) on the test split.}
\label{tab:efficiency}
\centering
\begin{tabular}{lrrr}
\toprule
System & Runtime (s) & Events/s & Peak memory (MB) \\
\midrule
""" + \
        f"Rule baseline & {rb['runtime_seconds']:.1f} & {rb['events_per_second']:,.0f} & {rb['peak_memory_mb']:.1f} \\\\\n" + \
        f"Full system (E3) & {e6['runtime_seconds']:.1f} & {e6['events_per_second']:,.0f} & {e6['peak_memory_mb']:.1f} \\\\\n" + \
r"""\bottomrule
\end{tabular}
\end{table}
"""
    write("efficiency.tex", tex)

# ── Table 4: Failure analysis ─────────────────────────────────────────────────

def make_failures():
    fa  = load("failure_analysis.json")
    tot = fa["total_junctures"]
    fts = fa["failure_types"]

    tex = r"""\begin{table}[t]
\caption{Failure-mode analysis across """ + str(tot) + r""" junctures on the test split.}
\label{tab:failures}
\centering
\begin{tabular}{clrr}
\toprule
\# & Failure type & Count & Share \\
\midrule
"""
    for k, v in fts.items():
        label = v["label"].replace("(", r"\textit{(").replace(")", r")}") \
                          if "(" in v["label"] else v["label"]
        tex += f"{k} & {label} & {v['count']:,} & {v['share']:.4f} \\\\\n"

    tex += r"""\bottomrule
\end{tabular}
\end{table}
"""
    write("failures.tex", tex)

# ── Table 5: Transfer study (G3) ─────────────────────────────────────────────

def make_transfer():
    tr = load("e4_g3_transfer.json")

    tex = r"""\begin{table}[t]
\caption{Transfer study (G3): mean Spearman $\rho$ across 5 seeds, $N=120$ simulated learners.}
\label{tab:transfer}
\centering
\begin{tabular}{lrr}
\toprule
Condition & Mean transfer $\rho$ & Mean assisted completion $r$ \\
\midrule
"""
    for cond in tr["conditions"]:
        name = cond["condition"].replace("_", r"\_")
        tex += (f"{name} & {cond['mean_transfer_r']:.4f} & "
                f"{cond['mean_assisted_r']:.4f} \\\\\n")

    tex += r"""\bottomrule
\end{tabular}
\end{table}
"""
    write("transfer.tex", tex)

# ── Table 6: Gap-resolution ───────────────────────────────────────────────────

def make_gaps():
    tex = r"""\begin{table}[t]
\caption{Phase~1 gap-resolution table: identified deficiencies and Phase~2 fixes.}
\label{tab:gaps}
\centering
\begin{tabular}{p{3.5cm}p{3cm}p{4cm}}
\toprule
Gap & Phase~1 symptom & Phase~2 fix \\
\midrule
Interrupt risk & Scaffolds fire mid-burst & G1 timing gate: hold until pause $\geq 45$\,s \\
Thin evidence  & Advice on 1--4 events & G2 evidence floor: require $\geq 5$ window events \\
No baseline    & Nothing to compare against & E2 three on-demand models \\
No transfer    & Single-domain evaluation & G3 simulated transfer study \\
No efficiency  & Runtime not measured & E6 events/s and peak memory \\
\bottomrule
\end{tabular}
\end{table}
"""
    write("gaps.tex", tex)

# ── main ─────────────────────────────────────────────────────────────────────

def main():
    make_main()
    make_ablation()
    make_efficiency()
    make_failures()
    make_transfer()
    make_gaps()
    print("\n[make_tables] Done. Files written to paper/tables/")

if __name__ == "__main__":
    main()
