import json, sys
h=open('christina.html').read()
data=open('app_data.json').read().replace('</','<\\/')
def rep(a,b,count=1):
    global h
    assert a in h, 'MISSING: '+a[:80]
    h=h.replace(a,b,count)
rep('<title>Healthy Places — intervention pathways</title>','<title>Healthy Places — indoor air evidence pathways</title>\n<link rel="preconnect" href="https://fonts.googleapis.com"><link href="https://fonts.googleapis.com/css2?family=Work+Sans:wght@400;500;600;700;800;900&display=swap" rel="stylesheet">')
rep('</style></head>', open('graph.css').read()+'</style></head>')
rep('<span class="tag">Evidence pathways · concept</span>','<span class="tag">Evidence pathways · System Public Graph data</span>')
rep('<div class="sim"><b>Illustrative design only.</b> All line colours and weights below are invented examples, not assessed findings or priorities. No evidence has been ranked in this mockup.</div>',
    '<div class="sim"><b>Real data.</b> Bars show study counts from the curated System Public Graph v2.1: blue = studies linking the exposure each action reduces to health; black = studies testing the action itself. Counts measure evidence volume, not effect size.</div>')
rep('data-setting="Office" aria-pressed="false">▤ &nbsp; Office</button>','data-setting="Workplace" aria-pressed="false">▤ &nbsp; Workplace</button>')
rep('<div class="front-foot">Health · equity · wider outcomes</div>','<div class="front-foot">Health · equity · wider outcomes</div>${window.HP_cardBars?window.HP_cardBars(i):""}')
rep('aria-haspopup="dialog">Open systems map ↗</button>','>Open evidence graph ↓</button>')
rep('if(map)openMap(Number(map.dataset.map));','if(map)window.HP_selectAction(Number(map.dataset.map));')
rep('<p class="foot">Concept only · Not connected to the System Public Graph or external datasets · No intervention outcomes or combined effects have been assessed.</p>',
    open('graph_section.html').read()+'<p class="foot">Single-action pathways use real counts from the System Public Graph v2.1 and cited reports. The joint package map is still an illustrative concept: no combined effects have been assessed.</p>')
pre='''<script>window.HP_DATA='''+data+''';
window.HP_cardBars=function(i){var it=window.HP_DATA.interventions[i];if(!it)return "";var mh=Math.max.apply(null,window.HP_DATA.interventions.map(function(x){return x.harm_total})),md=Math.max.apply(null,window.HP_DATA.interventions.map(function(x){return x.direct}));
function r(lbl,n,m,c){return '<div class="row"><span class="trk"><span class="fill" style="width:'+(m?n/m*100:0)+'%;background:'+c+'"></span></span><span>'+n+' '+lbl+'</span></div>';}
return '<div class="cardbars">'+r('via exposure',it.harm_total,mh,'#36c9ff')+r('direct tests',it.direct,md,'#111')+'</div>';};</script>
'''
rep('<script>\nconst data=[', pre+'<script>\nconst data=[')
rep('</script></body></html>', '</script>\n<script>'+open('graph.js').read()+'</script></body></html>')
open(sys.argv[1],'w').write(h); print('ok', len(h))
