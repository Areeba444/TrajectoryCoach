"""Simulated learner transfer instrument (Gap 3 – G3).

Implements a synthetic learner cohort to estimate the degree to which
coaching improves transfer performance on novel tasks.  No real learner
data or course outcomes are used in this module.
"""
import math
import random
from dataclasses import dataclass, field
from typing import Optional

from .stats import spearman_rho

# ── Parameters ────────────────────────────────────────────────────────────────
N_LEARNERS = 120          # simulated learners per run
N_TASKS = 6               # transfer tasks after coaching
LATENT_SKILL_RANGE = (0.3, 0.9)   # uniform draw

_CONDITIONS = ('unassisted', 'on_demand', 'trajectory')


@dataclass
class SimulatedLearner:
    """
    A synthetic learner with a latent skill level.

    - During 'coached phase': generates events, receives scaffolds
    - In 'transfer phase': given N_TASKS independent tasks, no scaffolding
    - transfer_score: weighted sum of task completion ~ latent_skill + noise
    - assisted_completion: fraction of coached tasks completed
    """
    latent_skill: float
    seed: int = 0
    _rng: random.Random = field(init=False, repr=False)
    transfer_scores: list[float] = field(default_factory=list, init=False)
    assisted_completions: list[float] = field(default_factory=list, init=False)

    def __post_init__(self):
        self._rng = random.Random(self.seed)

    def coached_phase(self, condition: str, n_coached_tasks: int = 4) -> float:
        """
        Simulate the coached phase.  Returns assisted_completion fraction.

        In 'trajectory' condition, coaching improves task completion probability.
        In 'on_demand' condition, there is a smaller benefit.
        In 'unassisted', no coaching effect.
        """
        # Scaffolding benefit factors
        benefit = {
            'unassisted': 0.0,
            'on_demand': 0.08,
            'trajectory': 0.15,
        }.get(condition, 0.0)

        completions = []
        for task_i in range(n_coached_tasks):
            # Base completion probability from latent skill + benefit + noise
            p = min(1.0, max(0.0, self.latent_skill + benefit + self._rng.gauss(0, 0.08)))
            completed = self._rng.random() < p
            completions.append(1.0 if completed else 0.0)

        self.assisted_completions = completions
        return sum(completions) / len(completions) if completions else 0.0

    def transfer_phase(self, n_tasks: int = N_TASKS) -> float:
        """
        Simulate N_TASKS independent transfer tasks (no scaffolding).
        Returns mean transfer score in [0, 1].
        """
        scores = []
        for task_i in range(n_tasks):
            # Transfer score ~ latent_skill + noise (no coaching benefit)
            p = min(1.0, max(0.0, self.latent_skill + self._rng.gauss(0, 0.10)))
            scores.append(p)
        self.transfer_scores = scores
        return sum(scores) / len(scores) if scores else 0.0


def run_transfer_study(condition: str, seed: int = 0) -> dict:
    """
    Run one condition ('unassisted', 'on_demand', 'trajectory') with N_LEARNERS learners.

    Returns:
      {condition, seed, n_learners,
       transfer_spearman_r,       # rank correlation: transfer_score ~ latent_skill
       assisted_completion_r,     # rank correlation: assisted ~ latent_skill
       transfer_scores: [...],
       latent_skills: [...]}
    """
    if condition not in _CONDITIONS:
        raise ValueError(f'Unknown condition {condition!r}. Use one of {_CONDITIONS}.')

    rng = random.Random(seed)
    learners = []
    for i in range(N_LEARNERS):
        skill = rng.uniform(*LATENT_SKILL_RANGE)
        learner = SimulatedLearner(latent_skill=skill, seed=rng.randint(0, 2**31))
        learners.append(learner)

    transfer_scores = []
    assisted_completions = []
    latent_skills = [l.latent_skill for l in learners]

    for learner in learners:
        ac = learner.coached_phase(condition)
        ts = learner.transfer_phase()
        transfer_scores.append(ts)
        assisted_completions.append(ac)

    transfer_r = spearman_rho(latent_skills, transfer_scores)
    assisted_r = spearman_rho(latent_skills, assisted_completions)

    return {
        'condition': condition,
        'seed': seed,
        'n_learners': N_LEARNERS,
        'transfer_spearman_r': round(transfer_r, 4),
        'assisted_completion_r': round(assisted_r, 4),
        'transfer_scores': [round(s, 4) for s in transfer_scores],
        'latent_skills': [round(s, 4) for s in latent_skills],
    }


def sensitivity_analysis(
    n_tasks_range: list[int] = [2, 4, 6, 8],
    seed: int = 0,
) -> list[dict]:
    """
    Vary number of transfer tasks; return [{n_tasks, spearman_r, sd}, ...]
    pooled over 5 seeds.
    """
    results = []
    for n_tasks in n_tasks_range:
        all_r = []
        for s in range(5):
            rng = random.Random(seed + s)
            learners = [
                SimulatedLearner(
                    latent_skill=rng.uniform(*LATENT_SKILL_RANGE),
                    seed=rng.randint(0, 2**31),
                )
                for _ in range(N_LEARNERS)
            ]
            transfer_scores = []
            latent_skills = []
            for l in learners:
                l.coached_phase('trajectory')
                # Override n_tasks
                l._rng = random.Random(l.seed + 999)
                ts_list = []
                for _ in range(n_tasks):
                    p = min(1.0, max(0.0, l.latent_skill + l._rng.gauss(0, 0.10)))
                    ts_list.append(p)
                transfer_scores.append(sum(ts_list) / len(ts_list))
                latent_skills.append(l.latent_skill)
            r = spearman_rho(latent_skills, transfer_scores)
            all_r.append(r)
        mean_r = sum(all_r) / len(all_r)
        variance = sum((r - mean_r) ** 2 for r in all_r) / len(all_r)
        sd = math.sqrt(variance)
        results.append({
            'n_tasks': n_tasks,
            'spearman_r': round(mean_r, 4),
            'sd': round(sd, 4),
        })
    return results

