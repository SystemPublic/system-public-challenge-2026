"""Check processed-data conservation, denominators, joins and JSON-stat ordering."""
from collections import Counter
from pathlib import Path
import csv
import gzip
import json

from clean_data import ROOT, jsonstat

def load(name):
    return json.loads((ROOT/'data/processed'/f'{name}.json').read_text())

def main():
    # Order independence: Year is the outer dimension; sparse zero is preserved here.
    fixture={'id':['Year','ISO'],'size':[2,2],
             'dimension':{'Year':{'category':{'index':{'2021':1,'2020':0}}},
                          'ISO':{'category':{'index':['BEN','TZA']}}},
             'value':{'0':0,'1':0.2,'3':0.4}}
    assert list(jsonstat(fixture))==[
        ({'Year':'2020','ISO':'BEN'},0.0),({'Year':'2020','ISO':'TZA'},0.2),
        ({'Year':'2021','ISO':'BEN'},None),({'Year':'2021','ISO':'TZA'},0.4)]
    q=json.loads((ROOT/'reports/quality_report.json').read_text())
    system=load('system_candidates')
    assert len(system)==q['system']['output_candidates']
    assert all(r['verification_status']=='pending_source_review' for r in system)
    assert all(r['country_iso3'] is None and r['comparator'] is None and r['trial_family_id'] is None for r in system)
    assert all(r['effect_display_eligible'] is False for r in system)
    assert len(load('system_review_queue'))==len(system)
    assert len({(r['system_id'],r['source_row']) for r in system})==len(system)
    for r in system:
        if r['system_statistic_type'] in {'hazard_ratio','odds_ratio','relative_risk_ratio'} and r['statistic_value'] is not None and r['statistic_value']<=0:
            assert 'nonpositive_ratio' in r['flags']
    for r in load('who_context'):
        if r['indicator']=='MALARIA_IRS_COVERAGE':assert r['unit']=='people'
    map_rows=load('map_context')
    expected=set()
    for path in (ROOT/'data/raw/map').glob('*.json'):
        import re
        match=re.fullmatch(r'([A-Z]{3})_(.+)_mean_(\d+)',path.stem)
        if not match:continue
        country,metric,release=match.groups()
        for coords,_ in jsonstat(json.loads(path.read_text())):
            expected.add((country,int(coords['Year']),metric,release))
    assert {(r['country_iso3'],r['year'],r['metric'],r['release']) for r in map_rows}==expected
    assert len({(r['country_iso3'],r['year'],r['metric'],r['release']) for r in map_rows})==len(map_rows)
    for r in map_rows:
        if r['value_raw']==0:assert r['value'] is None and 'zero_may_mean_missing' in r['flags']
    samples=load('pf8_samples');assert len(samples)==q['pf8']['input_samples']
    selected=[r for r in samples if r['aggregation_eligible']]
    assert len({r['case_group_id'] for r in selected})==len(selected)
    assert all(r['qc_pass'] and r['selected_case_representative'] for r in selected)
    long=load('pf8_drug_classifications')
    source_counts=Counter(r['sample_id'] for r in long)
    assert all(v==10 for v in source_counts.values())
    summary=load('pf8_resistance_context')
    for r in summary:
        assert r['n_determined']==r['n_resistant']+r['n_sensitive']
        assert r['n_total']==r['n_determined']+r['n_undetermined']+r['n_missing_or_invalid']
        if r['n_determined']==0:assert r['resistant_proportion_among_determined'] is None
        else:assert r['resistant_proportion_among_determined']==r['n_resistant']/r['n_determined']
    assert sum(r['n_total'] for r in summary)==sum(10 for r in selected if r['has_drug_classification'])
    national=load('pf8_country_year_resistance')
    assert sum(r['n_total'] for r in national)==sum(r['n_total'] for r in summary)
    for r in national:
        members=[x for x in summary if (x['country_iso3'],x['year'],x['drug_or_combination'])==(r['country_iso3'],r['year'],r['drug_or_combination'])]
        assert r['n_determined']==sum(x['n_determined'] for x in members)
        assert r['resistant_proportion_among_determined']==(r['n_resistant']/r['n_determined'] if r['n_determined'] else None)
    with gzip.open(ROOT/'data/processed/pf8_marker_calls.csv.gz','rt') as f:
        assert sum(1 for _ in csv.DictReader(f))==q['pf8']['marker_call_rows']
    print('Passed: JSON-stat dimension order/sparse values, candidate provenance, units, unique keys, sample conservation, case deduplication, resistance denominators, marker row counts.')

if __name__=='__main__':main()
