(function(){
const D=window.HP_DATA, INTS=D.interventions, CR=D.crowding, HL=D.health, CB=D.cob;
const COL={benefit:'#57ef8a',mixed:'#ff9c36',harm:'#ff43bd',unknown:'#bcbcbc',health:'#36c9ff'};
const DASH={benefit:'',mixed:'9 4',harm:'2 5',unknown:'7 6'};
const LV={None:0,Limited:1,Moderate:2,Strong:3};
const Q=new URLSearchParams(location.search);const ONLY=(Q.get('a')||'').split(',').filter(x=>x!=='').map(Number).filter(n=>n>=0&&n<INTS.length);
const VIS=ONLY.length?ONLY:INTS.map((_,i)=>i);const SHOWCR=!ONLY.length||ONLY.some(i=>CR.worsens.includes(INTS[i].key));
const MEAS={};const st={sel:ONLY.length?ONLY[0]:0,layout:'rows',region:'all',edge:null};
const isSel=i=>ONLY.length>1?ONLY.includes(i):i===st.sel;
const esc=s=>String(s==null?'':s).replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;');
const uk=()=>st.region==='uk';
const ITEM=i=>i===8?CR:INTS[i];
const P_=it=>it.strength?it.strength.p:{studies:0,pct_sig:null,trials:0,level:'None'};
const F_=it=>it.strength?it.strength.f:{studies:0,pct_sig:null,trials:0,level:'None'};
const edgeP=(it,k)=>uk()?{studies:it.health[k].harm_uk,pct_sig:null,consistency:'untestable',trials:0,effect_size:0,group_comparison:0,findings:0}:it.health[k].ps;
const edgeF=(it,k)=>uk()?{studies:it.health[k].direct_uk,pct_sig:null}:it.health[k].fs;
const lw=n=>n?Math.min(14,1.5+n/8):1;
function cons(pct){if(pct==null)return['','untestable'];if(pct>=60)return['','consistent'];if(pct>=40)return['9 5','mixed'];return['2 5','mostly null'];}
function sigtxt(s){return s.studies<5?'too few to judge':(s.pct_sig==null?'no CI or p-value':`${Math.round(s.studies*s.pct_sig/100)} significant (${s.pct_sig}%)`);}
function meter(lbl,s,col){const lv=LV[s.level]||0,lt=uk()?s.level+' overall':s.level;let seg='';for(let j=0;j<3;j++)seg+=`<span class="seg" style="background:${j<lv?col:'#eee'}"></span>`;return `<div class="mt"><div class="mh"><span>${lbl}</span><span>${lt}</span></div><div class="ms">${seg}</div></div>`;}
function qbar(s,mx,col,light,lbl){const n=s.studies||0,pct=s.pct_sig,sig=Math.round(n*(pct||0)/100),w=mx?n/mx*100:0,ws=n?sig/n*w:0;
  return `<div class="qb"><div class="qt"><span class="qh" style="width:${w}%;background:repeating-linear-gradient(135deg,${light} 0 4px,#fff 4px 7px)"></span><span class="qs" style="width:${n>=5?ws:0}%;background:${col}"></span></div><div class="ql">${n} ${lbl} ${n===1?'study':'studies'}</div><div class="ql2">${n?sigtxt(s):'none found'}</div></div>`;}
function fo(x,y,w,h,html,cls,attrs){return `<foreignObject x="${x}" y="${y}" width="${w}" height="${h}" ${attrs||''}><div xmlns="http://www.w3.org/1999/xhtml" class="gn ${cls||''}" style="width:${w}px;min-height:${h}px" data-grp="${(cls||'').split(' ')[0]}">${html}</div></foreignObject>`;}
function curve(x1,y1,x2,y2,col,op,w,dash,vert,id){const d=vert?`M${x1} ${y1} C${x1} ${(y1+y2)/2} ${x2} ${(y1+y2)/2} ${x2} ${y2}`:`M${x1} ${y1} C${(x1+x2)/2} ${y1} ${(x1+x2)/2} ${y2} ${x2} ${y2}`;const da=dash?`stroke-dasharray="${dash}"`:'';
  return `<path d="${d}" fill="none" stroke="#111" stroke-opacity="${op}" stroke-width="${w+2}" ${da}/><path d="${d}" fill="none" stroke="${col}" stroke-opacity="${op}" stroke-width="${w}" ${da}/>`+(id?`<path class="hit" d="${d}" data-edge="${id}" tabindex="0" role="button" aria-label="Inspect link"/>`:'');}
function badge(x,y,t){const w=14+String(t).length*6.8;return `<rect x="${x-w/2}" y="${y-11}" width="${w}" height="22" fill="#fff" stroke="#111"/><text x="${x}" y="${y+4}" text-anchor="middle" font-size="12" font-weight="800">${esc(t)}</text>`;}
function draw(){
  const rows=st.layout==='rows', sel=INTS[st.sel];
  const slots=VIS.concat(SHOWCR?[8]:[]);
  const maxP=Math.max(...INTS.concat([CR]).map(it=>uk()?it.exp_uk:P_(it).studies),1), maxF=Math.max(...INTS.map(it=>uk()?it.direct_uk:F_(it).studies),1);
  const fk=ONLY.length>1?ONLY:[st.sel];
  const hv=k=>fk.reduce((a,i)=>a+(edgeP(INTS[i],HL[k].key).studies||0),0), maxHv=Math.max(...HL.map((h,k)=>hv(k)),1);
  let W,Hh,P={};
  const n=slots.length;
  const sig=st.layout+n+st.region,HO=MEAS[sig]||{};
  if(rows){W=1340;const iw=n<=3?300:(n<=5?230:Math.floor((W-(n-1)*12)/n)),ih=HO.int||(n<=3?250:300),ch=HO.cob||96,hh=HO.hl||150;Hh=ch+30+200+ih+120+hh;
    const xs=(m,w)=>m===1?[(W-w)/2]:Array.from({length:m},(_,i)=>i*(w+(W-m*w)/(m-1)));
    const cw=Math.floor((W-5*20)/6),hw=Math.floor((W-6*20)/7),iy=30+ch+200;P.cob=xs(6,cw).map(x=>({x,y:30,w:cw,h:ch}));P.int=[];xs(n,iw).forEach((x,s)=>P.int[slots[s]]={x,y:iy,w:iw,h:ih});P.hl=xs(7,hw).map(x=>({x,y:iy+ih+120,w:hw,h:hh}));}
  else{W=1300;const ih=HO.int||210,gap=24;Hh=Math.max(40+n*(ih+gap),40+7*170,40+6*130)+20;
    const ys=(m,h,top,bot)=>m===1?[(top+bot-h)/2]:Array.from({length:m},(_,i)=>top+i*((bot-top-h)/(m-1)));
    const ch=HO.cob||110,hh=HO.hl||150;Hh=Math.max(40+n*(ih+gap),40+7*(hh+20),40+6*(ch+20))+20;P.cob=ys(6,ch,40,Hh-20).map(y=>({x:0,y,w:250,h:ch}));P.int=[];ys(n,ih,40,Hh-20).forEach((y,s)=>P.int[slots[s]]={x:500,y,w:320,h:ih});P.hl=ys(7,hh,40,Hh-20).map(y=>({x:1070,y,w:230,h:hh}));}
  const top=p=>rows?[p.x+p.w/2,p.y]:[p.x,p.y+p.h/2], bot=p=>rows?[p.x+p.w/2,p.y+p.h]:[p.x+p.w,p.y+p.h/2];
  const cobEnd=p=>rows?[p.x+p.w/2,p.y+p.h]:[p.x+p.w,p.y+p.h/2], hlEnd=p=>rows?[p.x+p.w/2,p.y]:[p.x,p.y+p.h/2];
  let E='',B='',N='';
  const have=new Set();fk.forEach(i=>INTS[i].cob.forEach(c=>have.add(c.g)));
  if(fk.length===1)CB.forEach((g,j)=>{if(!have.has(j)){const a=top(P.int[st.sel]),b=cobEnd(P.cob[j]);E+=curve(a[0],a[1],b[0],b[1],COL.unknown,.9,2,DASH.unknown,rows,`cob:${st.sel}:${j}:na`);}});
  VIS.forEach(i=>INTS[i].cob.forEach((c,ci)=>{const s=isSel(i),a=top(P.int[i]),b=cobEnd(P.cob[c.g]);E+=curve(a[0],a[1],b[0],b[1],COL[c.type],s?1:.12,c.w==='W2'?4.5:2.5,DASH[c.type],rows,s?`cob:${i}:${c.g}:${ci}`:null);}));
  slots.forEach(i=>{const it=ITEM(i);HL.forEach((h,k)=>{const e=edgeP(it,h.key),v=e.studies;if(!v)return;const s=isSel(i)||(ONLY.length>1&&i===8);
    const a=bot(P.int[i]),b=hlEnd(P.hl[k]),c=cons(e.pct_sig);E+=curve(a[0],a[1],b[0],b[1],i===8?COL.harm:COL.health,s?1:.1,lw(v),c[0],rows,s?`hl:${i}:${k}`:null);
});});
  if(SHOWCR)CR.worsens.forEach(key=>{const t=INTS.findIndex(x=>x.key===key);if(!slots.includes(t))return;const a=P.int[8],b=P.int[t];
    E+=rows?`<path d="M${a.x+a.w/2} ${a.y} C${a.x+a.w/2} ${a.y-70} ${b.x+b.w/2} ${b.y-70} ${b.x+b.w/2} ${b.y}" fill="none" stroke="#ff43bd" stroke-width="2.5" stroke-dasharray="2 5"/>`:`<path d="M${a.x} ${a.y+30} C${a.x-46} ${a.y+30} ${b.x-46} ${b.y+30} ${b.x} ${b.y+30}" fill="none" stroke="#ff43bd" stroke-width="2.5" stroke-dasharray="2 5"/>`;});
  CB.forEach((g,j)=>{const p=P.cob[j],hit=have.has(j);N+=fo(p.x,p.y,p.w,p.h,`<div class="gt">${esc(g.name)}</div><div class="gs">${g.n} of 8 actions have evidence</div><div class="gs2">${hit?'Evidence for the selected action':'Not assessed for the selected action'}</div>`,'cob'+(hit?' on':''));});
  slots.forEach(i=>{const it=ITEM(i),p=P.int[i],s=isSel(i),cr=i===8;
    const pS=uk()?{studies:it.exp_uk,pct_sig:null,level:P_(it).level}:P_(it), fS=uk()?{studies:it.direct_uk,pct_sig:null,level:F_(it).level}:F_(it);
    const body=`<div class="gt">${esc(it.name)}</div><div class="gs">${cr?'exposure only · makes damp &amp; stale air worse':'reduces '+esc(it.exposure)}</div>`+
      meter('Problem',pS,cr?'#ff43bd':'#36c9ff')+qbar(pS,maxP,cr?'#ff43bd':'#36c9ff',cr?'#ffb3e3':'#a6e6ff','problem')+
      (cr?'':meter('Fix',fS,'#111')+qbar(fS,maxF,'#111','#9a9a9a','fix'));
    N+=fo(p.x,p.y,p.w,p.h,body,'int'+(s?' sel':'')+(cr?' cr':''),cr?'':`data-kind="int" data-i="${i}" tabindex="0" role="button" aria-label="${esc(it.name)}"`);});
  HL.forEach((h,k)=>{const p=P.hl[k],v=hv(k);let e;if(fk.length===1)e=edgeP(sel,h.key);else{const sg=fk.reduce((a,i)=>{const x=edgeP(INTS[i],h.key);return a+(x.pct_sig!=null?Math.round((x.studies||0)*x.pct_sig/100):0);},0);e={studies:v,pct_sig:uk()||!v?null:Math.round(sg/v*100)};}const f=fk.reduce((a,i)=>a+(edgeF(INTS[i],h.key).studies||0),0);
    N+=fo(p.x,p.y,p.w,p.h,`<div class="gt">${esc(h.name)}</div>`+(v?qbar(e,maxHv,'#36c9ff','#a6e6ff','problem'):'<div class="gs">No study found</div>')+`<div class="gs2">${f} fix ${f===1?'study':'studies'}</div>`,'hl'+(v?' on':''));});
  const hd=rows?[[0,18,'CO-BENEFITS & COST'],[0,P.int[slots[0]].y-14,'INTERVENTIONS'],[0,P.hl[0].y-14,'HEALTH']]:[[0,26,'CO-BENEFITS & COST'],[500,26,'INTERVENTIONS'],[1070,26,'HEALTH']];
  const svg=document.getElementById('gsvg');svg.classList.toggle('multi',n>1);svg.setAttribute('viewBox',`-6 -6 ${W+12} ${Hh+12}`);svg.style.minWidth=Math.min(W,1000)+'px';
  svg.innerHTML=E+N+B+hd.map(h=>`<text x="${h[0]}" y="${h[1]}" font-size="13" font-weight="800" letter-spacing="1" fill="#111" stroke="#fff" stroke-width="5" paint-order="stroke" stroke-linejoin="round">${h[2]}</text>`).join('');
  document.querySelectorAll('#gpick button').forEach(b=>b.setAttribute('aria-pressed',String(+b.dataset.pick===st.sel)));
  const m={};svg.querySelectorAll('.gn[data-grp]').forEach(d=>{d.style.minHeight='0';const g=d.dataset.grp,v=Math.ceil(d.scrollHeight)+2;m[g]=Math.max(m[g]||0,v);});
  const cur={cob:rows?(HO.cob||96):(HO.cob||110),int:HO.int||(rows?(n<=3?250:300):210),hl:HO.hl||150};
  if(!MEAS[sig]&&(m.cob!==cur.cob||m.int!==cur.int||m.hl!==cur.hl)){MEAS[sig]={cob:m.cob||cur.cob,int:m.int||cur.int,hl:m.hl||cur.hl};return draw();}
  svg.querySelectorAll('.gn[data-grp]').forEach(d=>{d.style.minHeight=d.parentNode.getAttribute('height')+'px';});
  inspect(st.edge||`hl:${st.sel}:${bestHealth(sel)}`);
  const unk=(sel.regions['Unknown']||0);
  document.getElementById('gfoot').textContent=`${D.meta.studies} curated studies · ${D.meta.uk_pct}% UK · ${D.meta.unknown_country_pct}% country not recorded (counted in “All regions”, excluded from “UK only”) · ${sel.name}: ${unk} of ${sel.exp_studies} exposure studies have no country. ${D.meta.source}`;
}
function bestHealth(it){let b=0,m=-1;HL.forEach((h,k)=>{const v=edgeP(it,h.key).studies;if(v>m){m=v;b=k;}});return b;}
function row(k,v){return `<div class="metric"><b>${k}</b>${v}</div>`;}
function inspect(id){
  const el=document.getElementById('ginspect'),p=id.split(':');let html='';
  if(p[0]==='hl'){const it=ITEM(+p[1]),h=HL[+p[2]],e=edgeP(it,h.key),f=edgeF(it,h.key),fl=it.health[h.key].findings,c=cons(e.pct_sig)[1];
    html=`<h4>${esc(it.name)} → ${esc(h.name)}</h4>`+
    row('Problem evidence',`${e.studies} studies link ${esc(it.exposure)} to ${esc(h.name.toLowerCase())}${uk()?' (UK only)':''}<br>${sigtxt(e)}${e.trials?` · ${e.trials} trial${e.trials>1?'s':''}`:''}`)+
    (uk()?'':row('Consistency',{consistent:'Consistent: 60%+ of studies significant',mixed:'Mixed: 40–59% significant','mostly null':'Mostly null: under 40% significant',untestable:'No CI or p-value to test'}[c]))+
    (uk()?'':row('Finding types',`${e.effect_size||0} effect-size findings (odds, risk or hazard ratios, correlations)<br>${e.group_comparison||0} group comparisons`))+
    (+p[1]===8?'':row('Fix evidence',`${f.studies||0} studies test the action on this outcome${(f.studies||0)?'<br>'+sigtxt(f):' — <span style="color:#b3006b;font-weight:700">gap: never tested directly</span>'}`))+
    row('What this means','An expected benefit via the exposure, not a measured effect of the action. Findings are associations, not causal estimates.')+
    row('How these were made','LLM-extracted from peer-reviewed papers (PubMed, Europe PMC, OpenAlex), values checked against the source text. Matched to this action by our keyword rules rather than System’s biomedical concept labels.')+
    `<div class="metric"><b>Findings in the graph</b>${fl.length?'':'None in this view.'}</div><ul>${(uk()?fl.filter(f=>f.r==='UK'):fl).slice(0,12).map(f=>`<li><span class="tagk ${f.k==='exposure'?'e':''}">${f.k==='exposure'?'EXPOSURE':'ACTION TEST'}</span>${esc(f.a)} → ${esc(f.b)}<div><span class="st">${esc(f.st||'')} ${f.v!=null?esc(f.v):''}${f.lo!=null?` (${esc(f.lo)}–${esc(f.hi)})`:''}</span></div><div class="meta">${esc(f.c)}${f.r==='UK'?' · UK':''}${f.doi?` · <a href="https://doi.org/${esc(f.doi)}" target="_blank" rel="noopener">doi</a>`:''}</div></li>`).join('')}</ul>`;
    if(+p[1]!==8&&it.notes&&it.notes.length)html+=row('Reviews &amp; trials outside the graph',it.notes.map(esc).join('<br>'));}
  else if(p[0]==='cob'){const it=INTS[+p[1]],g=CB[+p[2]];
    if(p[3]==='na')html=`<h4>${esc(it.name)} → ${esc(g.name)}</h4>`+row('Status','Not assessed: no evidence found for this action. A data gap worth funding.');
    else{const c=it.cob[+p[3]];html=`<h4>${esc(it.name)} → ${esc(g.name)}</h4>`+row('Direction',{benefit:'Possible benefit',mixed:'Mixed / conditional',harm:'Potential harm / trade-off'}[c.type]+' · '+c.w)+row('Evidence',esc(c.text))+row('Source',esc(c.src||'not quantified')+' · cited report, outside the System graph');}}
  el.innerHTML=html;
}
function pick(i){st.sel=i;st.edge=null;draw();}
window.HP_selectAction=function(i){location.href='graph.html?a='+i;};window.HP_openPackage=function(arr){location.href='graph.html?a='+arr.join(',');};
document.getElementById('gpick').innerHTML=(ONLY.length?[]:VIS).map(i=>`<button type="button" data-pick="${i}" aria-pressed="false">${esc(INTS[i].name)}</button>`).join('');
document.getElementById('gpick').addEventListener('click',e=>{const b=e.target.closest('[data-pick]');if(b)pick(+b.dataset.pick);});
document.querySelectorAll('[data-layout]').forEach(b=>b.addEventListener('click',()=>{st.layout=b.dataset.layout;document.querySelectorAll('[data-layout]').forEach(x=>x.setAttribute('aria-pressed',String(x===b)));draw();}));
document.querySelectorAll('[data-region]').forEach(b=>b.addEventListener('click',()=>{st.region=b.dataset.region;document.querySelectorAll('[data-region]').forEach(x=>x.setAttribute('aria-pressed',String(x===b)));draw();}));
const svg=document.getElementById('gsvg');
const act=t=>{const e=t.closest('[data-edge]');if(e){st.edge=e.dataset.edge;inspect(st.edge);document.getElementById('ginspect').scrollIntoView({behavior:'smooth',block:'nearest'});return;}const n=t.closest('[data-kind="int"]');if(n&&ONLY.length!==1)pick(+n.dataset.i);};
svg.addEventListener('click',e=>act(e.target));svg.addEventListener('keydown',e=>{if(e.key==='Enter'||e.key===' '){e.preventDefault();act(e.target);}});
draw();
})();
