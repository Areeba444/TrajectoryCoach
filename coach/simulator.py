"""G3: parametrised simulated learners for validating the transfer instrument.

This does not model real students and produces no evidence about human
learning. Its only purpose is to check whether the delayed, no-AI transfer
task and rubric separate internalised skill from assisted completion, which
is the dissociation reported by Bassner et al. A simulated learner has a
latent skill, a reliance on assistance, and an engagement level. Assistance
raises the chance of finishing a task now; only scaffolds the learner actually
answers raise latent skill, and reliance damps that gain.

If the rubric is a usable instrument, transfer scores should track latent
skill after the assisted session, while assisted completion should track it
less closely because reliance inflates it.
"""
import math, random
from dataclasses import dataclass, asdict

CONDITIONS = ('unassisted', 'on_demand', 'trajectory')

# Share of delivered scaffolds a learner actually engages with, by condition.
# The trajectory condition is higher because scaffolds arrive at junctures;
# this is the simulator's assumption, not a measured value.
ENGAGEMENT_CEILING = {'unassisted': 0.0, 'on_demand': 0.45, 'trajectory': 0.70}
SCAFFOLDS = {'unassisted': 0, 'on_demand': 3, 'trajectory': 3}
COMPLETION_BOOST = {'unassisted': 0.0, 'on_demand': 1.10, 'trajectory': 0.85}

ALPHA = 0.22      # how much an engaged scaffold can raise latent skill
DECAY = 0.04      # forgetting over the seven-day delay
SLOPE = 4.0       # logistic slope on (skill - difficulty)


def _sigmoid(z):
    return 1.0 / (1.0 + math.exp(-z))


@dataclass
class SimLearner:
    ident: int
    skill: float
    reliance: float
    engagement: float


def make_cohort(n, rng):
    return [SimLearner(i, rng.betavariate(2, 2), rng.random(), rng.betavariate(2, 2))
            for i in range(n)]


def assisted_session(learner, condition, difficulties, rng):
    """Returns assisted completion rate and the latent skill gained."""
    boost = COMPLETION_BOOST[condition]
    # A learner who leans on help gains more completion from it and less skill.
    completed = 0
    for d in difficulties:
        p = _sigmoid(SLOPE * (learner.skill - d) + boost * (0.4 + 0.6 * learner.reliance))
        completed += 1 if rng.random() < p else 0
    engaged = 0
    for _ in range(SCAFFOLDS[condition]):
        p = ENGAGEMENT_CEILING[condition] * learner.engagement
        engaged += 1 if rng.random() < p else 0
    denom = SCAFFOLDS[condition] or 1
    gain = ALPHA * (engaged / denom) * (1 - learner.reliance) * (1 - learner.skill)
    return completed / len(difficulties), gain


def transfer_task(skill, difficulties, rng):
    """Delayed, no-AI rubric score in [0, 4] averaged over the transfer tasks."""
    total = 0.0
    for d in difficulties:
        p = _sigmoid(SLOPE * (skill - d))
        # Four rubric points: restates the goal, produces a case, handles the
        # edge case, returns a correct value. Later points are harder.
        total += sum(1 for level in (0.25, 0.50, 0.75, 1.00) if rng.random() < p ** level)
    return total / len(difficulties)


def run_study(n_learners=120, condition='trajectory', seed=0,
              session_difficulties=(0.3, 0.45, 0.55, 0.65, 0.75, 0.85),
              transfer_difficulties=(0.35, 0.5, 0.65, 0.8)):
    rng = random.Random(seed)
    rows = []
    for learner in make_cohort(n_learners, rng):
        completion, gain = assisted_session(learner, condition, session_difficulties, rng)
        post_skill = max(0.0, min(1.0, learner.skill + gain - DECAY))
        score = transfer_task(post_skill, transfer_difficulties, rng)
        rows.append({**asdict(learner), 'condition': condition,
                     'assisted_completion': completion, 'skill_gain': gain,
                     'latent_skill_after': post_skill, 'transfer_score': score})
    return rows
