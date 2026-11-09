"""Score the human rating sheets: agreement between the two raters, and the
mean timing and relevance scores for the delivered system.
"""
import csv, json, pathlib, statistics, sys

from coach.stats import spearman, mean_sd

ROOT = pathlib.Path(__file__).resolve().parents[1]
RESULTS = ROOT / 'results' / 'phase2'


def read_sheet(path):
    """Accepts either this repo's sheet (column 'id') or the sheet used for the
    completed November study (column 'row_id')."""
    out = {}
    with open(path, encoding='utf-8', newline='') as f:
        for row in csv.DictReader(r for r in f if not r.startswith('#') and r.strip()):
            ident = row.get('id') or row.get('row_id')
            if ident and row.get('timing'):
                out[ident] = {'timing': float(row['timing']),
                              'relevance': float(row['relevance'])
                              if row.get('relevance') else None}
    return out


def weighted_kappa(a, b, lo=0, hi=4):
    """Linearly weighted kappa, the standard agreement measure for ordinal scales."""
    cats = list(range(lo, hi + 1))
    n = len(a)
    obs = sum(1 - abs(x - y) / (hi - lo) for x, y in zip(a, b)) / n
    pa = {c: sum(1 for x in a if round(x) == c) / n for c in cats}
    pb = {c: sum(1 for y in b if round(y) == c) / n for c in cats}
    exp = sum(pa[i] * pb[j] * (1 - abs(i - j) / (hi - lo)) for i in cats for j in cats)
    return None if exp == 1 else (obs - exp) / (1 - exp)


def main(paths):
    meta_path = RESULTS / 'rating_meta.json'
    meta = (json.loads(meta_path.read_text(encoding='utf-8')) if meta_path.exists()
            else {'source_condition': 'full system', 'design': 'single condition'})
    sheets = [read_sheet(p) for p in paths]
    common = sorted(set.intersection(*(set(s) for s in sheets)))
    if not common:
        print('no rows rated in common'); return
    out = {'condition': meta['source_condition'], 'raters': len(sheets),
           'rated_in_common': len(common)}
    if len(sheets) == 2:
        a = [sheets[0][i]['timing'] for i in common]
        b = [sheets[1][i]['timing'] for i in common]
        out['timing_weighted_kappa'] = round(weighted_kappa(a, b), 4)
        out['timing_rater_correlation'] = round(spearman(a, b) or 0, 4)
        ra = [sheets[0][i]['relevance'] for i in common if sheets[0][i]['relevance']]
        rb = [sheets[1][i]['relevance'] for i in common if sheets[1][i]['relevance']]
        if len(ra) == len(rb) and ra:
            out['relevance_weighted_kappa'] = round(weighted_kappa(ra, rb, 1, 4), 4)
    t = [statistics.fmean(sh[i]['timing'] for sh in sheets) for i in common]
    r = [statistics.fmean(sh[i]['relevance'] for sh in sheets) for i in common
         if all(sh[i]['relevance'] for sh in sheets)]
    tm, tsd = mean_sd(t)
    rm, rsd = mean_sd(r)
    out['mean_timing'] = round(tm, 3)
    out['sd_timing'] = round(tsd, 3)
    out['mean_relevance'] = round(rm, 3) if rm is not None else None
    out['sd_relevance'] = round(rsd, 3) if rsd is not None else None
    out['relevance_target_3_of_4_met'] = (rm is not None and rm >= 3.0)
    out['per_rater'] = {}
    for path, sheet in zip(paths, sheets):
        tv = [sheet[i]['timing'] for i in common]
        rv = [sheet[i]['relevance'] for i in common if sheet[i]['relevance']]
        tmean, tsdev = mean_sd(tv)
        rmean, rsdev = mean_sd(rv)
        out['per_rater'][pathlib.Path(path).stem] = {
            'timing_mean': round(tmean, 3), 'timing_sd': round(tsdev, 3),
            'relevance_mean': round(rmean, 3) if rmean is not None else None,
            'relevance_sd': round(rsdev, 3) if rsdev is not None else None}
    out['note'] = meta['design']
    out['timing_caveat'] = (
        'The sheet used for this study showed raters the phase and the prompt text '
        'but no information about when the scaffold was delivered relative to the '
        'learner activity. A timing judgement cannot be made from a prompt alone, so '
        'the timing column is reported for completeness and no claim rests on it. '
        'The relevance column is unaffected.')
    (RESULTS / 'human_ratings.json').write_text(json.dumps(out, indent=2), encoding='utf-8')
    print(json.dumps(out, indent=2))
    print(f'\nwrote {RESULTS / "human_ratings.json"}')


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print(__doc__); sys.exit(1)
    main(sys.argv[1:])
