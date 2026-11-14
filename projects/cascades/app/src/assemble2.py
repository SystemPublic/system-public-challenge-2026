import sys, os
h=open('christina.html').read()
data=open('app_data.json').read().replace('</','<\\/')
def rep(a,b):
    global h
    assert a in h, 'MISSING: '+a[:90]; h=h.replace(a,b,1)
rep('<title>Healthy Places — intervention pathways</title>','<title>Airways for Impact — indoor air evidence pathways</title>\n<link rel="preconnect" href="https://fonts.googleapis.com"><link href="https://fonts.googleapis.com/css2?family=Work+Sans:wght@400;500;600;700;800;900&display=swap" rel="stylesheet">')
rep('</style></head>', open('graph.css').read()+'.back{display:inline-block;margin:18px 0 0;font-weight:800;color:#111}.pkgnote{background:#fff8d2;border:1px solid #c8ba55;padding:10px 13px;font-size:13px;margin-top:12px}</style></head>')
head=h[:h.index('<body>')]
rep('<span class="mark">✳</span> Healthy Places</div><span class="tag">Evidence pathways · concept</span>','<span class="mark">✳</span> Airways for Impact</div><span class="tag">Evidence pathways · System Public Graph data</span>')
topbar=h[h.index('<header class="top">'):h.index('</header>')+9]
rep('<div class="mini-legend" aria-label="Legend">','<div class="card-legend" aria-label="Legend" style="display:flex;flex-wrap:wrap;gap:8px 17px;border-top:1px solid #edf1ed;margin-top:17px;padding-top:15px;font-size:12px;color:#111"><b>How to read the cards</b><span><b>Problem evidence</b> = studies linking the exposure the action reduces to health</span><span><b>Fix evidence</b> = studies testing the action itself</span><span><b>Strong</b> = 20+ problem studies (or 5+ fix trials) and most significant · <b>Moderate</b> = 5+ studies, ≥40% significant · <b>Limited</b> = fewer · associations, not proof of cause</span></div><div hidden class="old-legend">')
rep('<div class="sim"><b>Illustrative design only.</b> All line colours and weights below are invented examples, not assessed findings or priorities. No evidence has been ranked in this mockup.</div>',
    '')
rep('<section class="pack" id="package">','<section class="pack" id="package" hidden style="display:none">')
rep('<button class="btn" id="review" type="button">Review package · 0 ↓</button>','<span style="display:flex;gap:8px;flex-wrap:wrap"><button class="btn" id="review" type="button" disabled>Review package · 0 ↗</button><button class="btn" id="clear2" type="button">Clear</button></span>')
rep("document.getElementById('review').textContent=`Review package · ${states.selected.size} ↓`;","document.getElementById('review').textContent=`Review package · ${states.selected.size} ↗`;document.getElementById('review').disabled=states.selected.size<1;")
rep("document.getElementById('clear').addEventListener('click',","document.getElementById('clear2').addEventListener('click',()=>document.getElementById('clear').click());document.getElementById('clear').addEventListener('click',")
# settings
rep('<div class="choices" role="group" aria-label="Setting"><button class="choice" data-setting="Home" aria-pressed="true">','<div class="choices" role="group" aria-label="Setting"><button class="choice" data-setting="All" aria-pressed="true">◎ &nbsp; All settings</button><button class="choice" data-setting="Home" aria-pressed="false">')
rep('data-setting="Office" aria-pressed="false">▤ &nbsp; Office</button>','data-setting="Workplace" aria-pressed="false">▤ &nbsp; Workplace</button>')
rep('In this preview, the selector does not filter data.','Filters the card evidence bars by where studies took place. 37.5% of studies do not say, so they only count under All settings.')
rep("const states={open:0,selected:new Set(),setting:'Home'};","const states={open:0,selected:new Set(),setting:'All'};")
rep('<span id="setting-label">Home</span>','<span id="setting-label">All settings</span>')
rep("document.getElementById('announcement').textContent=states.setting+' selected. Examples remain illustrative.';","document.getElementById('announcement').textContent=states.setting+' selected. Card bars updated.';render();")
# cards
rep("<span class=\"number\">${String(i+1).padStart(2,'0')} / INTERVENTION</span>","<span class=\"number\">${String(i+1).padStart(2,'0')} · ${window.HP_expLabel(i)}</span>")
rep('<div class="front-foot">Health · equity · wider outcomes</div>','<div class="front-foot">${window.HP_verdict(i)}</div>${window.HP_cardBars(i,states.setting)}')
rep('aria-haspopup="dialog">Open systems map ↗</button>','>Open evidence graph ↗</button>')
rep('if(map)openMap(Number(map.dataset.map));','if(map)window.HP_selectAction(Number(map.dataset.map));')
# package
rep("document.getElementById('review').addEventListener('click',()=>document.getElementById('package').scrollIntoView({behavior:'smooth'}));",
    "document.getElementById('review').addEventListener('click',()=>{if(states.selected.size)window.HP_openPackage([...states.selected].sort((a,b)=>a-b));else document.getElementById('package').scrollIntoView({behavior:'smooth'});});")
rep("document.getElementById('open-package').addEventListener('click',openPackage);","document.getElementById('open-package').addEventListener('click',()=>window.HP_openPackage([...states.selected].sort((a,b)=>a-b)));")
rep('aria-haspopup="dialog" disabled>Open joint systems map ↗</button>','disabled>Open package evidence graph ↗</button>')
rep("document.getElementById('open-package').disabled=states.selected.size<2;","document.getElementById('open-package').disabled=states.selected.size<1;")
rep('<p class="foot">Concept only · Not connected to the System Public Graph or external datasets · No intervention outcomes or combined effects have been assessed.</p>',
    '<p class="foot">Built on the System Public Graph v2.1 and cited reports. No combined effects of packages have been assessed.</p>')
def homesec():
    s=open('graph_section.html').read().replace('03 / Evidence graph · real data','02 / Overview · all actions')
    i=s.index('<div class="gctl">'); j=s.index('<div id="gpick"')
    block=s[i:j]; assert block.endswith('</div></div>\n')
    segs=block[len('<div class="gctl">'):-len('</div></div>\n')]
    row='<div class="gctl" style="justify-content:space-between;width:100%;margin:12px 0 14px">'+segs+'</div>\n'
    return s[:i]+'</div>\n'+row+s[j:]
rep('</div></div></main><div id="announcement"','</div></div>'+homesec()+'</main><div id="announcement"')
pre='''<script>window.HP_DATA='''+data+''';
(function(){var D=window.HP_DATA.interventions;
window.HP_expLabel=function(i){return D[i]?'REDUCES '+D[i].exposure.toUpperCase():'';};
window.HP_verdict=function(i){return '';};
window.HP_cardBars=function(i,setting){var it=D[i];if(!it)return "";var key=(setting||'All').toLowerCase(),all=key==='all',L={None:0,Limited:1,Moderate:2,Strong:3};
 var mxP=Math.max.apply(null,D.map(function(d){return d.strength.p.studies})),mxF=Math.max.apply(null,D.map(function(d){return d.strength.f.studies}));
 function sig(s){if(!s.studies)return 'none found';if(s.studies<5)return 'too few studies to judge';if(s.pct_sig==null)return 'no CI or p-value';return Math.round(s.studies*s.pct_sig/100)+' significant ('+s.pct_sig+'%)';}
 function block(lbl,s,n,mx,col,light,sub2){var lv=L[s.level]||0,seg='';for(var j=0;j<3;j++)seg+='<span class="cb-seg" style="background:'+(j<lv?col:'#eee')+'"></span>';
  var w=mx?n/mx*100:0,sg=all&&s.studies>=5?Math.round(s.studies*(s.pct_sig||0)/100):0,ws=n?sg/n*w:0;
  return '<div class="cb"><div class="cb-h"><span>'+lbl+' evidence</span><span>'+s.level+(all?'':' overall')+'</span></div><div class="cb-m">'+seg+'</div>'+
   '<div class="cb-q"><span class="cb-qh" style="width:'+w+'%;background:repeating-linear-gradient(135deg,'+light+' 0 4px,#fff 4px 7px)"></span><span class="cb-qs" style="width:'+ws+'%;background:'+col+'"></span></div>'+
   '<div class="cb-l">'+n+' '+lbl.toLowerCase()+' stud'+(n===1?'y':'ies')+(all?'':' in '+key+' settings <span class="cb-of">(of '+s.studies+')</span>')+'</div><div class="cb-l2">'+(all?sig(s):'significance shown under All settings')+'</div>'+(sub2||'')+'</div>';}
 var p=it.strength.p,f=it.strength.f,pn=all?p.studies:(it.settings[key]||0),fn=all?f.studies:(it.int_settings[key]||0);
 var tr=f.trials?f.trials+' trial'+(f.trials===1?'':'s'):'no trials';
 var out='';
 return '<div class="cardbars">'+block('Problem',p,pn,mxP,'#36c9ff','#a6e6ff','')+block('Fix',f,fn,mxF,'#111','#9a9a9a','<div class="cb-l2">'+tr+'</div>'+out)+'</div>';};
})();</script>
'''
rep('<script>\nconst data=[', pre+'<script>\nconst data=[')
gjs=open('graph.js').read()
rep('</script></body></html>', '</script>\n<script>'+gjs+'</script></body></html>')

TXT=[('the exposure the action reduces','the exposure the intervention reduces'),('studies testing the action','studies testing the intervention'),
 ('actions selected','interventions selected'),('Matched to this action','Matched to this intervention'),('of 8 actions have evidence','of 8 interventions have evidence'),
 ('studies test the action on this outcome','studies test the intervention on this outcome'),('Overview · all actions','Overview · all interventions'),
 ('explore actions together','explore interventions together'),('Choose an action','Choose an intervention'),('Compare possible actions','Compare possible interventions'),
 ('for the selected action','for the selected intervention'),('no evidence found for this action','no evidence found for this intervention'),
 ('Pick an action. Lines run to its wider outcomes (above)','Pick an intervention. Lines run to its co-benefits and costs (above)'),
 ('Selected action','Selected intervention'),('measured effect of the action','measured effect of the intervention'),('compare all selected actions','compare all selected interventions'),
 ('evidence for one action','evidence for one intervention'),('Action evidence graph','Intervention evidence graph'),('← All actions','← All interventions')]
def fixtxt(s):
    for x,y in TXT: s=s.replace(x,y)
    return s
h=fixtxt(h)
out=sys.argv[1]; os.makedirs(out,exist_ok=True)
open(os.path.join(out,'index.html'),'w').write(h)
# ---- graph.html: one action or a package ----
sec=open('graph_section.html').read()
g=head+'''<body>
'''+topbar+'''
<main class="shell main"><a class="back" href="index.html">← All actions</a>
<div id="pkg"></div>
'''+sec+'''<p class="foot">Built on the System Public Graph v2.1 and cited reports.</p></main>
<script>window.HP_DATA='''+data+''';
(function(){var D=window.HP_DATA.interventions,Q=new URLSearchParams(location.search),a=(Q.get('a')||'').split(',').filter(function(x){return x!==''}).map(Number).filter(function(n){return n>=0&&n<D.length});
var t=document.getElementById('graph-title'),n=a.map(function(i){return D[i].name});
if(a.length===1){t.textContent=n[0];document.title=n[0]+' — Airways for Impact';}
else if(a.length>1){t.textContent='Package: '+n.join(' + ');document.title='Package — Airways for Impact';
 document.getElementById('pkg').innerHTML='<div class="pkgnote"><b>Package view.</b> Each line is evidence for one action. Combined effects and interactions have not been assessed; counts cannot be added to estimate a joint effect.</div>';}
document.querySelector('#graph .eyebrow').textContent=a.length>1?'Package evidence graph · real data':'Action evidence graph · real data';})();</script>
<script>'''+gjs+'''</script></body></html>'''
g=fixtxt(g)
open(os.path.join(out,'graph.html'),'w').write(g)
print('ok', len(h), len(g))
