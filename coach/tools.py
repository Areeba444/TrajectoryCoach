"""Read-only tool interface for the coaching agent.

The agent never touches learner code or course outcomes. It can only ask for
summaries of what the trajectory engine has already observed. Every tool is
read-only, validates its arguments, and counts against a per-run call budget.
"""
from .core import EDIT


class ToolError(ValueError):
    """Raised for unknown tools, bad arguments or an exhausted call budget."""


def _state(coach, student):
    state = coach.states.get(str(student))
    if state is None:
        raise ToolError('No active learner: ' + str(student))
    return state


def get_trajectory_summary(coach, student):
    """Counts and timing for the learner's current observation window."""
    s = _state(coach, student)
    counts = s.counts
    return {
        'student': str(student),
        'part_exercise': list(s.task) if s.task else None,
        'session': s.session,
        'window_seconds': coach.window_seconds,
        'window_events': len(s.history),
        'runs': counts['run'],
        'edits': sum(counts[k] for k in EDIT),
        'submissions': counts['submit'],
        'active_seconds_estimate': s.session_seconds,
        'last_event': s.last_event,
        'last_source_row': s.history[-1].source_row if s.history else None,
        'outcomes_observed': False,  # logs never reveal test results or correctness
    }


def get_prior_interventions(coach, student, limit=5):
    """The most recent prompts delivered to this learner in the current task."""
    s = _state(coach, student)
    if type(limit) is not int or not 1 <= limit <= 5:
        raise ToolError('limit must be an integer from 1 to 5')
    return {'student': str(student), 'prompts_this_task': s.task_prompts,
            'recent': list(s.recent_decisions)[-limit:]}


def get_learner_reflection(coach, student):
    """The learner's latest written reflection (untrusted text, may be empty)."""
    s = _state(coach, student)
    return {'student': str(student), 'reflection': s.reflection,
            'reflection_time': s.reflection_time}


def check_evidence_row(coach, student, source_row):
    """Is this source row inside the learner's current observation window?"""
    s = _state(coach, student)
    if type(source_row) is not int:
        raise ToolError('source_row must be an integer')
    for e in s.history:
        if e.source_row == source_row:
            return {'source_row': source_row, 'in_window': True, 'event': e.event}
    return {'source_row': source_row, 'in_window': False, 'event': None}


TOOLS = {
    'get_trajectory_summary': (get_trajectory_summary,
        {'student': {'type': 'string'}}),
    'get_prior_interventions': (get_prior_interventions,
        {'student': {'type': 'string'}, 'limit': {'type': 'integer', 'minimum': 1, 'maximum': 5}}),
    'get_learner_reflection': (get_learner_reflection,
        {'student': {'type': 'string'}}),
    'check_evidence_row': (check_evidence_row,
        {'student': {'type': 'string'}, 'source_row': {'type': 'integer'}}),
}


def tool_specs():
    """JSON-schema descriptions in the shape LLM function-calling APIs expect."""
    specs = []
    for name, (fn, props) in TOOLS.items():
        required = [k for k in props if k != 'limit']
        specs.append({'type': 'function', 'name': name, 'description': (fn.__doc__ or '').strip(),
                      'parameters': {'type': 'object', 'properties': props,
                                     'required': required, 'additionalProperties': False}})
    return specs


class ToolBox:
    """Dispatches tool calls against one coach, with a call budget and a log."""

    def __init__(self, coach, max_calls=20):
        self.coach, self.max_calls, self.calls, self.log = coach, max_calls, 0, []

    def call(self, name, **args):
        if name not in TOOLS:
            raise ToolError('Unknown tool: ' + name)
        if self.calls >= self.max_calls:
            raise ToolError('Tool call budget exhausted')
        fn, props = TOOLS[name]
        extra = set(args) - set(props)
        if extra:
            raise ToolError('Unexpected arguments: ' + ', '.join(sorted(extra)))
        self.calls += 1
        result = fn(self.coach, **args)
        self.log.append({'tool': name, 'args': args})
        return result
