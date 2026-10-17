"""Causal event processing. No course outcome is available to the policy."""
from collections import Counter, deque
from dataclasses import dataclass, field, asdict
from datetime import datetime
from typing import Optional

EVENTS = {'text_insert','text_remove','text_paste','focus_gained','focus_lost','run','submit'}
EDIT = {'text_insert','text_remove','text_paste'}

@dataclass(frozen=True)
class Event:
    student: str
    part: str
    exercise: str
    event: str
    time: float
    source_row: int = 0

    @classmethod
    def from_row(cls, row, number=0):
        name = row['eventType']
        if name not in EVENTS:
            raise ValueError('Unknown event type: '+name)
        dt = datetime.strptime(row['timestamp'], '%Y-%m-%d %H:%M:%S')
        # A timezone-free ordinal preserves original relative durations.
        t = dt.toordinal()*86400 + dt.hour*3600 + dt.minute*60 + dt.second
        return cls(str(row['student']),str(row['part']),str(row['exercise']),name,t,int(row.get('sourceRow') or number))

@dataclass
class Decision:
    phase: str
    reason: str
    prompt: str
    evidence: dict
    provider: str = 'deterministic'

@dataclass
class LearnerState:
    history: deque = field(default_factory=deque)
    counts: Counter = field(default_factory=Counter)
    last_time: Optional[float] = None
    last_event: Optional[str] = None
    task: Optional[tuple] = None
    session: int = 0
    session_seconds: float = 0
    task_prompts: int = 0
    last_prompt: Optional[float] = None
    pending_until: float = 0
    reflection: str = ''
    reflection_time: Optional[float] = None
    first_edit: bool = True
    recent_decisions: deque = field(default_factory=lambda:deque(maxlen=5))

class TrajectoryCoach:
    """rule = uncapped trigger baseline; adaptive = stateful policy prototype.

    Thresholds are engineering defaults, not validated diagnoses of cognition.
    Session gaps > 30 minutes reset local state. A task switch clears its window.
    Equal timestamps keep source order; backwards time is rejected.
    """
    def __init__(self, mode='adaptive', window_seconds=300, cooldown=180,
                 max_prompts=3, run_threshold=3, provider=None):
        if mode not in {'rule','adaptive','no_memory','no_cooldown'}:
            raise ValueError('Unknown mode')
        if min(window_seconds,run_threshold,max_prompts)<=0 or cooldown<0:
            raise ValueError('Invalid policy configuration')
        self.mode, self.window_seconds = mode, window_seconds
        self.cooldown, self.max_prompts, self.run_threshold = cooldown,max_prompts,run_threshold
        self.provider = provider
        self.states = {}

    def reflect(self, student, text, now):
        state=self.states.get(str(student))
        if state is None: raise ValueError('No active learner')
        if state.last_time is not None and now<state.last_time:
            raise ValueError('Reflection predates current state')
        if not text.strip(): raise ValueError('Reflection cannot be blank')
        state.reflection=text.strip()[:1000]
        state.reflection_time=now
        state.pending_until=0

    def observe(self, event):
        if event.event not in EVENTS: raise ValueError('Unknown event')
        s=self.states.setdefault(event.student,LearnerState())
        if s.last_time is not None and event.time<s.last_time:
            raise ValueError('Events must be ordered within each student')
        gap=0 if s.last_time is None else event.time-s.last_time
        new_session=s.last_time is None or gap>1800
        new_task=s.task!=(event.part,event.exercise)
        if new_session or new_task:
            s.history.clear(); s.counts.clear(); s.first_edit=True; s.task_prompts=0
            s.last_prompt=None; s.pending_until=0; s.reflection=''; s.reflection_time=None
            s.recent_decisions.clear(); s.task=(event.part,event.exercise)
        if new_session:
            s.session+=1; s.session_seconds=0
        elif s.last_event!='focus_lost':
            s.session_seconds+=min(gap,60)
        s.history.append(event)
        s.counts[event.event]+=1
        while s.history and event.time-s.history[0].time>self.window_seconds:
            s.counts[s.history.popleft().event]-=1
        counts=s.counts
        evidence={'student':event.student,'part':event.part,'exercise':event.exercise,
                  'session':s.session,'source_row':event.source_row,'time':event.time,
                  'window_seconds':self.window_seconds,'window_events':len(s.history),
                  'runs':counts['run'],'edits':sum(counts[k] for k in EDIT),
                  'submissions':counts['submit'],'active_seconds_estimate':s.session_seconds,
                  'current_event':event.event,'gap_seconds':gap,
                  'outcomes_observed':False}
        phase,reason='wait','No trigger'
        if event.event=='submit': phase,reason='evaluate','Submission observed; correctness unknown'
        elif s.first_edit and event.event in EDIT:
            phase,reason='plan','First observed edit in this task/session'
        elif event.event=='run' and counts['run']>=self.run_threshold and evidence['edits']:
            phase,reason='monitor','Repeated executions within the observation window'
        if event.event in EDIT: s.first_edit=False
        s.last_time,s.last_event=event.time,event.event
        if self.mode!='rule' and phase!='wait':
            if self.mode!='no_memory' and s.task_prompts>=self.max_prompts:
                phase,reason='wait','Task/session prompt budget exhausted'
            elif self.mode!='no_memory' and event.time<s.pending_until:
                phase,reason='wait','Waiting for learner response'
            elif self.mode!='no_cooldown' and s.last_prompt is not None and event.time-s.last_prompt<self.cooldown:
                phase,reason='wait','Cooldown active'
        prompts={
            'plan':'Before the next step, state your goal and one input-output example you expect.',
            'monitor':f"The recent window contains {counts['run']} runs. What hypothesis are you checking, and what result would support it?",
            'evaluate':'A submission was recorded. What evidence would you use to check correctness, including an edge case?',
            'wait':''}
        d=Decision(phase,reason,prompts[phase],evidence)
        if self.provider and phase!='wait':
            # Provider can ask to wait or rephrase the current permitted scaffold.
            # It never executes code or grants access to outcome labels.
            context={'observation':evidence,'allowed_phase':phase,'reflection':s.reflection,
                     'recent_decisions':list(s.recent_decisions)}
            try:
                d=self.provider.generate(d,context)
            except Exception as exc:
                d.provider='fallback:'+type(exc).__name__
        if d.phase!='wait':
            s.task_prompts+=1; s.last_prompt=event.time; s.pending_until=event.time+120
            s.recent_decisions.append({'phase':d.phase,'reason':d.reason})
        return d

def decision_dict(d): return asdict(d)
