"""Public CMS spending analysis. Python standard library only; pinned source."""
from pathlib import Path
from decimal import Decimal, ROUND_HALF_UP
import csv
import hashlib
import io
import json
import sqlite3
import urllib.request

ROOT = Path(__file__).resolve().parent
YEARS = range(2020, 2025)
# Explicit single-agent cohort; excludes insulin combinations and GLP-2 drugs.
INCRETINS = {'semaglutide', 'tirzepatide', 'dulaglutide', 'liraglutide',
             'exenatide', 'exenatide microspheres', 'lixisenatide'}

def number(value):
    if value is None or not str(value).strip():
        return None
    value = Decimal(str(value))
    if not value.is_finite() or value < 0:
        raise ValueError('Expected finite nonnegative source number')
    return value

def integer(value):
    value = number(value)
    if value is None:
        return None
    if value != value.to_integral_value():
        raise ValueError('Fractional count')
    return int(value)

def cents(value):
    value = number(value)
    return None if value is None else int((value * 100).quantize(Decimal('1'), rounding=ROUND_HALF_UP))

def normalize(source_rows):
    rows, seen = [], set()
    overall = 0
    missing = {y: 0 for y in YEARS}
    for r in source_rows:
        if r['Mftr_Name'] != 'Overall':
            continue
        overall += 1
        key = (r['Brnd_Name'], r['Gnrc_Name'])
        if key in seen:
            raise ValueError('Duplicate Overall brand/generic: ' + repr(key))
        seen.add(key)
        for year in YEARS:
            spend = cents(r.get(f'Tot_Spndng_{year}'))
            if spend is None:
                missing[year] += 1
                continue  # Missing/redacted observations remain absent, never zero-filled.
            claims = integer(r[f'Tot_Clms_{year}'])
            if claims is None or claims <= 0:
                raise ValueError('Published spend must have a positive claims denominator')
            unit = number(r.get(f'Avg_Spnd_Per_Dsg_Unt_Wghtd_{year}'))
            flag = integer(r.get(f'Outlier_Flag_{year}'))
            if flag not in (0, 1, None):
                raise ValueError('Unexpected unit outlier flag')
            rows.append(dict(brand=key[0], generic=key[1], year=year,
                spend_cents=spend, claims=claims,
                beneficiaries=integer(r.get(f'Tot_Benes_{year}')),
                weighted_unit_spend=None if unit is None else float(unit),
                unit_outlier=flag,
                selected_incretin=int(key[1].lower() in INCRETINS)))
    return rows, dict(source_rows=len(source_rows), overall_products=overall,
                     manufacturer_detail_rows=len(source_rows)-overall,
                     unavailable_product_years=missing)

def bridge(previous, current):
    """Sequential quantity then average-spend bridge, dollars; not causal pricing."""
    if previous is None or current is None:
        return None
    q0, q1 = Decimal(previous['claims']), Decimal(current['claims'])
    if not q0 or not q1:
        return None
    s0, s1 = Decimal(previous['spend_cents']) / 100, Decimal(current['spend_cents']) / 100
    a0, a1 = s0 / q0, s1 / q1
    volume, average = (q1-q0)*a0, q1*(a1-a0)
    assert abs(volume+average-(s1-s0)) < Decimal('0.00001')
    return dict(change=float(s1-s0), claims_component=float(volume),
                average_spend_component=float(average),
                claims_growth_pct=float((q1/q0-1)*100),
                average_spend_growth_pct=float((a1/a0-1)*100) if a0 else None)

def analyze(rows, quality, source):
    db=sqlite3.connect(':memory:'); db.row_factory=sqlite3.Row
    db.execute('CREATE TABLE drug_years(brand TEXT,generic TEXT,year INTEGER,spend_cents INTEGER,claims INTEGER,beneficiaries INTEGER,weighted_unit_spend REAL,unit_outlier INTEGER,selected_incretin INTEGER,PRIMARY KEY(brand,generic,year))')
    db.executemany('INSERT INTO drug_years VALUES(:brand,:generic,:year,:spend_cents,:claims,:beneficiaries,:weighted_unit_spend,:unit_outlier,:selected_incretin)',rows)
    cohorts={}
    for cohort in ('all','incretin'):
        annual=[dict(r) for r in db.execute((ROOT/'sql/summary.sql').read_text(),{'cohort':cohort})]
        for a in annual:
            a['top_products']=[dict(r) for r in db.execute((ROOT/'sql/top_products.sql').read_text(),{'cohort':cohort,'year':a['year']})]
            a['top10_share_pct']=100*sum(r['spend_cents'] for r in a['top_products'])/a['spend_cents'] if a['spend_cents'] else None
            a['average_spend_per_claim']=a['spend_cents']/100/a['claims'] if a['claims'] else None
        cohorts[cohort]=annual
    stories=[]
    for brand,generic in sorted({(r['brand'],r['generic']) for r in rows if r['selected_incretin']}):
        history=[r for r in rows if (r['brand'],r['generic'])==(brand,generic)]
        by_year={r['year']:r for r in history}
        stories.append({'brand':brand,'generic':generic,'history':history,'bridge':bridge(by_year.get(2023),by_year.get(2024))})
    quality['checks']={
        'overall_keys_unique':len({(r['brand'],r['generic'],r['year']) for r in rows})==len(rows),
        'source_rows_partition':quality['source_rows']==quality['overall_products']+quality['manufacturer_detail_rows'],
        'historical_coverage_reconciles':all(len([r for r in rows if r['year']==y])+quality['unavailable_product_years'][y]==quality['overall_products'] for y in YEARS),
        'annual_spend_reconciles':all(a['spend_cents']==sum(r['spend_cents'] for r in rows if r['year']==a['year']) for a in cohorts['all']),
        'selected_cohort_is_subset':all(s['spend_cents']<=a['spend_cents'] for s,a in zip(cohorts['incretin'],cohorts['all'])),
        'bridges_reconcile':all(abs(s['bridge']['claims_component']+s['bridge']['average_spend_component']-s['bridge']['change'])<0.01 for s in stories if s['bridge']),
    }
    if not all(quality['checks'].values()): raise AssertionError(quality['checks'])
    db.close()
    return {'data_kind':'public_cms','source':source,'cohorts':cohorts,'stories':stories,'quality':quality}

def main():
    source=json.loads((ROOT/'source.json').read_text())
    path=ROOT/'data/raw/cms_part_d_2024.csv';path.parent.mkdir(parents=True,exist_ok=True)
    if not path.exists():
        with urllib.request.urlopen(source['download_url'],timeout=60) as response:
            path.write_bytes(response.read())
    raw=path.read_bytes()
    if hashlib.sha256(raw).hexdigest()!=source['sha256']:
        raise ValueError('Source checksum changed. Review the new release before updating source.json.')
    records=list(csv.DictReader(io.StringIO(raw.decode('utf-8-sig'))))
    rows,quality=normalize(records);data=analyze(rows,quality,source)
    (ROOT/'outputs').mkdir(exist_ok=True);(ROOT/'dashboard').mkdir(exist_ok=True)
    for folder in ('outputs','dashboard'):
        (ROOT/folder/'data.json').write_text(json.dumps(data,indent=2)+'\n')
    for filename, export in [('drug_years.csv',rows),('selected_incretin_drugs.csv',[r for r in rows if r['selected_incretin']])]:
        with (ROOT/'outputs'/filename).open('w',newline='') as f:
            writer=csv.DictWriter(f,fieldnames=list(export[0]));writer.writeheader();writer.writerows(export)
    latest=data['cohorts']['all'][-1];group=data['cohorts']['incretin'][-1]
    oz=next(s for s in data['stories'] if s['brand']=='Ozempic');b=oz['bridge']
    findings=f'''# Findings from the pinned CMS release

Source: [CMS Medicare Part D Spending by Drug]({source['landing_page']}), released {source['release_date']}; observation years 2020–2024. This is public aggregate data, analyzed with AI assistance.

## What stands out

- The {latest['products']:,} listed products have **${latest['spend_cents']/100/1e9:,.2f} billion** in reported gross spending for 2024. The ten largest account for **{latest['top10_share_pct']:.1f}%** of that listed-product total.
- The explicitly selected single-agent GLP-1 / GIP cohort accounts for **${group['spend_cents']/100/1e9:.2f} billion**, or **{100*group['spend_cents']/latest['spend_cents']:.1f}%** of listed-product spending. Insulin combination products are excluded by design.
- Ozempic gross spending increased **${b['change']/1e9:.2f} billion** between 2023 and 2024. The arithmetic bridge attributes **${b['claims_component']/1e9:.2f} billion** to the change in claim count at 2023 average spending, and **${b['average_spend_component']/1e9:.2f} billion** to the subsequent change in average spending per claim at 2024 claim volume.

## How to use the findings

Start a budget discussion with spending concentration and changes in claim volume. For a specific drug, inspect average spending per claim alongside claim counts. A rise in total spending can occur while average spending per claim falls. This decomposition describes the arithmetic; it does not establish the causes.

## Limits that matter

This release excludes drugs with fewer than 11 claims in 2024. Historical cells can be redacted; missing cells are never zero-filled. Earlier-year totals describe the products visible in this release, not a complete historical market census. Spending is gross and excludes manufacturer rebates. Medicare results do not represent an employer population. A claim is a prescription fill, with varying days supplied; average spending per claim is not a standardized unit price. Beneficiaries overlap across products and are not summed into a unique-person total. The data does not identify treatment indication, adherence, health outcomes, or a suitable treatment for any individual.

## Reproduce and challenge it

Run `python analysis.py` and `python -m unittest discover -s tests -v`. Check `source.json`, the SQL files, and `METHODOLOGY.md`. Try changing the explicit cohort definition; retain the missing-value rules and avoid adding manufacturer rows to the Overall summaries.
'''
    (ROOT/'outputs/findings.md').write_text(findings)
    print(json.dumps({'listed_products':latest['products'],'gross_spending_2024':latest['spend_cents']/100,'cohort_spending_2024':group['spend_cents']/100,'checks':quality['checks']},indent=2))

if __name__=='__main__':main()
