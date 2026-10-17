"""Extract complete contiguous learner records 0..23 from the Zenodo CSV.

Fails unless learner 24 is encountered, demonstrating the preceding boundary.
This is a convenience subset for engineering, not a population sample.
"""
import argparse,csv,gzip,hashlib,json,pathlib

def extract(source,out,limit=24):
    out=pathlib.Path(out);out.mkdir(parents=True,exist_ok=True)
    dst=out/'zenodo_24_students.csv.gz';counts={};event_counts={};boundary=False
    inversions=0; buffered=[]; prev_time=None
    with open(source,newline='',encoding='utf-8') as f, gzip.open(dst,'wt',newline='',encoding='utf-8') as w:
        reader=csv.DictReader(f);writer=csv.DictWriter(w,fieldnames=reader.fieldnames+['sourceRow']);writer.writeheader()
        last=-1
        for raw_number,row in enumerate(reader,2):
            sid=int(row['student'])
            if sid<last:raise ValueError('Expected contiguous learner ordering')
            if sid!=last:
                writer.writerows(sorted(buffered,key=lambda r:r['timestamp']))
                buffered=[];prev_time=None
            last=sid
            if sid>=limit:boundary=True;break
            if prev_time is not None and row['timestamp']<prev_time:inversions+=1
            prev_time=row['timestamp'];row['sourceRow']=raw_number;buffered.append(row)
            counts[str(sid)]=counts.get(str(sid),0)+1
            k=row['eventType'];event_counts[k]=event_counts.get(k,0)+1
    if not boundary or len(counts)!=limit:raise ValueError('Incomplete subset; boundary not reached')
    manifest={'source_doi':'10.5281/zenodo.6903968','license':'CC-BY-4.0',
      'creators':['Juho Leinonen','Arto Hellas'],'accessed':'2026-10-17',
      'selection':f'First {limit} complete contiguous student identifiers (0..{limit-1}); convenience sample',
      'boundary_observed':limit,'students':len(counts),'events':sum(counts.values()),
      'preprocessing':'Stable timestamp sort within learner; original sourceRow preserved; identical events retained',
      'raw_adjacent_timestamp_inversions':inversions,
      'events_per_student':counts,'event_counts':event_counts,
      'compressed_sha256':hashlib.sha256(dst.read_bytes()).hexdigest(),
      'content_sha256':hashlib.sha256(gzip.decompress(dst.read_bytes())).hexdigest(),
      'full_source_md5_verified':False,
      'caution':'Downloaded source prefix; full 1.36 GB file not needed for this baseline. No population or learning-effect inference.'}
    (out/'manifest.json').write_text(json.dumps(manifest,indent=2),encoding='utf-8')
    return manifest
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('source');p.add_argument('--out',default='data');a=p.parse_args()
    print(json.dumps(extract(a.source,a.out),indent=2))
