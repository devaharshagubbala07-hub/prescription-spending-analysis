"""Independent release controls for the native report; no DAX engine claims.

Run from the repository root after python analysis.py. Reads only the pinned
CMS bytes already downloaded by that pipeline. Python standard library only.
"""
from pathlib import Path
from decimal import Decimal, ROUND_HALF_UP
import csv, hashlib, io, json

ROOT=Path(__file__).resolve().parents[2]
manifest=json.loads((ROOT/'source.json').read_text())
raw=(ROOT/'data/raw/cms_part_d_2024.csv').read_bytes()
assert hashlib.sha256(raw).hexdigest()==manifest['sha256']
rows=list(csv.DictReader(io.StringIO(raw.decode('utf-8-sig'))))
overall=[r for r in rows if r['Mftr_Name']=='Overall']
assert len(overall)==3625
assert len({(r['Brnd_Name'],r['Gnrc_Name']) for r in overall})==len(overall)
assert len({r['Brnd_Name']+' ('+r['Gnrc_Name']+')' for r in overall})==len(overall)
ingredients={'semaglutide','tirzepatide','dulaglutide','liraglutide','exenatide','exenatide microspheres','lixisenatide'}
def money(v):return None if not v.strip() else int((Decimal(v)*100).quantize(Decimal('1'),rounding=ROUND_HALF_UP))
controls=[];observations=0
for y in range(2020,2025):
 available=[r for r in overall if r['Tot_Spndng_'+str(y)].strip()]
 observations+=len(available)
 for cohort in ('all','incretin'):
  selected=available if cohort=='all' else [r for r in available if r['Gnrc_Name'].lower() in ingredients]
  spend=sum(money(r['Tot_Spndng_'+str(y)]) for r in selected)
  fills=sum(int(Decimal(r['Tot_Clms_'+str(y)])) for r in selected)
  controls.append({'year':y,'cohort':cohort,'available_products':len(selected),'spending_cents':spend,'prescription_fills':fills})
all2024=next(c for c in controls if c['year']==2024 and c['cohort']=='all')
group2024=next(c for c in controls if c['year']==2024 and c['cohort']=='incretin')
assert all2024['spending_cents']==28866784205840
assert group2024['spending_cents']==2751335012766
assert group2024['prescription_fills']==21833867
oz=next(r for r in overall if r['Brnd_Name']=='Ozempic' and r['Gnrc_Name']=='Semaglutide')
assert money(oz['Tot_Spndng_2024'])==1297029634700
lir=next(r for r in overall if r['Brnd_Name']=='Liraglutide' and r['Gnrc_Name']=='Liraglutide')
assert money(lir['Tot_Spndng_2023']) is None
weg=next(r for r in overall if r['Brnd_Name']=='Wegovy' and r['Gnrc_Name']=='Semaglutide')
assert Decimal(weg['Tot_Clms_2023'])==142

# Confirm the exported Python/SQL cohort summaries agree with direct source sums.
reference=json.loads((ROOT/'outputs/data.json').read_text())
for c in controls:
 key='all' if c['cohort']=='all' else 'incretin'
 a=next(v for v in reference['cohorts'][key] if v['year']==c['year'])
 assert (a['products'],a['spend_cents'],a['claims'])==(c['available_products'],c['spending_cents'],c['prescription_fills'])

result={'source_sha256':manifest['sha256'],'release_date':manifest['release_date'],'source_rows':len(rows),
 'overall_products':len(overall),'available_drug_years':observations,'annual_controls':controls,
 'special_cases':{'liraglutide_2023_spending':'unavailable','wegovy_2023_fills':142},
 'validation_scope':'Direct source controls and agreement with the existing Python/SQL outputs. Power Query and DAX execution still require Power BI Desktop.'}
(Path(__file__).parent/'source_controls.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps({'available_drug_years':observations,'annual_control_rows':len(controls),'source_controls':'PASS','native_desktop_validation':'pending'},indent=2))
