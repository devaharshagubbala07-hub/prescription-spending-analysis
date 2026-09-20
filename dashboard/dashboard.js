(() => {
  'use strict';
  const $=id=>document.getElementById(id);
  const money=n=>n==null?'—':new Intl.NumberFormat('en-US',{style:'currency',currency:'USD',maximumFractionDigits:2}).format(n);
  const compactMoney=n=>n==null?'—':new Intl.NumberFormat('en-US',{style:'currency',currency:'USD',notation:'compact',maximumFractionDigits:2}).format(n);
  const integer=n=>new Intl.NumberFormat('en-US').format(n);
  const pct=n=>n==null?'—':n.toFixed(1)+'%';
  let data,current;
  try{if(localStorage.getItem('dg-portfolio-motion')==='off')document.documentElement.dataset.motion='off';}catch(_){}
  function bar(label,value,width,note){
    const li=document.createElement('li'),top=document.createElement('div'),title=document.createElement('strong'),amount=document.createElement('span'),track=document.createElement('div'),fill=document.createElement('span'),detail=document.createElement('small');
    top.className='bar-top';title.textContent=label;amount.textContent=value;top.append(title,amount);
    track.className='track';track.setAttribute('aria-hidden','true');fill.className='fill';fill.style.setProperty('--width',Math.max(0,Math.min(100,width))+'%');track.append(fill);
    detail.className='bar-detail';detail.textContent=note;li.append(top,track,detail);return li;
  }
  function render(){
    const cohort=$('cohort').value,year=Number($('year').value),history=data.cohorts[cohort];
    current=history.find(x=>x.year===year);const all=data.cohorts.all.find(x=>x.year===year);
    const group=cohort==='all'?'All listed products':'Selected GLP-1 / GIP drugs';
    $('scope').textContent=`${group} · ${year} observations · ${integer(current.products)} available products · CMS June 2026 release`;
    $('spend').textContent=compactMoney(current.spend_cents/100);$('claims').textContent=new Intl.NumberFormat('en-US',{notation:'compact',maximumFractionDigits:2}).format(current.claims);
    $('average').textContent=money(current.average_spend_per_claim);$('share').textContent=pct(100*current.spend_cents/all.spend_cents);
    const maximum=Math.max(...history.map(x=>x.spend_cents));
    $('trend').replaceChildren(...history.map(x=>bar(String(x.year)+(x.year===year?' · selected':''),compactMoney(x.spend_cents/100),100*x.spend_cents/maximum,`${integer(x.products)} available products · ${integer(x.claims)} fills`)));
    $('concentration').textContent=`Top ${current.top_products.length} products = ${pct(current.top10_share_pct)} of selected spending`;
    $('leaders').replaceChildren(...current.top_products.slice(0,5).map(x=>bar(x.brand,compactMoney(x.spend_cents/100),100*x.spend_cents/current.spend_cents,`${pct(100*x.spend_cents/current.spend_cents)} of selected spending`)));
    $('product-caption').textContent=`Highest-spending ${current.top_products.length} of ${integer(current.products)} available products · ${year}. The flag concerns CMS's weighted unit-spend measure.`;
    $('products').replaceChildren(...current.top_products.map(r=>{
      const tr=document.createElement('tr');
      const values=[r.brand,money(r.spend_cents/100),integer(r.claims),money(r.spend_cents/100/r.claims),r.unit_outlier===1?'Flagged':r.unit_outlier===0?'Not flagged':'Unavailable'];
      values.forEach((v,i)=>{const td=document.createElement(i===0?'th':'td');td.textContent=v;if(i===0){td.scope='row';const small=document.createElement('small');small.textContent=r.generic;td.append(small);}tr.append(td);});return tr;
    }));
  }
  function story(){
    const s=data.stories.find(x=>x.brand===$('drug').value);$('drug-title').textContent=s.brand+' · Gross spending';
    const maximum=Math.max(...s.history.map(x=>x.spend_cents));
    $('drug-history').replaceChildren(...[2020,2021,2022,2023,2024].map(y=>{const r=s.history.find(x=>x.year===y);return bar(String(y),r?compactMoney(r.spend_cents/100):'Unavailable',r?100*r.spend_cents/maximum:0,r?integer(r.claims)+' fills':'Missing or redacted in this release');}));
    $('bridge').replaceChildren();
    if(!s.bridge){$('bridge-note').textContent='A comparable 2023 baseline is unavailable. No growth rate or decomposition is imputed.';return;}
    const b=s.bridge;
    for(const [label,value] of [['Change in fills, at 2023 average',b.claims_component],['Change in average, at 2024 volume',b.average_spend_component],['Total spending change',b.change]]){
      const dt=document.createElement('dt'),dd=document.createElement('dd');dt.textContent=label;dd.textContent=(value>0?'+':'')+compactMoney(value);if(value<0)dd.className='negative';$('bridge').append(dt,dd);
    }
    $('bridge-note').textContent=`Fills changed ${pct(b.claims_growth_pct)}; average spending per fill changed ${pct(b.average_spend_growth_pct)}. Components reconcile before display rounding. Average spending is affected by supply and mix; it is not a pure price effect or a causal estimate.`;
  }
  function download(){
    const fields=['data_kind','release_date','year','cohort','brand','generic','spend_usd','claims','average_spend_per_claim','unit_outlier'];
    const quote=x=>'"'+String(x??'').replaceAll('"','""')+'"';
    const rows=current.top_products.map(r=>['public_cms',data.source.release_date,current.year,$('cohort').value,r.brand,r.generic,(r.spend_cents/100).toFixed(2),r.claims,(r.spend_cents/100/r.claims).toFixed(4),r.unit_outlier]);
    const csv=[fields,...rows].map(r=>r.map(quote).join(',')).join('\r\n')+'\r\n',url=URL.createObjectURL(new Blob([csv],{type:'text/csv;charset=utf-8'}));
    const a=document.createElement('a');a.href=url;a.download=`cms-spending-${current.year}-${$('cohort').value}.csv`;a.click();setTimeout(()=>URL.revokeObjectURL(url),1000);
  }
  fetch('data.json').then(r=>{if(!r.ok)throw Error('Data unavailable');return r.json();}).then(payload=>{
    if(payload.data_kind!=='public_cms')throw Error('Unexpected source');data=payload;
    for(const s of data.stories){const option=document.createElement('option');option.value=s.brand;option.textContent=s.brand;$('drug').append(option);}$('drug').value='Ozempic';
    const q=data.quality;$('checks').textContent=`${Object.values(q.checks).filter(Boolean).length} of ${Object.keys(q.checks).length} checks passed`;
    $('quality').textContent=`${integer(q.source_rows)} source rows → ${integer(q.overall_products)} Overall product summaries. ${integer(q.manufacturer_detail_rows)} manufacturer-detail rows excluded to prevent double counting. Source bytes are checked against a recorded SHA-256 digest.`;
    $('cohort').addEventListener('change',render);$('year').addEventListener('change',render);$('drug').addEventListener('change',story);$('download').addEventListener('click',download);
    $('reset').addEventListener('click',()=>{$('cohort').value='incretin';$('year').value='2024';$('drug').value='Ozempic';render();story();});
    $('explorer').hidden=false;render();story();
  }).catch(e=>{$('error').hidden=false;$('explorer').hidden=true;console.error(e);});
})();
