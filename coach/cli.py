"""Live coaching session over a real file on disk.

This is the application interface. The learner edits an ordinary Python file
in whatever editor they like; the coach watches the file, turns saves and runs
into trajectory events, and offers a scaffold when its policy says the moment
is right. Nothing the learner writes is sent anywhere unless a live model is
enabled, and even then only the event counts are sent, never the source code.

    python -m coach.cli --file solution.py
    python -m coach.cli --file solution.py --live        (needs GROQ_API_KEY)

Commands inside the session:
    run         execute the file and record a run event
    submit      record a submission
    reflect ... record a written reflection and clear the response wait
    state       print what the coach can currently see
    quit        end the session and write the trace
"""
import argparse, json, pathlib, subprocess, sys, threading, time
from datetime import datetime

from .core import Event, TrajectoryCoach, decision_dict
from .tools import ToolBox

ROOT = pathlib.Path(__file__).resolve().parents[1]
LOGS = ROOT / 'logs'
POLL = 0.5


class Session:
    def __init__(self, path, student='local', part='live', exercise='1',
                 live=False, model=None, gate_seconds=20):
        self.path = pathlib.Path(path)
        if not self.path.exists():
            self.path.write_text('# write your solution here\n', encoding='utf-8')
            print(f'created {self.path}')
        self.student, self.part, self.exercise = student, part, exercise
        provider = None
        if live:
            from .groq_provider import GroqProvider
            provider = GroqProvider(model=model, max_calls=40)
        self.provider = provider
        self.coach = TrajectoryCoach(mode='adaptive', provider=provider,
                                     gate_seconds=gate_seconds)
        self.box = ToolBox(self.coach, max_calls=200)
        self.row = 0
        self.stop = threading.Event()
        LOGS.mkdir(parents=True, exist_ok=True)
        stamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        self.trace = (LOGS / f'session_{stamp}.jsonl').open('w', encoding='utf-8')
        self._mtime = self.path.stat().st_mtime

    # ---- plumbing --------------------------------------------------------
    def _log(self, kind, payload):
        self.trace.write(json.dumps({'t': round(time.time(), 3), 'kind': kind,
                                     **payload}) + '\n')
        self.trace.flush()

    def feed(self, kind):
        self.row += 1
        event = Event(self.student, self.part, self.exercise, kind,
                      time.time(), self.row)
        decision = self.coach.observe(event)
        self._log('event', {'event': kind, 'source_row': self.row,
                            'phase': decision.phase, 'reason': decision.reason})
        if decision.phase != 'wait':
            self._log('scaffold', decision_dict(decision))
            print(f'\n  [{decision.phase}] {decision.prompt}'
                  f'\n  why: {decision.reason}'
                  f'  (provider: {decision.provider})\n> ', end='', flush=True)
        return decision

    def watch(self):
        """A save is the only edit signal an external editor gives us."""
        while not self.stop.is_set():
            try:
                m = self.path.stat().st_mtime
                if m != self._mtime:
                    self._mtime = m
                    self.feed('text_insert')
            except FileNotFoundError:
                pass
            time.sleep(POLL)

    # ---- commands --------------------------------------------------------
    def run_file(self):
        self.feed('run')
        proc = subprocess.run([sys.executable, str(self.path)], capture_output=True,
                              text=True, timeout=20)
        out = (proc.stdout or '') + (proc.stderr or '')
        # The coach is never told whether this succeeded; only that a run happened.
        self._log('run_result', {'returncode': proc.returncode, 'bytes': len(out)})
        print(out.rstrip()[:2000] or '(no output)')

    def show_state(self):
        try:
            print(json.dumps(self.box.call('get_trajectory_summary',
                                           student=self.student), indent=2))
        except Exception as exc:
            print(f'(nothing observed yet: {exc})')

    def close(self):
        self.stop.set()
        summary = {'events': self.row, 'gate_stats': dict(self.coach.gate_stats),
                   'tool_calls': self.box.calls}
        if self.provider is not None:
            summary['model'] = self.provider.efficiency()
        self._log('session_end', summary)
        self.trace.close()
        print('\n' + json.dumps(summary, indent=2))
        print(f'trace written to {self.trace.name}')


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--file', default='solution.py')
    ap.add_argument('--student', default='local')
    ap.add_argument('--exercise', default='1')
    ap.add_argument('--live', action='store_true', help='use a live model for wording')
    ap.add_argument('--model')
    ap.add_argument('--gate-seconds', type=int, default=20, dest='gate_seconds')
    a = ap.parse_args()
    s = Session(a.file, student=a.student, exercise=a.exercise, live=a.live,
                model=a.model, gate_seconds=a.gate_seconds)
    threading.Thread(target=s.watch, daemon=True).start()
    print(f'watching {s.path}. commands: run | submit | reflect <text> | state | quit')
    try:
        while True:
            line = input('> ').strip()
            if not line:
                continue
            cmd, _, rest = line.partition(' ')
            if cmd == 'quit':
                break
            elif cmd == 'run':
                s.run_file()
            elif cmd == 'submit':
                s.feed('submit')
            elif cmd == 'reflect':
                if not rest.strip():
                    print('reflect needs some text')
                    continue
                s.coach.reflect(s.student, rest, time.time())
                s._log('reflection', {'text': rest})
                print('recorded')
            elif cmd == 'state':
                s.show_state()
            else:
                print('unknown command')
    except (EOFError, KeyboardInterrupt):
        pass
    finally:
        s.close()


if __name__ == '__main__':
    main()
