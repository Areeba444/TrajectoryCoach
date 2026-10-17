"""Reproducible policy replay; counts describe decisions, not educational gains."""
import pathlib,sys,json
sys.path.insert(0,str(pathlib.Path(__file__).resolve().parents[1]))
from coach.__main__ import replay

root=pathlib.Path(__file__).resolve().parents[1]
results=[]
for mode in ('rule','adaptive','no_memory','no_cooldown'):
    r=replay(root/'data/zenodo_24_students.csv.gz',root/'results'/mode,mode)
    results.append({k:v for k,v in r.items() if k!='examples'})
    print(mode,r['events'],r['phases'],flush=True)
(root/'results/benchmark.json').write_text(json.dumps(results,indent=2),encoding='utf-8')
