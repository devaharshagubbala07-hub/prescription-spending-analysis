"""Build the native Power BI project from readable M and DAX definitions.

No Power BI engine is emulated here. Refresh and DAX execution are checked in
Power BI Desktop using validation/desktop_checks.dax after opening the project.
"""
from pathlib import Path
import json
import uuid

ROOT = Path(__file__).resolve().parent
REPORT = ROOT / 'PrescriptionSpending.Report'
MODEL = ROOT / 'PrescriptionSpending.SemanticModel'
BASE = 'https://developer.microsoft.com/json-schemas/'
SCHEMAS = {
 'pbip': BASE+'fabric/pbip/pbipProperties/1.0.0/schema.json',
 'pbism': BASE+'fabric/item/semanticModel/definitionProperties/1.0.0/schema.json',
 'pbir': BASE+'fabric/item/report/definitionProperties/2.0.0/schema.json',
 'report': BASE+'fabric/item/report/definition/report/1.0.0/schema.json',
 'page': BASE+'fabric/item/report/definition/page/1.0.0/schema.json',
 'pages': BASE+'fabric/item/report/definition/pagesMetadata/1.0.0/schema.json',
 'version': BASE+'fabric/item/report/definition/versionMetadata/1.0.0/schema.json',
 'visual': BASE+'fabric/item/report/definition/visualContainer/2.1.0/schema.json',
}
NAVY, BLUE, MUTED, PAPER, LINE = '#142A43', '#335D91', '#56677B', '#F8FAFC', '#D6DFE9'

def write(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False)+'\n', encoding='utf-8')

def tag(name): return str(uuid.uuid5(uuid.NAMESPACE_URL, 'devaharsha/prescription/'+name))
def lines(text): return text.strip().splitlines()

def build_model():
    measures = json.loads((ROOT/'measures.json').read_text())
    tables=[]
    specs={
      'Drug': [('DrugKey','int64',True),('Brand','string',False),('Ingredient','string',False),('Product','string',False),('Drug group','string',False)],
      'Year': [('Year','int64',False)],
      'DrugYear': [('DrugKey','int64',True),('Year','int64',True),('SpendingCents','int64',True),('Fills','int64',True)],
    }
    for table,cols in specs.items():
        columns=[]
        for name,kind,hidden in cols:
            col={'name':name,'dataType':kind,'sourceColumn':name,'summarizeBy':'none','isHidden':hidden,'lineageTag':tag(table+'/'+name)}
            if kind=='int64': col['formatString']='0'
            if (table,name) in [('Drug','DrugKey'),('Year','Year')]: col['isKey']=True
            columns.append(col)
        item={'name':table,'lineageTag':tag(table),'columns':columns,'partitions':[{'name':table,'mode':'import','source':{'type':'m','expression':lines((ROOT/'queries'/(table+'.pq')).read_text())}}]}
        if table=='DrugYear':
            item['description']='One published Overall brand/ingredient/year observation. Missing historical spending observations are excluded, never imputed.'
            item['measures']=[dict(m,lineageTag=tag('measure/'+m['name'])) for m in measures]
        tables.append(item)
    model={'name':'PrescriptionSpending','compatibilityLevel':1600,'model':{
      'culture':'en-US','sourceQueryCulture':'en-US','defaultPowerBIDataSourceVersion':'powerBI_V3',
      'dataAccessOptions':{'legacyRedirects':True,'returnErrorValuesAsNull':False},
      'tables':tables,
      'relationships':[
        {'name':tag('relationship/Drug'),'fromTable':'DrugYear','fromColumn':'DrugKey','toTable':'Drug','toColumn':'DrugKey','fromCardinality':'many','toCardinality':'one','crossFilteringBehavior':'oneDirection','isActive':True},
        {'name':tag('relationship/Year'),'fromTable':'DrugYear','fromColumn':'Year','toTable':'Year','toColumn':'Year','fromCardinality':'many','toCardinality':'one','crossFilteringBehavior':'oneDirection','isActive':True}],
      'expressions':[{'name':'CMS Overall','kind':'m','expression':lines((ROOT/'queries/CMS_Overall.pq').read_text()),'description':'Pinned June 2026 CMS release, Overall rows only. Public web source; anonymous access.'}],
      'annotations':[{'name':'PBI_QueryOrder','value':json.dumps(['CMS Overall','Drug','Year','DrugYear'])},{'name':'__PBI_TimeIntelligenceEnabled','value':'0'}]
    }}
    write(MODEL/'definition.pbism',{'$schema':SCHEMAS['pbism'],'version':'1.0','settings':{}})
    write(MODEL/'model.bim',model)
    (MODEL/'DAXQueries').mkdir(exist_ok=True)
    (MODEL/'DAXQueries/Release checks.dax').write_text((ROOT/'validation/desktop_checks.dax').read_text())
    return measures

def lit(value):
    if isinstance(value,bool): value='true' if value else 'false'
    elif isinstance(value,int): value=str(value)+'D'
    elif isinstance(value,float): value=str(value)+'D'
    else: value="'"+value.replace("'","''")+"'"
    return {'expr':{'Literal':{'Value':value}}}

def color(value): return {'solid':{'color':lit(value)}}
def obj(**properties): return [{'properties':properties}]
def field(table,name,measure=False): return {('Measure' if measure else 'Column'):{'Expression':{'SourceRef':{'Entity':table}},'Property':name}}
def projection(table,name,measure=False): return {'field':field(table,name,measure),'queryRef':table+'.'+name,'nativeQueryRef':name}
def role(*args): return {'projections':list(args)}
def measure(name): return projection('DrugYear',name,True)

def container(title=None, background='#FFFFFF'):
    result={'background':obj(show=lit(True),color=color(background),transparency=lit(0)),
            'border':obj(show=lit(True),color=color(LINE),radius=lit(4)),
            'padding':obj(top=lit(16),bottom=lit(12),left=lit(16),right=lit(16)),
            'visualHeader':obj(show=lit(False))}
    if title: result['title']=obj(show=lit(True),text=lit(title),fontColor=color(NAVY),fontSize=lit(12),fontFamily=lit('Segoe UI'),bold=lit(True),titleWrap=lit(True))
    return result

def save_visual(page,name,kind,x,y,w,h,query=None,objects=None,title=None,formatting=None):
    visual={'visualType':kind,'visualContainerObjects':formatting or container(title)}
    if query: visual['query']=query
    if objects: visual['objects']=objects
    result={'$schema':SCHEMAS['visual'],'name':name,'position':{'x':x,'y':y,'z':y*10+x,'width':w,'height':h,'tabOrder':y*10+x},'visual':visual}
    write(REPORT/'definition/pages'/page/'visuals'/name/'visual.json',result)
    return name

def textbox(page,name,text,x,y,w,h,size=12,bold=False,ink=NAVY,bg=None):
    paragraphs=[]
    for paragraph in text.split('\n'):
        paragraphs.append({'textRuns':[{'value':paragraph,'textStyle':{'fontFamily':'Segoe UI','fontSize':str(size)+'pt','color':ink,'fontWeight':'bold' if bold else 'normal'}}],'horizontalTextAlignment':'left'})
    formatting={'background':obj(show=lit(bool(bg)),color=color(bg or PAPER),transparency=lit(0)),
                'border':obj(show=lit(False)), 'padding':obj(top=lit(3),bottom=lit(3),left=lit(4),right=lit(4)), 'visualHeader':obj(show=lit(False))}
    save_visual(page,name,'textbox',x,y,w,h,objects={'general':obj(paragraphs=paragraphs)},formatting=formatting)

def card(page,name,metric,label,x,y,w=332,h=116,precision=1,units=0):
    save_visual(page,name,'card',x,y,w,h,query={'queryState':{'Values':role(measure(metric))}},
      objects={'labels':obj(color=color(NAVY),fontSize=lit(30),labelPrecision=lit(precision),labelDisplayUnits=lit(units)),
               'categoryLabels':obj(show=lit(False))},title=label)

def slicer(page,name,table,column,selected,x,y,w):
    selection={'Version':2,'From':[{'Name':'s','Entity':table,'Type':0}],
      'Where':[{'Condition':{'In':{'Expressions':[{'Column':{'Expression':{'SourceRef':{'Source':'s'}},'Property':column}}],
      'Values':[[{'Literal':{'Value':(str(selected)+'L') if isinstance(selected,int) else "'"+selected.replace("'","''")+"'"}}]]}}}]}
    save_visual(page,name,'slicer',x,y,w,100,query={'queryState':{'Values':role(projection(table,column))}},
      objects={'data':obj(mode=lit('Dropdown')),'selection':obj(singleSelect=lit(True),selectAllCheckboxEnabled=lit(False)),
               'general':obj(filter={'filter':selection}),'header':obj(show=lit(False)),'items':obj(fontSize=lit(11),fontColor=color(NAVY))},title=column)
    return name

def bar_chart(page,name,title,category,metric,x,y,w,h,horizontal=False,sort_measure=False):
    p=projection(*category)
    q={'queryState':{'Category':role(p),'Y':role(measure(metric))},'sortDefinition':{'sort':[{'field':field('DrugYear',metric,True) if sort_measure else p['field'],'direction':'Descending' if sort_measure else 'Ascending'}]}}
    save_visual(page,name,'clusteredBarChart' if horizontal else 'clusteredColumnChart',x,y,w,h,query=q,
      objects={'dataPoint':obj(defaultColor=color(BLUE)),'categoryAxis':obj(show=lit(True),showAxisTitle=lit(False),fontSize=lit(10),fontFamily=lit('Segoe UI'),axisType=lit('Categorical')),
               'valueAxis':obj(show=lit(True),showAxisTitle=lit(False),fontSize=lit(10)),'legend':obj(show=lit(False)),
               'labels':obj(show=lit(True),fontSize=lit(10),color=color(NAVY),labelPrecision=lit(1))},title=title)

def table(page,name,title,projections,x,y,w,h):
    save_visual(page,name,'tableEx',x,y,w,h,query={'queryState':{'Values':role(*projections)}},
      objects={'grid':obj(gridVertical=lit(False),gridHorizontal=lit(True),rowPadding=lit(9)),
               'columnHeaders':obj(fontColor=color(NAVY),backColor=color('#EEF3F9'),fontSize=lit(11),wordWrap=lit(True)),
               'values':obj(fontColor=color(NAVY),fontSize=lit(11)), 'total':obj(totals=lit(False))},title=title)

def page_def(name,title,interactions=None):
    d={'$schema':SCHEMAS['page'],'name':name,'displayName':title,'displayOption':'FitToPage','width':1440,'height':900,
       'objects':{'background':obj(color=color(PAPER),transparency=lit(0))}}
    if interactions: d['visualInteractions']=interactions
    write(REPORT/'definition/pages'/name/'page.json',d)

def footer(page):
    textbox(page,'source_footer','CMS June 25, 2026 release  |  2020–2024 observations  |  Gross spending before rebates  |  Devaharsha Gubbala',32,859,1376,26,10,ink=MUTED)

def build_report():
    write(ROOT/'PrescriptionSpending.pbip',{'$schema':SCHEMAS['pbip'],'version':'1.0','artifacts':[{'report':{'path':'PrescriptionSpending.Report'}}],'settings':{'enableAutoRecovery':True}})
    write(REPORT/'definition.pbir',{'$schema':SCHEMAS['pbir'],'version':'4.0','datasetReference':{'byPath':{'path':'../PrescriptionSpending.SemanticModel'}}})
    write(REPORT/'definition/version.json',{'$schema':SCHEMAS['version'],'version':'4.0.0'})
    write(REPORT/'definition/report.json',{'$schema':SCHEMAS['report'],'layoutOptimization':'None',
      'themeCollection':{'baseTheme':{'name':'CY23SU04','reportVersionAtImport':'5.43','type':'SharedResources'}},
      'resourcePackages':[{'name':'SharedResources','type':'SharedResources','items':[{'name':'CY23SU04','path':'BaseThemes/CY23SU04.json','type':'BaseTheme'}]}],
      'settings':{'useStylableVisualContainerHeader':True,'exportDataMode':'AllowSummarized','defaultDrillFilterOtherVisuals':True},
      'annotations':[{'name':'author','value':'Devaharsha Gubbala; developed with AI assistance'},{'name':'validation','value':'Source controls and file schemas checked; Power BI Desktop refresh and rendering require verification.'}]})
    write(REPORT/'definition/pages/pages.json',{'$schema':SCHEMAS['pages'],'pageOrder':['overview','drivers','definitions'],'activePageName':'overview'})

    p='overview'
    page_def(p,'01  Spending overview',[{'source':'year_filter','target':'history','type':'NoFilter'}])
    textbox(p,'title','Prescription spending, in context.',32,25,905,56,27,True)
    textbox(p,'subtitle','Start with the concentration of gross spending. Then inspect the volume behind it.',32,82,905,46,12,ink=MUTED)
    slicer(p,'year_filter','Year','Year',2024,966,24,150)
    slicer(p,'group_filter','Drug','Drug group','GLP-1 / GIP',1132,24,276)
    for i,(m,t,prec) in enumerate([('Total spending','Reported gross spending',2),('Prescription fills','Prescription fills',1),('Average spending per fill','Average spending / fill',2),('Share of listed spending','Share of all listed spending',1)]):
        card(p,'kpi_'+str(i),m,t,32+i*348,148,precision=prec,units=1 if i>=2 else 0)
    bar_chart(p,'ranking','Leading products · up to 10 spending ranks',('Drug','Product'),'Leading product spending',32,288,760,386,True,True)
    bar_chart(p,'history','Five-year history · selected drug group',('Year','Year'),'Total spending',816,288,592,386)
    textbox(p,'history_note','Year selection updates the cards and ranking. The history chart keeps all five years; drug-group selection applies to both.',816,683,592,70,11,ink=MUTED)
    textbox(p,'finding','2024 finding: Ozempic represents 47.1% of the selected GLP-1 / GIP cohort’s spending.\nBudget implication: review volume alongside average spending per fill. The Growth & drivers page separates those components.',32,702,760,135,12,bg='#EEF3F9')
    textbox(p,'scope_note','Coverage: the products listed in this release. Historical totals are not a complete historical market census. Average spending per fill is not a standardized price.',816,766,592,74,11,ink=MUTED)
    footer(p)

    p='drivers'
    page_def(p,'02  Growth & drivers',[{'source':'year_filter','target':'spending_history','type':'NoFilter'},{'source':'year_filter','target':'fill_history','type':'NoFilter'}])
    textbox(p,'title','What changed—and what explains it?',32,25,820,58,26,True)
    textbox(p,'subtitle','Choose one drug and one comparison year. Missing history leaves the comparison blank.',32,84,820,44,12,ink=MUTED)
    slicer(p,'year_filter','Year','Year',2024,866,24,150)
    slicer(p,'drug_filter','Drug','Product','Ozempic (Semaglutide)',1032,24,376)
    for i,(m,t,prec) in enumerate([('Spending YoY','Gross spending · year over year',1),('Fills YoY','Prescription fills · year over year',1),('Average per fill YoY','Average / fill · year over year',1),('Prior-year fills','Prior-year prescription fills',0)]):
        card(p,'kpi_'+str(i),m,t,32+i*348,148,precision=prec,units=1)
    bar_chart(p,'spending_history','Gross spending · all available years',('Year','Year'),'Total spending',32,288,676,286)
    bar_chart(p,'fill_history','Prescription fills · all available years',('Year','Year'),'Prescription fills',732,288,676,286)
    table(p,'bridge','Spending-change bridge · volume first, then average spending',[
      measure('Fill-volume component'),measure('Average-spend component'),measure('Spending change'),measure('Bridge residual')],32,598,1376,145)
    save_visual(p,'comparison_context','card',32,764,1376,66,query={'queryState':{'Values':role(measure('Comparison context'))}},
      objects={'labels':obj(fontSize=lit(12),color=color(MUTED)),'categoryLabels':obj(show=lit(False))},formatting=container(background=PAPER))
    footer(p)

    p='definitions'
    page_def(p,'03  Definitions & checks')
    textbox(p,'title','Definitions are part of the analysis.',32,25,1376,59,27,True)
    textbox(p,'subtitle','Refresh the public CMS release, inspect the model, and compare the results with independent source controls.',32,87,1376,41,12,ink=MUTED)
    card(p,'release_products','Release products','Listed products · 2024',32,148,332,116,0,1)
    card(p,'release_rows','Release observations','Available drug-year rows',380,148,332,116,0,1)
    save_visual(p,'release_check','card',728,148,680,116,query={'queryState':{'Values':role(measure('Release reconciliation'))}},
      objects={'labels':obj(fontSize=lit(19),color=color(NAVY)),'categoryLabels':obj(show=lit(False))},title='2024 source-control check')
    textbox(p,'model_title','The model',32,292,665,38,18,True)
    textbox(p,'model_description','Drug: one row per brand + ingredient.\nYear: one row for each observation year, 2020–2024.\nDrugYear: one row per available product + year.\n\nDrug and Year each filter DrugYear through a one-to-many, single-direction relationship. Counts and spending are calculated from the fact table.',32,344,660,246,13,bg='#EEF3F9')
    textbox(p,'rules_title','The rules behind the numbers',744,292,664,38,18,True)
    textbox(p,'rules_description','• Keep Overall rows; exclude manufacturer-detail duplicates.\n• Preserve unavailable history; a blank does not mean zero.\n• Gross spending excludes manufacturer rebates.\n• Beneficiaries overlap across drugs and are not added together.\n• Average spending per fill reflects supply and mix.\n• Medicare results do not estimate an employer’s costs.',744,344,664,246,13,bg='#EEF3F9')
    textbox(p,'check_heading','A useful next question',32,618,1376,36,18,True)
    textbox(p,'next_question','How much of the observed change remains after accounting for days supplied, product mix, and net cost after rebates? That requires additional data. This report describes public spending; its arithmetic bridge does not establish a causal price effect or treatment value.',32,667,1376,104,13)
    textbox(p,'checks_instruction','For exact checks: open DAX query view → Release checks, run the query, and compare Actual with Expected. Setup steps, measure definitions, and the model diagram are included in the powerbi folder.',32,790,1376,49,11,ink=MUTED)
    footer(p)

def main():
    build_model()
    build_report()
    print('Built model, three report pages, and',len(list(REPORT.glob('definition/pages/*/visuals/*/visual.json'))),'native visuals.')

if __name__=='__main__': main()
