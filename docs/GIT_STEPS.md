# Git steps — run these in the repository root

Everything in the repository is already correct. These three blocks are the only
commands left. Run them in order.

## 1. Minahil — commit the corrected system

```powershell
cd "D:\Kaam Shaam\Semester 7\Agentic AI\Project\Phase2\TrajectoryCoach"
git status
```

You should see modified files under `coach/`, `scripts/`, `tests/`, `docs/`,
`figures/`, `paper/` and `results/phase2/`. Then:

```powershell
git add -A
git commit -m "Phase 2: restore working measurement layer, regenerate all results

The committed metrics were degenerate: interruption_rate was 0.0 in all 13
conditions, pause_aligned_rate and coverage were the same quantity, coverage
used a different denominator per condition, and seeds had no effect on two of
the three on-demand comparators.

Restores the burst-based interruption test, separate pause-alignment and
coverage with a common denominator, the bounded deliberation ratio, and the
cluster bootstrap over learners. All measures now discriminate between
conditions. Regenerates results, tables and figures, replaces the ASCII
figures with vector PDFs, and records the change in docs/devlog.md.

The 30-item inter-rater study is preserved unchanged and its kappa values
reproduce exactly."
git push
```

## 2. Areeba — the Groq run, then commit from her own account

On her machine, after `git pull`:

```powershell
$env:GROQ_API_KEY="gsk_...."
python -m scripts.run_llm_experiments --smoke
python -m scripts.run_llm_experiments --prefixes 100 --sleep 1.5
python -m scripts.make_tables
git add results/phase2/e4_g2_grounding.json logs/ paper/tables/
git commit -m "Phase 2: G2 grounding experiment and live-model efficiency on 100 held-out prefixes"
git push
```

## 3. Re-tag after the final commit

Only once the paper is finished and everything is pushed:

```powershell
git tag -d phase2-final
git push origin :refs/tags/phase2-final
git tag -a phase2-final -m "Phase 2 final submission, project G3-11"
git push --tags
```

Then on GitHub: Releases to Draft a new release to pick `phase2-final` to Publish.

## 4. Check before submitting

```powershell
git ls-files | Select-String -Pattern "\.env$"     # must print nothing
git shortlog -sne                                   # both members must appear
python -m unittest discover -s tests                # 57 tests
```
