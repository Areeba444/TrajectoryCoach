"""Live coaching session: watches an event file and feeds it to the engine.

Usage:
    python -m coach.cli --input data/demo.csv [--student 5] [--mode adaptive]
    python -m coach.cli --input data/demo.csv --replay
    python -m coach.cli --input data/demo.csv --groq

In live mode it tails the file, sleeping 0.1s between reads.
In replay mode (--replay) it feeds all rows as fast as possible.
Prints each non-wait Decision in human-readable format.
"""
import argparse
import csv
import gzip
import os
import sys
import time
from pathlib import Path

from .core import Event, TrajectoryCoach, Decision
from .grounding import evidence_floor_met


def _format_decision(d: Decision) -> str:
    lines = [
        f'[{d.phase.upper()}] {d.reason}',
        f'  Prompt : {d.prompt}',
        f'  Provider: {d.provider}',
    ]
    return '\n'.join(lines)


def _open_file(path: Path):
    """Open a CSV or gzip CSV file and return (file_obj, reader)."""
    if str(path).endswith('.gz'):
        f = gzip.open(path, 'rt', encoding='utf-8', newline='')
    else:
        f = open(path, 'r', encoding='utf-8', newline='')
    reader = csv.DictReader(f)
    return f, reader


def _make_coach(args) -> TrajectoryCoach:
    """Build TrajectoryCoach from CLI args."""
    provider = None
    if args.groq:
        from .groq_provider import GroqProvider
        provider = GroqProvider()

    return TrajectoryCoach(
        mode=args.mode,
        provider=provider,
        gate_seconds=45,
        min_evidence=5,
        use_timing_gate=not args.no_gate,
        use_evidence_floor=not args.no_floor,
    )


def _run_replay(coach: TrajectoryCoach, path: Path, student_filter: str | None):
    """Feed all rows as fast as possible."""
    f, reader = _open_file(path)
    with f:
        for rownum, row in enumerate(reader, 2):
            if student_filter and str(row.get('student', '')) != student_filter:
                continue
            try:
                event = Event.from_row(row, rownum)
            except (ValueError, KeyError):
                continue
            d = coach.observe(event)
            if d.phase != 'wait':
                print(f'\n--- Row {rownum} | Student {event.student} ---')
                print(_format_decision(d))


def _run_live(coach: TrajectoryCoach, path: Path, student_filter: str | None):
    """Tail the file, sleeping 0.1s between reads."""
    print(f'[live] Watching {path} ... (Ctrl-C to stop)', flush=True)
    seen_rows = 0
    header = None

    while True:
        try:
            f, reader = _open_file(path)
            with f:
                for rownum, row in enumerate(reader, 2):
                    if rownum <= seen_rows:
                        continue
                    seen_rows = rownum
                    if student_filter and str(row.get('student', '')) != student_filter:
                        continue
                    try:
                        event = Event.from_row(row, rownum)
                    except (ValueError, KeyError):
                        continue
                    d = coach.observe(event)
                    if d.phase != 'wait':
                        print(f'\n--- Row {rownum} | Student {event.student} ---')
                        print(_format_decision(d), flush=True)
        except KeyboardInterrupt:
            print('\n[live] Stopped.')
            break
        except Exception as e:
            print(f'[live] Error: {e}', file=sys.stderr)

        time.sleep(0.1)


def main():
    parser = argparse.ArgumentParser(description='TrajectoryCoach live/replay CLI')
    parser.add_argument('--input', required=True, help='Event CSV or CSV.GZ file')
    parser.add_argument('--student', default=None, help='Filter to one student id')
    parser.add_argument('--mode', default='adaptive',
                        choices=['rule', 'adaptive', 'no_memory', 'no_cooldown'],
                        help='Coach mode')
    parser.add_argument('--replay', action='store_true',
                        help='Replay all rows at once (default: live tail)')
    parser.add_argument('--groq', action='store_true',
                        help='Use Groq provider (requires GROQ_API_KEY)')
    parser.add_argument('--no-gate', action='store_true',
                        help='Disable timing gate (G1)')
    parser.add_argument('--no-floor', action='store_true',
                        help='Disable evidence floor (G2)')
    args = parser.parse_args()

    path = Path(args.input)
    if not path.exists():
        print(f'Error: file not found: {path}', file=sys.stderr)
        sys.exit(1)

    coach = _make_coach(args)

    if args.replay:
        _run_replay(coach, path, args.student)
    else:
        _run_live(coach, path, args.student)


if __name__ == '__main__':
    main()

