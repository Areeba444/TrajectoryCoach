import argparse, csv, gzip, json, pathlib, time
from collections import Counter
from .core import Event,TrajectoryCoach,decision_dict

def replay(path,out,mode='adaptive',provider=None,student=None):
    out=pathlib.Path(out); out.mkdir(parents=True,exist_ok=True)
    engine=TrajectoryCoach(mode=mode,provider=provider)
    counts=Counter(); events=Counter(); reasons=Counter(); learners=set(); n=0
    started=time.perf_counter(); samples=[]
    opener=gzip.open if str(path).endswith('.gz') else open
    with opener(path,'rt',encoding='utf-8',newline='') as f, (out/'decisions.jsonl').open('w',encoding='utf-8') as w:
        for rownum,row in enumerate(csv.DictReader(f),2):
            if student is not None and str(row['student'])!=str(student): continue
            event=Event.from_row(row,rownum)
            d=engine.observe(event); n+=1; counts[d.phase]+=1; reasons[d.reason]+=1
            events[event.event]+=1; learners.add(event.student)
            if d.phase!='wait':
                item=decision_dict(d); w.write(json.dumps(item)+'\n')
                if len(samples)<20: samples.append(item)
    elapsed=time.perf_counter()-started
    summary={'mode':mode,'input':pathlib.Path(path).name,'events':n,'students':len(learners),
        'phases':dict(counts),'reasons':dict(reasons),'event_types':dict(events),
        'runtime_seconds':round(elapsed,3),'prompts_per_1000_events':round(1000*(n-counts['wait'])/n,3) if n else 0,
        'learning_effect':'NOT MEASURED','live_provider':provider is not None,'examples':samples}
    (out/'summary.json').write_text(json.dumps(summary,indent=2),encoding='utf-8')
    return summary

def main():
    p=argparse.ArgumentParser(description='Replay observations; no code correctness or learning claims.')
    p.add_argument('--input',default='data/demo.csv'); p.add_argument('--out',default='results/demo')
    p.add_argument('--mode',choices=['rule','adaptive','no_memory','no_cooldown'],default='adaptive')
    p.add_argument('--student'); p.add_argument('--live',action='store_true'); p.add_argument('--model')
    a=p.parse_args(); provider=None
    if a.live:
        from .provider import OpenAIProvider
        provider=OpenAIProvider(a.model)
    result=replay(a.input,a.out,a.mode,provider,a.student)
    print(json.dumps({k:v for k,v in result.items() if k!='examples'},indent=2))
if __name__=='__main__': main()
