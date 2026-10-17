# TrajectoryCoach: Evidence-Grounded Metacognitive Scaffolding for Collaborative Programming

**AI4015 Agentic Artificial Intelligence, Fall 2026, Phase 1.** Project seed G3-11 (project code G3-11).

| | |
|---|---|
| Group members | Minahil Kashif (23i-0554, group head), Areeba Javed (23i-0570) |
| Supervisor | Naeem Tareen |
| Base paper | Phung et al., *Plan More, Debug Less*, AIED 2025 |

This is the **Phase 1 project implementation**. It contains a working, inspectable trajectory baseline and an evaluation design.
It is not a completed educational experiment or a reproduction of the base paper's results.

## Start here

Requires Python 3.10 or newer. No third-party packages are required for the application.
Open a terminal in this folder:

```powershell
python demo.py
python -m unittest discover -s tests -v
python -m coach --input data/demo.csv --mode adaptive --out results/local/demo
```

For a step-by-step presentation with learner reflection input:

```powershell
python demo.py --interactive
```

Replay the included authentic-data subset and regenerate all four comparisons:

```powershell
python scripts/benchmark.py
```

This processes approximately 2.6 million records four times and can take several minutes.
The included `results/benchmark.json` contains measured results from the recorded run.
The large per-decision audit files (`results/<mode>/decisions.jsonl`, about 38 MB in total) are not
stored in the repository; running `python scripts/benchmark.py` regenerates them, and the
`summary.json` file for each mode is included.
Each mode writes a summary and a JSONL audit trail of delivered prompts.
Only non-wait decisions are written; every event still contributes to summary counts.

## What is implemented

- Strict CSV event contract; unknown event types and backwards timestamps fail visibly.
- A causal five-minute trajectory window, separated by learner and task.
- A transparent rule baseline and a policy with response wait, cooldown, and prompt limits.
- Learner reflection state, bounded recent-decision memory, and explicit abstention.
- Optional OpenAI Responses integration with JSON schema and conservative validation.
- Provider-error fallback to a deterministic scaffold; a ten-call default API budget.
- An external Python runtime-weaving demonstration that preserves source and exceptions.
- Read-only agent tool interface (`coach/tools.py`): trajectory summary, prior interventions, learner reflection and evidence-row check, with argument validation and a call budget. The agent loop that uses these tools is Phase 2 work.
- Real log replay, ablations, provenance, engineering tests, and project documentation.

The offline policies are deterministic. They do not demonstrate LLM reasoning or prove
the need for an agent. The optional provider adds a bounded decision to rephrase or
withhold a permitted scaffold. Richer tool selection and classroom adaptation remain
part of the proposed semester system. No artificial collection of separate LLM personas
is presented as a research contribution.

## Data and reproducibility

Source: Juho Leinonen and Arto Hellas, *IDE Action Log Dataset from a CS1 MOOC*,
2022, https://doi.org/10.5281/zenodo.6903968, CC BY 4.0.

`data/zenodo_24_students.csv.gz` contains all records for original student identifiers
0 through 23 encountered before identifier 24 in the downloaded source prefix.
This convenience subset is for engineering validation, **not population estimation**.
`data/manifest.json` records counts, source attribution, hashes and transformations.
The complete original 1.36 GB file was not downloaded or checksum-verified.
The complete README and outcome-label file were downloaded and checksum-verified;
the latter is excluded from policy inputs to avoid hindsight leakage.

The raw prefix contained 133 adjacent timestamp inversions. Extraction applies a stable
timestamp sort within learner and retains `sourceRow`. Equal-time events keep original
order. Duplicate-looking keystrokes are retained; they may be legitimate events.

To regenerate from an independently downloaded original file:

```powershell
python scripts/extract_subset.py PATH_TO_IDE_logs.csv --out data
python scripts/benchmark.py
```

Gzip container bytes can vary because the compressor records a creation time. Compare
the **decompressed content SHA-256** for semantic reproducibility. The bundled archive's
compressed hash is recorded for transfer-integrity checking.

## Policies and ablations

`rule`: first observed edit -> plan; third and subsequent runs within five minutes
with edits present -> monitor; submission -> evaluate. No rate limits.

`adaptive`: same triggers, plus a three-prompt limit per contiguous task episode/session,
120-second response wait, and 180-second cooldown. A learner reflection clears the
response wait, but never bypasses cooldown. A gap greater than 30 minutes starts a
new session. Switching exercises starts a new task episode and resets its budget.
Returning to a prior exercise also creates a new episode; this is a documented limitation.

`no_memory`: removes intervention budget and response-wait state, while retaining
the trajectory window and cooldown. It does **not** remove observational history.

`no_cooldown`: removes cooldown but retains response waiting and prompt budget.

Thresholds are engineering defaults. They have not been calibrated as cognitive diagnoses.
All feedback acknowledges observations rather than claiming a bug, failed test, or mastery.
Active time is only an estimate: inter-event gaps are capped at 60 seconds, intervals
after focus loss are excluded, and gaps over 30 minutes start a new session.

## Optional live model

Set environment variables locally; do not commit secrets:

```powershell
$env:OPENAI_API_KEY = 'YOUR_LOCAL_KEY'
$env:OPENAI_MODEL = 'YOUR_SUPPORTED_STRUCTURED_OUTPUT_MODEL'
python -m coach --input data/demo.csv --live --out results/local/live
```

The recorded run made **zero live API calls**. Account access, model availability,
latency, cost and semantic output quality have not been verified. The configured model
must support the Responses API and strict JSON-schema output. The adapter sends only
the event summary, recent decisions, and the learner's reflection. It sets `store=false`;
that flag is not a claim about all provider retention rules. Keep real student text out
of the API until the educational deployment has appropriate consent and data handling.

Response validation checks structure, source-row reference, permitted phase, lengths,
and a limited phrase screen. It is **not a complete factuality or code-leakage detector**.

Official interface reference:
https://developers.openai.com/api/docs/guides/structured-outputs?api-mode=responses

## Non-invasive monitoring demonstration

```powershell
python examples/weave_demo.py
```

The harness temporarily wraps a function in `student_program.py`, records duration and
exception type, and restores the original function. It does not change the student's
file or swallow their exception. This illustrates the separation of concerns in AOP.
It is **not a Spring AOP/AspectJ implementation or an IDE extension**. Those are deferred
in the explicitly narrowed Phase 1 scope. Runtime probe events are not merged into the
historical Zenodo data or misrepresented as fields present in that dataset.

## Research boundary

Base paper: Phung et al., *Plan More, Debug Less*, AIED 2025,
https://doi.org/10.1007/978-3-031-98414-3_1.

The included replay does not reproduce AIMS. The metadata lacks code, correctness,
and help-request events. A fair AIMS-inspired comparison requires the new task environment
specified in the report. Prompt-count reductions are an engineered operational effect,
not proof of learning improvement. No participants were recruited for this project.

## Repository use

Phase 1 repository for group G3-11. Both group members commit to this repository.
Consent, ethics clearance, human ratings and educational results are not part of Phase 1:
no participants were recruited and no learning outcomes have been measured.

## Contents

- `coach/`: event engine, policies, provider adapter, agent tools, CLI
- `data/`: synthetic demo; attributed authentic-data subset and manifest
- `results/`: measured replay outputs, ablations, test and demo transcripts
- `tests/`: deterministic correctness and boundary tests
- `examples/`: source-separated runtime monitoring illustration
- `scripts/`: extraction and benchmark commands
- `docs/`: research evidence register, evaluation protocol and demonstration guide

Code is supplied under the MIT license. Dataset-derived files remain CC BY 4.0.
