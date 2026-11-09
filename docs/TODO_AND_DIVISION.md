# Phase 2 — Remaining Work and Division

**Status: 9 November 2026.** Supervisor extension granted — confirm the new date and work back from it.
Repository: `https://github.com/Areeba444/TrajectoryCoach` · currently at `9d9bad5`, tag `phase2-final`.

**Decision taken:** go forward with the verified measurement layer, keeping the existing git history and both members' commits. The committed metrics were degenerate (interruption 0.0 in all 13 conditions, `pause_aligned == coverage` everywhere, seeds with no effect, unbounded deliberation). This is recorded as the 2026-11-09 entry in `docs/devlog.md`, which is itself evidence for rubric A3.

---

## Step 0 — Minahil, do this first (5 minutes)

Your local repo is at commit `45e2d89` from 17 October, three commits behind GitHub, with uncommitted files in the working tree. Do not try to merge it. Take a fresh clone:

```powershell
cd "D:\Kaam Shaam\Semester 7\Agentic AI\Project\Phase2"
git clone https://github.com/Areeba444/TrajectoryCoach.git
cd TrajectoryCoach
git log --oneline -3
```

You should see `9d9bad5` at the top. Tell me when that's done and I'll write the corrected files into it. Leave the old `Phase1\...\project` folder alone — don't delete it until everything is pushed, it's your backup.

---

## The work, split

### Minahil (group head) — owns the paper argument and the submission

| # | Task | Done when |
|---|---|---|
| M1 | Fresh clone (Step 0) | `git log` shows `9d9bad5` |
| M2 | **Confirm the new deadline** with Naeem Tareen and tell Areeba and me | Date written at the top of this file |
| M3 | **Turnitin route and turnaround** confirmed | You know how to get both reports and how long they take |
| M4 | Commit and push the corrected files from your account | `git log` shows your commit on top |
| M5 | Write §2 Introduction | No `\todo` left in that section |
| M6 | Write §4 Problem Formulation | ditto |
| M7 | Write §8 Results | ditto |
| M8 | Write §11 Limitations and Threats to Validity | all nine honesty points present |
| M9 | Write §12 Conclusion | ditto |
| M10 | Write §1 Abstract — **last**, after everything else | 150–250 words |
| M11 | Compile the final PDF, check 8–10 pages | PDF in hand |
| M12 | Run Turnitin on the final PDF, both reports | Two PDFs saved |
| M13 | Submit: paper PDF, similarity PDF, AI report PDF, LaTeX ZIP, repo link, release link | Google Classroom confirmation |

### Areeba — owns the evidence and the methods sections

| # | Task | Done when |
|---|---|---|
| A1 | **Groq run** — the only missing experiment. `--smoke` first, then `--prefixes 100` | `results/phase2/e4_g2_grounding.json` exists |
| A2 | Rerun `make_tables` after A1 | G2 row in the gap table is filled, not "not run" |
| A3 | **References**: fill the 16 slots in `paper/refs.bib`, verified DOIs only | 25–30 entries, every one cited in the text |
| A4 | Fix the base paper title in `refs.bib` — it is *"Applying Metacognitive Theory to AI-Assisted Programming Education"*, not *"Metacognitive Scaffolding for Novice Programmers"* | Title matches the DOI record |
| A5 | Write §3 Related Work | No `\todo` left |
| A6 | Write §5 Proposed System / Methodology | ditto |
| A7 | Write §6 Experimental Setup | ditto |
| A8 | Write §7 Evaluation Methodology | ditto |
| A9 | Write §9 Ablation and Comparative Analysis | ditto |
| A10 | Write §10 Failure Analysis, with 2 success + 2 failure traces quoted | ditto |
| A11 | Commit and push from **your own account** | Both names in `git log` for Phase 2 |

### Me

| # | Task | Status |
|---|---|---|
| C1 | Audit the committed repo against the brief | done — see devlog 2026-11-09 |
| C2 | Port your 30-item rating study, verify the kappas | done — reproduces 0.3284 / 0.3426 exactly |
| C3 | Write the corrected files into Minahil's fresh clone | waiting on M1 |
| C4 | Regenerate all results, tables and real PDF figures | ready to run |
| C5 | Check every number in your drafts against the results files | as you write |
| C6 | Review drafts for unsupported claims and missing citations | as you write |
| C7 | Help verify reference DOIs if Areeba wants | on request |

**I am not writing the paper prose.** The brief forbids it and you submit a Turnitin AI report on the same file. Everything in the `\todo{}` markers is yours.

---

## Both of you, before anything else

Read `docs/devlog.md`. It is the story of what broke and what was changed, and it is what a supervisor will use to check A3. It is also the fastest way to be able to answer viva questions about code you did not type.

---

## Order of work

1. **M1** fresh clone → I write corrected files (**C3**, **C4**) → **M4** commit
2. **A1** Groq run → **A2** tables. Until this is done the G2 column reads "not run".
3. Both write sections in parallel. Related Work (A5) and Introduction (M5) need no results and can start immediately.
4. **A3** references in parallel with writing.
5. **M11** compile → **M12** Turnitin → **M13** submit.
6. Re-tag the release **after** the final commit:
   ```powershell
   git tag -d phase2-final
   git push origin :refs/tags/phase2-final
   git tag -a phase2-final -m "Phase 2 final, G3-11"
   git push --tags
   ```
   Then publish the release on GitHub.

---

## Numbers that have changed since the handover

Do not use the figures from the earlier handover document. These are the verified ones.

| | Handover | Verified |
|---|---|---|
| E1 interruption | 0.0000 | **0.2736** |
| E3 scaffolds | 1,328 | **2,038** |
| E3 interruption | 0.0000 | **0.0206** |
| E3 pause-aligned | 1.0000 | **0.4485** |
| E3 coverage | 1.0 | **0.1368** |
| E3 deliberation | 89.22 s | **+0.0079, CI [−0.0016, +0.0172]** |
| E2 pause comparator | 821, SD 0 | **461.0 ± 11.4**, interruption 0.1273 ± 0.0137 |
| − timing gate | pause 0.5427 | interruption **0.2690**, pause 0.3105 |
| Phase 1 policy | pause 0.4572 | interruption **0.6567**, pause 0.1677 |
| G3 transfer ρ | 0.9743 all conditions | **0.7926–0.7988**, assisted 0.69–0.72 |
| Tests | 49 | **57** |

Unchanged and still correct: 726,897 test events, 8 test learners, 10,687 decision points, 10,687 E1 scaffolds, 2,364 for the no-gate ablation, 3,828 for the Phase 1 policy, and the whole rating study.

## Three claims to drop

- "0% interruptions" — the metric was zero by construction.
- "8.0× reduction in interruption risk" — that is a scaffold-count ratio, not an interruption measure.
- "rho = 0.97 transfer correlation" — at that value the conditions no longer differ and the instrument validation says nothing.

## One claim to add

The timing gate is the component that does the work: removing it takes interruption from 0.0206 to 0.2690, and removing both gap components takes it to 0.6567. Removing the episode budget and removing the response wait give **identical** results, so one Phase 1 component never binds. A redundant component found by ablation is a real finding and B3 rewards it.
