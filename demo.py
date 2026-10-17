"""Five-minute classroom walkthrough using an explicitly synthetic trace."""
import argparse,csv,json
from pathlib import Path
from coach.core import Event,TrajectoryCoach

def main():
    p=argparse.ArgumentParser();p.add_argument('--interactive',action='store_true');a=p.parse_args()
    print('TrajectoryCoach | SYNTHETIC EVENT WALKTHROUGH\n')
    engines={m:TrajectoryCoach(mode=m) for m in ('rule','adaptive')}
    for i,row in enumerate(csv.DictReader((Path(__file__).parent/'data/demo.csv').open()),2):
        e=Event.from_row(row,i)
        print(f"{row['timestamp']}  {e.event}")
        for mode,c in engines.items():
            d=c.observe(e)
            print(f"  {mode:8} -> {d.phase:8} | {d.reason}")
            if d.prompt:print('  '+d.prompt)
        if a.interactive:
            response=input('Reflection (Enter to continue): ').strip()
            if response:
                for c in engines.values():c.reflect(e.student,response,e.time)
    print('\nNo bugs, test outcomes, or learning gains were inferred from this trace.')
if __name__=='__main__':main()
