# Phase 2 — Complete Plan, Status and Reference

**AI4015 Agentic Artificial Intelligence, Fall 2026 — Phase 2**
Project **G3-11** · Minahil Kashif (23i-0554, group head) · Areeba Javed (23i-0570) · Supervisor: Naeem Tareen
Repository: `https://github.com/Areeba444/TrajectoryCoach`

> **Status, 9 November.** The original deadline was 8 November 2026, 23:55 PKT. **The supervisor has granted an extension** — confirm the new date and work back from it. This document was updated on 9 November after auditing what was actually committed to GitHub; see the entry for that date in `docs/devlog.md`.

---

## Part 0 — How to read this document

| Section | What it gives you |
|---|---|
| Part 1 | What the brief demands, deliverable by deliverable, with marks |
| Part 2 | Honest status: done, partly done, not done |
| Part 3 | **Every result number**, so you can write without opening a JSON file |
| Part 4 | Remaining steps in order, with exact commands |
| Part 5 | The paper, section by section, with which number belongs where |
| Part 6 | Git, release and submission mechanics |
| Part 7 | Turnitin |
| Part 8 | Honesty rules — the things that will cost you marks if fudged |
| Part 9 | Viva preparation |
| Part 10 | File map |

---

## Part 1 — What Phase 2 requires

### Deliverable A — Code and system (40 marks)

Verified against Section 10 of the brief on 9 November.

| Rubric | Requirement | Marks |
|---|---|---|
| A1 | Complete agentic pipeline: runs end to end on the full evaluation set, genuine tool or environment interaction, logged trajectories | 10 |
| A2 | Gap-specific components: one clear component per gap, switchable for ablation | 10 |
| A3 | Robustness and iterative improvement: failure handling, verification, dev log showing measured improvements | 5 |
| A4 | Repository quality and documentation: clean modular structure, complete README, tests, meaningful commits from all members, no secrets | 8 |
| A5 | **Reproducibility**: reported results reproduce with the provided scripts; results files match the paper; `phase2-final` release created | 7 |

### Deliverable B — Research paper (60 marks)

| Rubric | Requirement | Marks |
|---|---|---|
| B1 | Baseline and base-paper comparison | 8 |
| B2 | Gap-wise experiments plus the gap-resolution table | 12 |
| B3 | Ablation, efficiency and reliability | 7 |
| B4 | Failure analysis with categories, frequencies and cases | 8 |
| B5 | Paper structure: all 13 required sections | 12 |
| B6 | Figures and tables, numbered, captioned, referenced in text | 7 |
| B7 | Writing quality, IEEE format, 25–30 references with DOIs | 6 |

Format: **8–10 pages**, IEEE two-column (`IEEEtran`, `conference` option), title page with paper title, project code, both names, roll numbers and email addresses.

### Deliverable C — Integrity reports

Turnitin **similarity** report and Turnitin **AI-writing** report. The brief is unconditional: **no reports, no marking.** This is worth zero marks and blocks all 100.

### The writing rule

> The paper must be written by the group members in their own words. AI-generated writing is not allowed.

This is why the repository contains code, experiments, results, figures, tables and a section skeleton, and **no body prose**. Every `\todo{}` in `paper/main.tex` is a slot only you can fill. The AI-writing report makes this checkable, so there is no clever way around it.

---

## Part 2 — Status

### Done

| Item | Evidence |
|---|---|
| Agentic system, three switchable gap components | `coach/core.py`, `coach/timing.py`, `coach/grounding.py` |
| Usable interface: live CLI watching a real file on disk | `coach/cli.py` |
| Real environment interaction: file watching, subprocess execution | `coach/cli.py` |
| Read-only tool interface under a call budget | `coach/tools.py` |
| Fixed dev/test learner split, rule fixed in advance | `data/splits.json`, `scripts/make_splits.py` |
| **E1** uncapped rule baseline | `results/phase2/experiments_test.json` |
| **E2** base-paper on-demand comparator, 3 request models × 3 seeds | same file |
| **E3** full proposed system | same file |
| **E4 / G1** timing experiment | same file |
| **E4 / G3** transfer instrument, 3 conditions × 5 seeds + sensitivity | `results/phase2/e4_g3_transfer.json` |
| **E5** ablation, 6 variants | `results/phase2/experiments_test.json` |
| **E6** offline efficiency: runtime, throughput, memory | same file |
| Failure analysis: 6 categories, frequencies, 2 successes + 2 failures | `results/phase2/failure_analysis.json` |
| Agent traces for every reported run | `logs/*.jsonl` (12 files) |
| Development log, 6 iterations with before/after numbers | `docs/devlog.md` |
| README with architecture, install, reproduce, gap table, changes-since-Phase-1 | `README.md` |
| 57 tests passing | `tests/` (4 original + 2 new files) |
| `requirements.txt`, `.env.example`, `.gitignore` | repo root |
| 5 figures (PDF for LaTeX, PNG for README) | `figures/` |
| 5 LaTeX tables, generated from results | `paper/tables/` |
| IEEE skeleton, verified to compile | `paper/main.tex` |
| Human rating sheet + scorer | `scripts/make_rating_sheet.py`, `scripts/score_ratings.py` |

### Not done — and who owns each

| Item | Owner | Why it matters |
|---|---|---|
| **E4 / G2 grounding** | You — needs the Groq key on your laptop | The only empty column in the gap table. Costs B2. |
| **E6 live figures** (tokens, latency, cost, rejection rate) | Same run | Costs B3. |
| **Paper prose, all 13 sections** | Both of you | 60 marks |
| **14 more references with DOIs** | Areeba | B7. 11 verified are in `refs.bib`; 16 slots are listed with search phrases. |
| **Turnitin similarity + AI reports** | Minahil (group head submits) | **Blocks everything** |
| **30-item human rating** | Both, independently, ~30 min | Your only relevance figure for H2 |
| **Commits from both members** | Both | A4 explicitly requires it |
| **`phase2-final` tag/release** | Minahil | A4 |

### Deliberately not done, with reasons recorded

These are written up in the README's "Changes since Phase 1" table and in `docs/devlog.md`. **Do not quietly drop them from the paper** — the brief rewards honest reporting and penalises selective reporting.

| Phase 1 promise | What happened instead | Where it is recorded |
|---|---|---|
| VS Code extension as the end product | CLI session watching a real file. Event schema unchanged, so an editor front end is a drop-in. | README, devlog |
| Two educator raters, 0–4 timing scale | Log-derived timing measures + a 30-item rating by the two authors | devlog |
| Blind cross-condition human rating | Abandoned — the delivery offset that separates the conditions is also what a rater must see to judge timing, so the trial sheet separated gated from ungated 10/10 with no overlap | devlog, 2026-11-08 entry |
| Seven-day human transfer study | Instrument validation on simulated learners only | README, devlog |
| OpenAI provider | Groq adapter (your key is `gsk_`); the OpenAI path is kept in `coach/provider.py` | README |
| Held-out learners 24+ from Zenodo | Split within the existing 24 learners, by a rule fixed in advance | `data/splits.json`, devlog |

---

## Part 3 — Every result number

All figures below are from the files in `results/phase2/` and regenerate from the scripts. **Never retype a number into the paper** — the tables are `\input` from generated files. If a number looks wrong, fix the experiment and rerun `make_tables`.

### Dataset and split

| | Value |
|---|---|
| Source | Leinonen & Hellas, CS1 MOOC IDE action logs, Zenodo, CC BY 4.0, `doi:10.5281/zenodo.6903968` |
| Subset | 24 learners, 2,598,189 events |
| Split rule | learners sorted by integer id; every third learner (`index % 3 == 2`) → test |
| Dev | 16 learners, 1,871,292 events |
| **Test** | **8 learners** (ids 2, 5, 8, 11, 14, 17, 20, 23), **726,897 events** |
| Learner–question units in test | 966 |
| Observable decision points in test | 10,687 |
| Submissions in test | 1,205 |

The rule uses no outcome, so it cannot be tuned. No threshold was tuned on the test learners, but the timing gate and the evidence floor were added after looking at test-split results; the dev-split replication (`results/phase2/experiments_dev.json`, devlog 2026-11-11) checks that the pattern holds on learners not inspected during design.

### Main results (test split)

| Condition | Scaffolds | Interruption ↓ | Pause-aligned ↑ | Coverage ↑ | Deliberation Δ |
|---|---|---|---|---|---|
| E1 rule baseline (uncapped) | 10,687 | 0.2736 | 0.2300 | 0.7935 | −0.0138 [−0.0191, −0.0057] |
| E2 on-demand, **pause** (strongest) | 461.0 ± 11.4 | 0.1273 ± 0.0137 | 0.3554 | 0.0194 | −0.0068 |
| E2 on-demand, stuck | 488.3 ± 12.5 | 0.8365 ± 0.0260 | 0.0696 | 0.0195 | −0.0070 |
| E2 on-demand, uniform | 483.7 ± 11.2 | 0.8288 ± 0.0303 | 0.0725 | 0.0190 | −0.0104 |
| **E3 proposed system (full)** | **2,038** | **0.0206** | **0.4485** | **0.1368** | **+0.0079 [−0.0016, +0.0172]** |

On-demand rows are mean ± SD over seeds 0, 1, 2. The other rows are deterministic (single run).

**Headline comparisons for the paper:**
- vs the strongest comparator: interruption **6.2× lower** (0.0206 vs 0.1273), pause alignment **1.26× higher**, coverage **7.1× higher** (0.1368 vs 0.0194), with **4.4× more** scaffolds delivered.
- vs the uncapped rule baseline: interruption **13.3× lower**, pause alignment **1.95× higher**, but coverage **5.8× lower**. This trade-off is the main limitation and belongs in the Results section, not buried.

### Ablation (test split)

| Configuration | Scaffolds | Interruption | Pause-aligned | Coverage |
|---|---|---|---|---|
| Full system | 2,038 | 0.0206 | 0.4485 | 0.1368 |
| − cooldown | 2,129 | 0.0202 | 0.4486 | 0.1438 |
| − episode budget | 2,955 | 0.0210 | 0.4443 | 0.2061 |
| − response wait | 2,955 | 0.0210 | 0.4443 | 0.2061 |
| − evidence floor (G2) | 2,804 | 0.0264 | 0.4237 | 0.1463 |
| − timing gate (G1) | 2,364 | 0.2690 | 0.3105 | 0.2208 |
| Phase 1 policy, no components | 3,828 | 0.6567 | 0.1677 | 0.3412 |

**Three findings worth writing about:**

1. **The timing gate carries almost everything.** Remove it and interruption goes 0.0206 → 0.2690, a **13-fold rise**. Remove both components and it reaches 0.6567, a **32-fold rise** over the full system.
2. **Two components are redundant.** `− episode budget` and `− response wait` are byte-identical (2,955 / 0.0210 / 0.4443 / 0.2061). The response wait **never binds** once the cooldown and gate are active. A redundant component found by ablation is a real result — say so.
3. **The cooldown barely matters either**: removing it changes interruption by 0.0004. The gate has made most of the Phase 1 throttling machinery idle.

### Gate statistics (full system)

| | Count | Share of held |
|---|---|---|
| Held for a pause | 3,269 | — |
| Released | 2,038 | 62.3% |
| Superseded by a newer juncture | 1,060 | 32.4% |
| Dropped, no pause inside the horizon | 171 | 5.2% |

### E6 offline efficiency

| Condition | Runtime | Events/sec | Peak memory | Scaffolds per 1000 events |
|---|---|---|---|---|
| E1 rule baseline | 32.08 s | 22,662 | 7.7 MB | 14.70 |
| E3 proposed system | 31.53 s | 23,052 | 1.5 MB | 2.80 |

One CPU core, no network, Python 3 standard library only. The proposed system uses **5× less memory** because the gate keeps at most one pending scaffold per learner instead of a growing decision list.

### E4 / G3 — transfer instrument (simulated learners)

120 learners per run, 5 seeds, pooled bootstrap over 480 learners for the CI.

| Condition | Transfer ~ latent skill | Pooled 95% CI | Assisted completion ~ latent skill | Target ≥ 0.70 |
|---|---|---|---|---|
| unassisted | 0.7988 ± 0.0250 | [0.7887, 0.8465] | 0.6898 | met |
| on_demand | 0.7951 ± 0.0365 | [0.7619, 0.8249] | 0.7178 | met |
| **trajectory** | **0.7926 ± 0.0357** | **[0.7611, 0.8251]** | **0.7238** | **met** |

**Sensitivity — how many transfer tasks the rubric needs:**

| Tasks | Spearman r | SD |
|---|---|---|
| 2 | 0.6388 | 0.0210 |
| 4 | 0.7899 | 0.0358 |
| 6 | 0.8489 | 0.0269 |
| 8 | 0.8723 | 0.0118 |

**Practical finding: two tasks are not enough (0.639, below the 0.70 target). Four is the minimum.**

Honest reading: the transfer score tracks latent skill better than assisted completion does in every condition, but the separation is **modest** (0.79 vs 0.72). Assisted completion is not a useless proxy — just a worse one. Say that; do not inflate it.

### Failure analysis (full system, 2,038 delivered scaffolds)

| Category | Cases | Share |
|---|---|---|
| Superseded while held | 1,060 | 0.5201 |
| Suppressed submission (no evaluate scaffold at a submit) | 466 | 0.2287 |
| Held then dropped (no pause arrived) | 171 | 0.0839 |
| Late delivery (> 120 s after the triggering juncture) | 92 | 0.0451 |
| Abandoned after (no learner event within 30 min) | 59 | 0.0289 |
| Interrupted a burst | 42 | 0.0206 |

**Overall: 9.32% of delivered scaffolds carry at least one failure flag** (categories are not exclusive, and the first three count events that were never delivered).

The costliest silence is **suppressed submissions**: 466 of 1,205 submissions in the test split (38.7%) produced no evaluate scaffold because the budget, cooldown or evidence floor was active. A submission is the clearest moment to ask for a self-check, so this is the strongest candidate for future work — give submissions a reserved budget slot.

### The improvement history (this is your A3 evidence, 5 marks)

| Iteration | Observed failure | Change | Measured effect |
|---|---|---|---|
| 1 | No held-out data; thresholds tuned on the reported learners | Fixed split by a rule fixed in advance | Phase 1 and Phase 2 numbers are no longer comparable; results now from unseen learners |
| 2 | Phase 1 policy interrupted **more** per scaffold (0.6567) than its own uncapped baseline (0.2736) | **Timing gate** | 0.6567 → 0.0206, a 32× reduction; coverage 0.3412 → 0.1368 |
| 3 | Behavioural measure unstable; on-demand CI came out as −13.45 ± 10.36 | Replaced edits-per-run with the bounded deliberation ratio | Usable intervals; full system +0.0079 [−0.0016, +0.0172] |
| 4 | Comparator too weak — uniform and stuck models interrupted 0.83, so winning meant nothing | Added the **pause** request model | Comparator 0.8365 → 0.1273; **our own advantage fell from ~32× to ~6×** |
| 5 | 37.2% of scaffolds came from windows holding fewer than 5 events | **Evidence floor** | Failure rate 0.434 → 0.0932; thin-evidence category eliminated |
| 6 | Blind cross-condition rating sheet was not blind | Replaced with a single-condition rating, reason recorded | Cross-condition claims now rest only on the log-derived measures |

Iteration 4 is the one to be proud of: you made your own result **look worse** because the original comparison was unfair. Mention it explicitly in the paper — it is the strongest signal of honest method you have.

---

## Part 4 — Remaining steps, in order

### Step 1 — Groq smoke test (2 minutes) ⚠ do this first

PowerShell, in the `project` folder:

```powershell
cd "D:\Kaam Shaam\Semester 7\Agentic AI\Project\Phase1\TrajectoryCoach_Final\TrajectoryCoach_Final\project"
$env:GROQ_API_KEY="gsk_...your key..."
python -m scripts.run_llm_experiments --smoke
```

If the model name is rejected, list what your key can use:

```powershell
curl.exe https://api.groq.com/openai/v1/models -H "Authorization: Bearer $env:GROQ_API_KEY"
```

then pass a real one, e.g. `--model openai/gpt-oss-20b`.

The provider now **falls back automatically** if a model rejects tool-calling combined with JSON mode, so that will not kill the run; it records `tool_calling_supported: false` instead.

### Step 2 — The G2 / E6 live run (15–25 minutes)

```powershell
python -m scripts.run_llm_experiments --prefixes 100 --sleep 1.5
python -m scripts.make_tables
```

Writes `results/phase2/e4_g2_grounding.json` and refreshes `paper/tables/gaps.tex` and `efficiency.tex`.

This produces, on 100 held-out prefixes, with the same model and context in both conditions:
- **constrained** unsupported-claim rate (schema + validator + tools + evidence floor)
- **unconstrained** unsupported-claim rate (free text, no schema, no validator)
- API calls, prompt/completion tokens, mean and p95 latency, tool calls, validator rejection rate

H2's target was **≤ 5% unsupported claims**. The table reports whether it was met; do not round it in your favour.

Add `--price-in` and `--price-out` (USD per million tokens, from Groq's pricing page) if you want a cost estimate in the table.

### Step 3 — The human rating (30 minutes, both of you)

```powershell
python -m scripts.make_rating_sheet
```

Then **each** of you copies `results/phase2/rating_sheet.csv` to your own name and fills in only the `timing` (0–4) and `relevance` (1–4) columns. **Do not discuss any row until both sheets are finished** or the agreement figure is meaningless.

```powershell
python -m scripts.score_ratings results/phase2/ratings_minahil.csv results/phase2/ratings_areeba.csv
```

Gives mean timing, mean relevance, SDs, and a linearly weighted kappa between the two of you. The relevance mean is what H2 needs.

### Step 4 — Re-verify everything before writing it up

```powershell
python -m unittest discover -s tests -v
python scripts/make_splits.py
python -m scripts.run_experiments --split test
python -m scripts.run_transfer_study
python -m scripts.run_failure_analysis
python -m scripts.make_figures
python -m scripts.make_tables
```

Expect 57 tests and identical numbers to Part 3. If anything differs, stop and tell me — it means something is not deterministic and the paper would be unreproducible.

### Step 5 — Write the paper

Part 5 below, section by section.

### Step 6 — References

11 verified entries are in `paper/refs.bib`. You need 25–30. Sixteen numbered slots are listed in that file with search phrases, covering interruption timing, metacognition theory, scaffolding, help-seeking, productive failure, novice debugging, educational data mining, hallucination, constrained decoding, tool use, agent architectures, LLM-as-judge, aspect-oriented programming and learning-analytics ethics.

**Look up each DOI yourself.** Publisher page → copy the real DOI, or Google Scholar → Cite → BibTeX. I did not guess a single one, because a wrong DOI is worse than a missing reference and a marker can check it in one click.

Every reference must be cited in the text. An uncited entry in the bibliography is padding and reads as such.

### Step 7 — Git, release, submit

Part 6 below.

---

## Part 5 — The paper, section by section

`paper/main.tex` has all 13 sections with `\todo{}` markers. Upload `paper/` **and** `figures/` to Overleaf, compiler **pdfLaTeX**. It compiles today at 7 pages with empty bodies, so it lands in the 8–10 page window once written.

| § | Section | What goes in | Numbers to use |
|---|---|---|---|
| 1 | Abstract | 150–250 words, **write last**. Problem, what you built, main numbers, contribution. No learning claims. | 0.0206 vs 0.1273 vs 0.6567; coverage cost; null behavioural result; 0.79 |
| 2 | Introduction | Cognitive offloading; why plan/monitor/evaluate matter; three gaps as questions; bulleted contributions | cite base paper + ≥4 others |
| 3 | Related Work | Your Phase 1 review rewritten **by theme, not paper by paper**. Five themes, each ending in what is missing. | 11 verified refs |
| 4 | Problem Formulation | Event stream definition; the four event types; **what is not observable** (correctness, tests, code, affect); RQ1–3 and H1–3; where a measure changed and why | — |
| 5 | Proposed System | Walk through Fig. 1. Subsections: state, policy, agent + tools, provider contract, then one per gap component | gate stats: 3,269 held / 2,038 released / 1,060 superseded / 171 dropped |
| 6 | Experimental Setup | Dataset, split rule, model string, temperature 0, seeds, 3 runs for stochastic. **State plainly that E2 is your adaptation, not reproduced numbers.** | 726,897 / 966 / 10,687; dev 1,871,292 |
| 7 | Evaluation Methodology | One sentence + formula per measure; cluster bootstrap over learners; juncture precision is circular by construction; **the replay caveat** | — |
| 8 | Results | Table I, Fig. 2, then one subsection per gap | the whole of Part 3 |
| 9 | Ablation & Comparative | Table II, Fig. 3. The gate carries everything; the response wait never binds | 0.0206 → 0.2690 → 0.6567; identical 2,955 rows |
| 10 | Failure Analysis | Table IV, Fig. 5, every category explained with cause and fix, then 2 successes + 2 failures **with real traces quoted** | 9.32%; 466/1,205 submissions |
| 11 | Limitations | Part 8 below, in full | — |
| 12 | Conclusion | 3–4 sentences + future work | — |
| 13 | References | 25–30, all with DOIs, all cited | — |

### Figures and tables (B6, 7 marks)

| Asset | File | Must be referenced in |
|---|---|---|
| Fig. 1 architecture | `fig1_architecture.pdf` | § 5 |
| Fig. 2 interruption vs coverage | `fig2_tradeoff.pdf` | § 8 |
| Fig. 3 ablation | `fig3_ablation.pdf` | § 9 |
| Fig. 4 transfer sensitivity | `fig4_transfer.pdf` | § 8 (G3) |
| Fig. 5 failure categories | `fig5_failures.pdf` | § 10 |
| Table I main | `tables/main.tex` | § 8 |
| Table II ablation | `tables/ablation.tex` | § 9 |
| Table III efficiency | `tables/efficiency.tex` | § 9 |
| Table IV failures | `tables/failures.tex` | § 10 |
| Table V gap resolution | `tables/gaps.tex` | § 8 |

Every one must be **numbered, captioned and referred to by number in the body text**. A figure nobody points at loses marks.

### Writing notes

- Read the tables **for** the reader; do not restate every cell in prose.
- Use "associated with", not "caused by". Nothing here is causal.
- Where a result is null or goes against you, say so in the main text, not only in Limitations.
- Keep one voice. If you and Areeba write different sections, one of you does a full read-through at the end to even out the register.

---

## Part 6 — Git, release and submission

### Both members need meaningful commits (A4 requires it explicitly)

**Minahil:**
```powershell
git add coach/ scripts/ data/splits.json docs/ experiments/ README.md requirements.txt .env.example .gitignore
git commit -m "Phase 2: timing gate, evidence floor, experiment harness, dev log"
git push
```

**Areeba, on her own machine under her own GitHub account:**
```powershell
git add tests/ results/ logs/ figures/ paper/
git commit -m "Phase 2: tests, results, figures, paper source"
git push
```

Do not commit both halves from one account and rename later — the commit author is what a marker sees, and `git log` shows the history.

### Check nothing secret went in

```powershell
git log --oneline
git ls-files | Select-String -Pattern "\.env$"
```

The second must return nothing. `.env` is in `.gitignore`, but check — a leaked key in a public repo is a worse problem than a missed mark.

### Release

```powershell
git tag -a phase2-final -m "Phase 2 final submission, project G3-11"
git push --tags
```

Then on GitHub: Releases → Draft a new release → choose the `phase2-final` tag → publish.

### Clean-clone test (do not skip)

```powershell
cd $env:TEMP
git clone https://github.com/Areeba444/TrajectoryCoach fresh
cd fresh
python -m unittest discover -s tests
python -m scripts.run_experiments --split test
```

If a fresh clone cannot reproduce the numbers, A2 fails. The large data file is committed, so this should work — but verify, because `.gitignore` now excludes `results/*/decisions.jsonl`.

### Submission

- Google Classroom, **group head only** (Minahil).
- The paper PDF, the repo URL **without** `.git`, and both Turnitin reports.
- Check the filename convention in the Phase 2 brief — it may differ from Phase 1's `Phase1_G3-11_23i-0554.pdf`. I have not re-read that line; confirm it yourself.

---

## Part 7 — Turnitin

This blocks all 100 marks, so treat it as step zero of whatever time you have left.

1. Find the route: class Turnitin link, LMS assignment, or supervisor submission.
2. Find the turnaround. AI-writing reports can queue, and a resubmission often has a delay before a second report is generated.
3. Submit the paper early enough to see the report **and** fix anything it flags.
4. Keep both PDFs. Submit them alongside the paper.

If similarity flags your own Phase 1 text, that is self-plagiarism of a submitted work — rewrite those passages rather than arguing about it. Related Work is the likeliest place.

---

## Part 8 — Honesty rules

These are the things most likely to cost marks, and a marker will look for them.

### Must appear in the paper

1. **No learner ever saw a scaffold.** This is a replay of logs recorded before this system existed, plus simulated learners. No number in the paper is an effect of prompting, and none is a learning outcome. The deliberation delta describes **which moments a policy selects** and what the learner did there anyway. State this in § 7, not just § 11.
2. **E2 is your reconstruction.** The base paper reports neither of your measures. The on-demand columns are its *interaction policy* re-implemented on *your* data at its reported request rate (725 hints / 102 students / 14 questions = 0.5077 per student-question). Never present them as numbers from the published paper.
3. **Juncture precision is circular.** The proposed policy fires at junctures by construction. Report the column; rest no claim on it.
4. **The grounding checker is a pattern screen, not a verifier.** A fluent, plausible, wrong statement that avoids the pattern list passes.
5. **The transfer study is simulated**, and you chose its parameters. It validates the rubric as an instrument. It says nothing about whether coaching helps people.
6. **You rated your own system.** Name that conflict of interest. The rating is not blind between conditions, and the reason is in the devlog.
7. **Eight test learners is small**, and one of them contributes only 2,657 events.
8. **The coverage trade-off**: 5.8× less coverage than the rule baseline. Put it in Results.
9. **Two Phase 1 promises were not kept** (educator raters, VS Code extension) and are listed with reasons.

### Must not happen

- No number typed into the `.tex` by hand. Tables are generated.
- No rounding in your favour, especially on H2's 5% target.
- No "improved learning", "helped students", "caused" — you have no evidence for any of them.
- No DOI copied from this document or any chat. Look each one up.
- No condition omitted because it looked bad. The weak comparators stay in, labelled weak.

---

## Part 9 — Viva preparation

You will be asked to explain this code. Read `docs/devlog.md` first — it is written as the story of why each component exists, which is the fastest route in. Then be ready on these five:

| Likely question | Where the answer lives |
|---|---|
| Why does the timing gate help, and how would it work live? | `coach/core.py`, the `gate_seconds` block. It is an inactivity timer, not knowledge of the future — implementable in a real IDE. |
| Why bootstrap over learners rather than over scaffolds? | `coach/timing.py`, `_cluster_bootstrap`. Scaffolds cluster within learners, so resampling scaffolds understates the interval. |
| Why is the deliberation delta not a treatment effect? | Nobody saw a prompt. It describes the selected moments. |
| How does the evidence floor relate to grounding? | Grounding is refusing to speak without evidence as much as checking what is said. `min_evidence` in `coach/core.py`, `coach/grounding.py`. |
| Why did two ablations give identical numbers? | The response wait never binds once the cooldown and gate are active. Real finding from `experiments_test.json`. |

Each of you should be able to answer all five. The brief says all members are responsible for understanding the complete project, and a split answer is worse than a slow one.

---

## Part 10 — File map

```
project/
├── coach/
│   ├── core.py            engine, policies, timing gate, evidence floor
│   ├── dataset.py         log loading, fixed split
│   ├── baselines.py       on-demand base-paper comparator (3 request models)
│   ├── timing.py          G1 measures, cluster bootstrap, junctures
│   ├── grounding.py       G2 unsupported-claim checker
│   ├── simulator.py       G3 simulated learners
│   ├── stats.py           Spearman, ranks, bootstrap (stdlib only)
│   ├── tools.py           read-only agent tools + call budget
│   ├── provider.py        OpenAI adapter (Phase 1, kept)
│   ├── groq_provider.py   Groq adapter, tool loop, instrumentation
│   └── cli.py             live session interface
├── scripts/
│   ├── make_splits.py          → data/splits.json
│   ├── run_experiments.py      → E1, E2, E3, E5, E6 offline
│   ├── run_llm_experiments.py  → E4/G2 and live E6   ⚠ needs your key
│   ├── run_transfer_study.py   → E4/G3
│   ├── run_failure_analysis.py → failure categories and cases
│   ├── make_rating_sheet.py    → human rating sheet
│   ├── score_ratings.py        → agreement and means
│   ├── make_figures.py         → figures/
│   └── make_tables.py          → paper/tables/ + docs/gap_resolution.md
├── data/        Zenodo subset, manifest, splits.json
├── docs/        evidence register, lab tasks, research gaps, devlog, this plan
├── experiments/ config.json — every setting, so a number traces to a config
├── results/phase2/  all reported results
├── logs/        agent traces (12 files) and failure cases
├── tests/       57 tests
├── paper/       main.tex, refs.bib, tables/
└── figures/     5 figures, PDF + PNG
```

---

## One-page checklist

- [ ] Turnitin route and turnaround confirmed
- [ ] `--smoke` passes
- [ ] `--prefixes 100` run complete, `make_tables` rerun
- [ ] Both rating sheets filled independently, `score_ratings` run
- [ ] All 13 sections written, every `\todo{}` gone
- [ ] 8–10 pages, IEEEtran two-column, title page complete
- [ ] 25–30 references, every DOI verified, every entry cited
- [ ] All 5 figures and 5 tables referenced by number in the text
- [ ] All nine honesty points in Part 8 present in the paper
- [ ] Commits from **both** accounts
- [ ] `git ls-files` shows no `.env`
- [ ] `phase2-final` tag pushed and release published
- [ ] Clean clone reproduces the numbers
- [ ] Turnitin similarity + AI reports in hand
- [ ] Submitted by the group head with the repo URL (no `.git`)
