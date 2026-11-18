/* Browser Pareto explorer: source-of-truth datasets are built by web/build_site.py. */
'use strict';
const $=id=>document.getElementById(id);
const palette={'OpenAI':'#198c75','Anthropic':'#db8655','Google':'#588bc6','Microsoft':'#a576d1','GitHub':'#825bdf','xAI':'#718c9d','Alibaba':'#c49c40','DeepSeek':'#d06565','Moonshot AI':'#c55f96','MiniMax':'#b58645','Z.ai':'#be6565','ByteDance':'#ce8552'};
const $ns='http://www.w3.org/2000/svg';
let db=null, platform='Copilot', chartId='', chosen=new Set(), expanded=new Set(), labelMode='on', bounds=null, limits=null, costScale='linear', sidebarWidth=275, sidebarHidden=false, sidebarScroll=0;
const costDecimals=x=>Math.abs(x)<0.01?3:2;
const money=x=>'$'+Number(x).toLocaleString('en-US',{maximumFractionDigits:costDecimals(x),minimumFractionDigits:costDecimals(x)});
const shortCost=x=>Number(Number(x).toFixed(costDecimals(x)));
const pct=x=>Number(x).toLocaleString('en-US',{maximumFractionDigits:1});
const fmt=x=>Number(x).toLocaleString('en-US',{maximumFractionDigits:2});
const esc=x=>String(x??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;','"':'&quot;',"'":'&#39;'}[c]));
const key=m=>m.provider+'\0'+m.model;
function catalogs(){return db.catalog.filter(m=>m.platforms?.[platform]);}
function charts(){return db.charts.filter(c=>c.platforms?.includes(platform));}
function chart(){return charts().find(c=>c.id===chartId)||charts()[0];}
function scored(){return chart().points.filter(p=>chosen.has(key(p)));}
function visible(){return scored().filter(p=>p.cost>=bounds.xmin-1e-9&&p.cost<=bounds.xmax+1e-9&&p.score>=bounds.ymin-1e-9&&p.score<=bounds.ymax+1e-9);}
const preferenceKey='coding-agent-pareto.sidebar.v1';
const exclusionKey='coding-agent-pareto.model-exclusions.v1';
// Browser URL records the shared view; excluded model choices stay private in localStorage.
function getExclusions(){try{const v=JSON.parse(localStorage.getItem(exclusionKey)||'{}');return new Set(v[platform]||[])}catch{return new Set()}}
function saveExclusions(){try{const all=JSON.parse(localStorage.getItem(exclusionKey)||'{}');all[platform]=catalogs().filter(m=>!chosen.has(key(m))).map(key);localStorage.setItem(exclusionKey,JSON.stringify(all))}catch{}}
function writeQuery(){if(!db||!location.protocol.startsWith('http'))return;const u=new URL(location.href);const q=u.searchParams;
 for(const [k,v] of Object.entries({agent:platform,benchmark:chart().benchmark,snapshot:chart().id,scale:costScale,labels:labelMode,xmin:shortCost(bounds.xmin),xmax:shortCost(bounds.xmax),ymin:Number(bounds.ymin.toFixed(1)),ymax:Number(bounds.ymax.toFixed(1))})){q.set(k,String(v))}
 history.replaceState(null,'',u.pathname+'?'+q.toString()+u.hash);
}
function restoreQuery(q){
 const target=charts().find(c=>c.id===q.get('snapshot')) || charts().find(c=>c.benchmark===q.get('benchmark'));
 if(target){chartId=target.id;renderSnapshotOptions();rangeReset();renderAll()}
 const scale=q.get('scale');if(scale==='log'||scale==='linear')setCostScale(scale,true);
 const labels=q.get('labels');labelMode=labels==='none'?'none':'on';$('label-mode').value=labelMode;
 for(const side of ['min','max'])for(const a of ['x','y']){
  let v=Number(q.get(a+side));if(!q.has(a+side)||!Number.isFinite(v))continue;
  bounds[a+side]=Math.max(limits[a+'min'],Math.min(limits[a+'max'],v));
 }
 if(bounds.xmin>=bounds.xmax||bounds.ymin>=bounds.ymax)rangeReset();
 syncAxisInputs();renderAll();writeQuery();
}

function restoreSidebar(){try{const v=JSON.parse(localStorage.getItem(preferenceKey)||'{}');sidebarWidth=Math.min(620,Math.max(210,Number(v.width)||275));sidebarHidden=Boolean(v.hidden);sidebarScroll=Math.max(0,Number(v.scroll)||0)}catch{}applySidebar()}
function applySidebar(){const layout=$('layout');layout.style.setProperty('--sidebar-width',sidebarWidth+'px');layout.classList.toggle('sidebar-hidden',sidebarHidden);$('show-filters').hidden=!sidebarHidden;$('show-filters').setAttribute('aria-expanded',String(!sidebarHidden));$('sidebar-resizer').setAttribute('aria-valuenow',String(sidebarWidth));}
function storeSidebar(){try{localStorage.setItem(preferenceKey,JSON.stringify({width:sidebarWidth,hidden:sidebarHidden,scroll:sidebarScroll}))}catch{}}
function bindSidebar(){restoreSidebar();let scrollTimer;$('filters').addEventListener('scroll',()=>{clearTimeout(scrollTimer);scrollTimer=setTimeout(()=>{sidebarScroll=$('filters').scrollTop;storeSidebar()},120)});$('hide-filters').addEventListener('click',()=>{sidebarHidden=true;applySidebar();storeSidebar();renderContent()});$('show-filters').addEventListener('click',()=>{sidebarHidden=false;applySidebar();storeSidebar();renderContent()});const grip=$('sidebar-resizer');let startX=0,startW=0;
 grip.addEventListener('pointerdown',e=>{if(matchMedia('(max-width:780px)').matches)return;startX=e.clientX;startW=sidebarWidth;grip.setPointerCapture(e.pointerId);grip.classList.add('dragging')});
 grip.addEventListener('pointermove',e=>{if(!grip.hasPointerCapture(e.pointerId))return;sidebarWidth=Math.min(620,Math.max(210,startW+e.clientX-startX));applySidebar()});
 grip.addEventListener('pointerup',e=>{if(grip.hasPointerCapture(e.pointerId))grip.releasePointerCapture(e.pointerId);grip.classList.remove('dragging');storeSidebar();renderContent()});
 grip.addEventListener('keydown',e=>{if(e.key==='ArrowLeft'||e.key==='ArrowRight'){e.preventDefault();sidebarWidth=Math.min(620,Math.max(210,sidebarWidth+(e.key==='ArrowRight'?20:-20)));applySidebar();storeSidebar()}});
}
function scaleValue(a,v){return a==='x'&&costScale==='log'?Math.log10(Math.max(v,limits.xmin)):v}
function unscaleValue(a,v){return a==='x'&&costScale==='log'?10**v:v}
function logFloor(){const ps=scored().filter(p=>p.cost>0);const all=ps.length?ps:chart().points.filter(p=>p.cost>0);const min=Math.min(...all.map(p=>p.cost));const v=min*.9;const mag=10**Math.floor(Math.log10(v));return Math.max(.000001,Math.floor(v/mag*10)/10*mag)}
function rangeReset(){const ps=chart().points;const xmax=Math.max(1,...ps.map(p=>p.cost));const ymin=Math.max(0,Math.floor((Math.min(...ps.map(p=>p.score))-7)/5)*5);const ymax=Math.min(100,Math.ceil((Math.max(...ps.map(p=>p.score))+7)/5)*5);const floor=costScale==='log'?logFloor():0;
 limits={xmin:floor,xmax:Math.max(1,Math.ceil(xmax*1.08*10)/10),ymin:0,ymax:100};bounds={xmin:floor,xmax:limits.xmax,ymin,ymax};syncAxisInputs();}
function syncAxisInputs(){for(const a of ['x','y']){
  const min=scaleValue(a,limits[a+'min']),max=scaleValue(a,limits[a+'max']),step=a==='x'&&costScale==='log'?0.001:a==='x'?Math.max(.001,(max-min)/2000):.1;
  for(const side of ['min','max']){const slider=$(a+'-'+side);slider.min=min;slider.max=max;slider.step=step;slider.value=scaleValue(a,bounds[a+side]);$(a+'-'+side+'-value').value=a==='x'?shortCost(bounds[a+side]):Number(bounds[a+side].toFixed(1));}
  const span=Math.max(1e-9,max-min),lo=100*(scaleValue(a,bounds[a+'min'])-min)/span,hi=100*(scaleValue(a,bounds[a+'max'])-min)/span;
  $(a+'-dual').style.setProperty('--lo',Math.max(0,Math.min(100,lo))+'%');$(a+'-dual').style.setProperty('--hi',Math.max(0,Math.min(100,hi))+'%');
  for(const side of ['min','max']){const g=$(a+'-'+side+'-grip');g.setAttribute('aria-valuemin',String(limits[a+'min']));g.setAttribute('aria-valuemax',String(limits[a+'max']));g.setAttribute('aria-valuenow',String(Number(bounds[a+side].toPrecision(7))));g.setAttribute('aria-valuetext',a==='x'?money(bounds[a+side]):fmt(bounds[a+side])+' percent');}
 }}
function bindAxes(){for(const a of ['x','y'])for(const side of ['min','max']){
  const number=$(a+'-'+side+'-value'),grip=$(a+'-'+side+'-grip');let pointerActive=false;
  const on=value=>{let n=Number(value);if(!Number.isFinite(n))return;
    const minimum=scaleValue(a,limits[a+'min']),maximum=scaleValue(a,limits[a+'max']);
    let v=Math.max(minimum,Math.min(maximum,scaleValue(a,n)));const minGap=a==='y'?.1:Math.max((maximum-minimum)*0.0001,0.000001);
    if(side==='min')v=Math.min(v,scaleValue(a,bounds[a+'max'])-minGap);
    else v=Math.max(v,scaleValue(a,bounds[a+'min'])+minGap);
    bounds[a+side]=unscaleValue(a,Math.max(minimum,Math.min(maximum,v)));syncAxisInputs();renderContent();writeQuery();};
  number.addEventListener('change',()=>on(number.value));
  function pointerValue(e){const box=$(a+'-dual').getBoundingClientRect();let fraction=a==='x'?(e.clientX-box.left)/box.width:(box.bottom-e.clientY)/box.height;
    fraction=Math.max(0,Math.min(1,fraction));return unscaleValue(a,scaleValue(a,limits[a+'min'])+fraction*(scaleValue(a,limits[a+'max'])-scaleValue(a,limits[a+'min'])))}
  grip.addEventListener('pointerdown',e=>{pointerActive=true;grip.setPointerCapture(e.pointerId);on(pointerValue(e));e.preventDefault()});
  grip.addEventListener('pointermove',e=>{if(pointerActive)on(pointerValue(e))});
  grip.addEventListener('pointerup',()=>{pointerActive=false});
  grip.addEventListener('pointercancel',()=>{pointerActive=false});
  grip.addEventListener('keydown',e=>{const delta=a==='x'?Math.max(.001,(limits.xmax-limits.xmin)/100):1;
    let target=bounds[a+side];if(e.key==='Home')target=limits[a+'min'];else if(e.key==='End')target=limits[a+'max'];
    else if(e.key==='ArrowLeft'||e.key==='ArrowDown')target=costScale==='log'&&a==='x'?target/1.2:target-delta;
    else if(e.key==='ArrowRight'||e.key==='ArrowUp')target=costScale==='log'&&a==='x'?target*1.2:target+delta;
    else return;e.preventDefault();on(target)});
 }}
function setCostScale(mode,skipQuery=false){if(!['log','linear'].includes(mode))return;costScale=mode;$('cost-scale').value=mode;
 const ps=chart().points.filter(p=>p.cost>0);if(mode==='log'){
  limits.xmin=logFloor();
  if(bounds.xmin<limits.xmin)bounds.xmin=limits.xmin;
 }else{limits.xmin=0;if(bounds.xmin>0&&bounds.xmin<=Math.min(...ps.map(p=>p.cost))/10)bounds.xmin=0;}
 $('scale-explainer').textContent=mode==='log'?'Logarithmic: spreads low-cost points (cost must be positive); equal distance = equal ratio.':'Linear: compare absolute task costs directly. Switch to logarithmic to separate clustered low costs.';
 syncAxisInputs();renderContent();if(!skipQuery)writeQuery();}
function choosePlatform(name,skipQuery=false){if(!db||!['Copilot','Kiro','Claude Code'].includes(name))return;platform=name;const excluded=getExclusions();chosen=new Set(catalogs().filter(m=>!excluded.has(key(m))).map(key));expanded=new Set();$('model-search').value='';
 document.querySelectorAll('.platform-btn').forEach(b=>{b.classList.toggle('active',b.dataset.platform===platform);b.setAttribute('aria-pressed',b.dataset.platform===platform?'true':'false');});
 $('platform-full').value=platform;$('platform-heading').textContent=platform==='Copilot'?'GitHub Copilot':platform;
 const c=charts();chartId=c[0].id;renderBenchmarkOptions();rangeReset();renderAll();if(!skipQuery)writeQuery();requestAnimationFrame(()=>{$('filters').scrollTop=sidebarScroll});}
function renderTree(){const host=$('providers'),s=$('model-search').value.trim().toLowerCase(),oldScroll=$('filters').scrollTop;
 let prs=[...new Set(catalogs().map(m=>m.provider))].sort((a,b)=>a.localeCompare(b));
 host.replaceChildren(...prs.filter(pr=>{const models=catalogs().filter(m=>m.provider===pr);return !s||pr.toLowerCase().includes(s)||models.some(m=>m.model.toLowerCase().includes(s))}).map(pr=>{
  const models=catalogs().filter(m=>m.provider===pr).sort((a,b)=>a.model.localeCompare(b.model));const sel=models.filter(m=>chosen.has(key(m))).length;
  const country=models[0]?.country||'Unknown';const section=document.createElement('section');section.className='company';
  const head=document.createElement('div');head.className='company-head';
  const exp=document.createElement('button');exp.className='expand';exp.type='button';exp.textContent=expanded.has(pr)?'▾':'▸';exp.setAttribute('aria-label','Expand '+pr);exp.addEventListener('click',()=>{expanded.has(pr)?expanded.delete(pr):expanded.add(pr);renderTree()});
  const chk=document.createElement('input');chk.type='checkbox';chk.checked=sel===models.length;chk.indeterminate=sel>0&&sel<models.length;chk.setAttribute('aria-label','All models for '+pr);chk.addEventListener('change',()=>{models.forEach(m=>chk.checked?chosen.add(key(m)):chosen.delete(key(m)));saveExclusions();renderAll()});
  const name=document.createElement('span');name.className='company-name';name.textContent=pr;
  const countryTag=document.createElement('span');countryTag.className='country';countryTag.textContent=country;
  const count=document.createElement('span');count.className='company-count';count.textContent=sel+'/'+models.length;
  head.append(exp,chk,name,countryTag,count);section.append(head);
  const children=document.createElement('div');children.className='children';children.hidden=!(expanded.has(pr)||Boolean(s));
  for(const m of models.filter(m=>!s||pr.toLowerCase().includes(s)||m.model.toLowerCase().includes(s))){const row=document.createElement('label');row.className='child';const cb=document.createElement('input');cb.type='checkbox';cb.checked=chosen.has(key(m));cb.setAttribute('aria-label','Model '+m.model);cb.addEventListener('change',()=>{cb.checked?chosen.add(key(m)):chosen.delete(key(m));saveExclusions();renderAll()});const title=document.createElement('span');title.textContent=m.model;title.title=m.model;row.append(cb,title);children.append(row)}
  section.append(children);return section;
 }));
 $('filter-total').textContent=chosen.size+'/'+catalogs().length;
 $('filters').scrollTop=oldScroll;
}
function svg(tag,attrs={},parent){const e=document.createElementNS($ns,tag);for(const [k,v] of Object.entries(attrs))e.setAttribute(k,String(v));if(parent)parent.append(e);return e}
function txt(parent,x,y,s,attrs={}){const t=svg('text',{x,y,...attrs},parent);t.textContent=s;return t}
function frontier(points){let high=-Infinity;return [...points].sort((a,b)=>a.cost-b.cost||b.score-a.score).filter(p=>{if(p.score>high+1e-8){high=p.score;return true}return false})}
function graph(points){let host=$('chart-area');host.replaceChildren();const width=1200,height=675;
 if(!points.length){host.innerHTML='<p class="empty">No measured points in this range. Expand the cost / score axes or choose another benchmark.</p>';return}
 const plot={x:72,y:26,w:1103,h:574};const s=svg('svg',{viewBox:`0 0 ${width} ${height}`,role:'img','aria-label':chart().label+' interactive plot',preserveAspectRatio:'xMidYMid meet'},host);
 svg('rect',{x:plot.x,y:plot.y,width:plot.w,height:plot.h,class:'svg-panel'},s);
 const xp=x=>plot.x+((scaleValue('x',x)-scaleValue('x',bounds.xmin))/(scaleValue('x',bounds.xmax)-scaleValue('x',bounds.xmin)))*plot.w;
 const yp=y=>plot.y+plot.h-(y-bounds.ymin)/(bounds.ymax-bounds.ymin)*plot.h;
 const niceStep=(raw)=>{const m=10**Math.floor(Math.log10(Math.max(raw,1e-10)));return [1,2,2.5,5,10].map(v=>v*m).find(v=>v>=raw)||10*m};
 let xticks=[];
 if(costScale==='log'){
  for(let exp=Math.floor(Math.log10(bounds.xmin))-1;exp<=Math.ceil(Math.log10(bounds.xmax))+1;exp++)for(const factor of [1,2,5]){
   const tick=factor*10**exp;if(tick>=bounds.xmin-1e-10&&tick<=bounds.xmax+1e-10)xticks.push(tick);
  }
  // Do not crowd nearby logarithmic labels.
  xticks=xticks.filter((v,i,arr)=>i===0||xp(v)-xp(arr[i-1])>65);
 }else{const step=niceStep((bounds.xmax-bounds.xmin)/7);for(let v=Math.ceil(bounds.xmin/step)*step;v<=bounds.xmax+step*1e-9;v+=step)xticks.push(v)}
 for(const v of xticks){const x=xp(v);svg('line',{x1:x,x2:x,y1:plot.y,y2:plot.y+plot.h,class:'svg-grid'},s);txt(s,x,plot.y+plot.h+27,money(v),{'text-anchor':'middle',class:'svg-tick'});}
 const ystep=niceStep((bounds.ymax-bounds.ymin)/7);
 for(let v=Math.ceil(bounds.ymin/ystep)*ystep;v<=bounds.ymax+ystep*1e-9;v+=ystep){const y=yp(v);svg('line',{x1:plot.x,x2:plot.x+plot.w,y1:y,y2:y,class:'svg-grid'},s);txt(s,plot.x-15,y+4,pct(v)+'%',{'text-anchor':'end',class:'svg-tick'});}
 txt(s,plot.x+plot.w/2,height-19,'Estimated benchmark task cost (USD, '+costScale+' scale)',{'text-anchor':'middle',class:'svg-axislabel'});
 const best=frontier(points);
 if(best.length>1)svg('path',{d:best.map((p,i)=>(i?'L':'M')+xp(p.cost).toFixed(2)+' '+yp(p.score).toFixed(2)).join(' '),class:'svg-frontier'},s);
 const labels=[];for(const p of [...points].sort((a,b)=>b.score-a.score)){const x=xp(p.cost),y=yp(p.score),color=palette[p.provider]||'#8796a3';
  const dot=svg('circle',{cx:x,cy:y,r:8,fill:color,stroke:'var(--plot)','stroke-width':1.5,tabindex:0,role:'button',class:'svg-point','aria-label':`${p.model} ${p.effort}: score ${p.score}, cost ${p.cost}`},s);
  dot.addEventListener('mouseenter',e=>showTip(p,e));dot.addEventListener('mousemove',moveTip);dot.addEventListener('mouseleave',hideTip);dot.addEventListener('focus',e=>showTip(p,e));dot.addEventListener('blur',hideTip);
  if(labelMode==='none')continue;
  const label=p.model+(p.effort&&p.effort!=='default'?' / '+p.effort:'');const w=Math.min(290,label.length*8.3+6);let lx=Math.max(plot.x+6,Math.min(plot.x+plot.w-w-6,x+11)),ly=Math.max(plot.y+20,Math.min(plot.y+plot.h-7,y-12));
  let overlap;for(let attempt=0;attempt<55;attempt++){
   overlap=labels.some(q=>lx<q.x+q.w+5&&lx+w+5>q.x&&Math.abs(ly-q.y)<20);
   if(!overlap)break;
   ly=Math.max(plot.y+17,Math.min(plot.y+plot.h-7,y+((attempt%2)?-1:1)*Math.ceil(attempt/2)*20));
  }
  if(overlap)continue;
  labels.push({x:lx,y:ly,w});txt(s,lx,ly,label,{class:'svg-label',fill:color});
 }
 const providers=[...new Set(points.map(p=>p.provider))];$('chart-legend').textContent=providers.map(pr=>`${pr} (${catalogs().find(m=>m.provider===pr)?.country||'Unknown'}) ●`).join(' · ')+' · — Pareto';
}
function showTip(p,event){const el=$('tooltip');el.hidden=false;el.innerHTML=`<strong>${esc(p.model)} / ${esc(p.effort)}</strong><small>${esc(p.provider)} · ${esc(p.country||'Unknown')} · ${esc(p.harness||'benchmark reference')}</small><div>Score <b>${fmt(p.score)}%</b> · Cost <b>${money(p.cost)}</b></div><small>Estimate factor: ×${fmt(p.discount||1)}</small>`;moveTip(event)}
function moveTip(event){const b=$('tooltip');if(b.hidden)return;const x=event.clientX??innerWidth/2,y=event.clientY??innerHeight/2;b.style.left=Math.max(5,Math.min(innerWidth-335,x+12))+'px';b.style.top=Math.max(5,Math.min(innerHeight-125,y+14))+'px'}
function hideTip(){$('tooltip').hidden=true}
function renderTables(points){const sorted=[...points].sort((a,b)=>a.cost-b.cost);
 $('rows').replaceChildren(...sorted.map(p=>{const tr=document.createElement('tr');for(const val of [p.provider+' · '+(p.country||'Unknown'),p.model+' / '+p.effort,fmt(p.score),money(p.cost)]){const td=document.createElement('td');td.textContent=val;tr.append(td)}return tr}));$('table-meta').textContent=points.length+' visible';
 const scoredKeys=new Set(chart().points.map(key));const models=catalogs().filter(m=>chosen.has(key(m))).sort((a,b)=>a.provider.localeCompare(b.provider)||a.model.localeCompare(b.model));
 $('catalog-rows').replaceChildren(...models.map(m=>{const tr=document.createElement('tr'),info=m.platforms[platform]||{},r=info.rate||{};
  let price=r.credits_multiplier!=null?'×'+r.credits_multiplier+' credits':r.input!=null&&r.output!=null?money(r.input)+' / '+money(r.output):'—';let promo=(r.promo_end?'until '+r.promo_end:'')+(r.tier==='promotional'?' · Promo':'');
  if(!promo)promo=info.status||'—';for(const val of [m.provider+' · '+m.country,m.model,scoredKeys.has(key(m))?'Scored':'No score',price,promo]){const td=document.createElement('td');td.textContent=val;tr.append(td)}return tr}));$('catalog-meta').textContent=models.length+' models';
}
function renderContent(){if(!db)return;const ps=visible(),c=chart();graph(ps);$('point-count').textContent=`${ps.length} / ${scored().length} scored points visible`;$('axis-summary').textContent=`${money(bounds.xmin)}–${money(bounds.xmax)} (${costScale}) · ${pct(bounds.ymin)}–${pct(bounds.ymax)}%`;renderTables(ps);
 const src=c.cost_basis||'Benchmark task cost';$('platform-note').textContent=(platform==='Kiro'?'Kiro credits are model multipliers; plotted task costs use benchmark reference estimates.':platform==='Claude Code'?'Claude Code uses Anthropic models; plotted costs are AA benchmark estimates.':'Benchmark USD/task estimates; Fusion discount applied to available scored variants.')+' · '+src;
}
function renderBenchmarkOptions(){const benchmarks=[...new Set(charts().map(c=>c.benchmark))];const sel=$('benchmark-picker');sel.replaceChildren(...benchmarks.map(b=>{const o=document.createElement('option');o.value=b;o.textContent=b;return o}));renderSnapshotOptions();}
function renderSnapshotOptions(){const c=chart();$('benchmark-picker').value=c.benchmark;const siblings=charts().filter(x=>x.benchmark===c.benchmark);const sel=$('snapshot-picker');sel.replaceChildren(...siblings.map(x=>{const o=document.createElement('option');o.value=x.id;o.textContent=`v${x.version} (${x.snapshot})`+(x.id.endsWith('-csv')?' · legacy CSV':'');return o}));sel.value=c.id;}
function sourceLink(x){const a=document.createElement('a');a.href=x.url;a.textContent=x.label;a.target='_blank';a.rel='noopener';return a;}
function renderSources(){const c=chart(),bs=$('benchmark-sources'),ps=$('pricing-sources');bs.replaceChildren();ps.replaceChildren();
 const bSources=c.sources||[],costs=(db.platform_sources||{})[platform]||{};
 for(const entry of bSources){if(entry.url)bs.append(sourceLink(entry));}
 for(const entry of costs.links||[]){if(entry.url)ps.append(sourceLink(entry));}
 const meta=document.createElement('span');meta.className='source-meta';meta.textContent=`Saved price snapshot: ${costs.snapshot||'unknown'} · ${costs.update_method||'manual review required'}`;ps.append(meta);
}
function renderAll(){if(!db)return;renderTree();const c=chart();$('chart-title').textContent=c.label;$('benchmark-picker').value=c.benchmark;$('snapshot-picker').value=c.id;$('chart-meta').textContent=c.snapshot+' · '+c.benchmark+' · '+c.points.length+' scored records in this snapshot';
 const promos=platform==='Copilot'?db.promos:[];$('promo-line').textContent=promos.length?promos.map(x=>`${x.label}: ${x.discount} until ${x.until}`).join(' · '):platform==='Kiro'?'Kiro official credit multipliers shown in model catalog.':'Claude Code official API rates shown in model catalog.';
 const original=db.static_charts?.[c.id];for(const opt of $('export-kind').options)if(opt.value.startsWith('original'))opt.disabled=!original?.[opt.value.split('-')[1]];
 if(!original&&$('export-kind').value.startsWith('original'))$('export-kind').value='view-png';
 $('asset-links').replaceChildren();if(original){for(const ext of ['png','svg']){let a=document.createElement('a');a.href=original[ext];a.textContent='Original two-panel '+ext.toUpperCase();a.target='_blank';a.rel='noopener';$('asset-links').append(a)}}let gha=document.createElement('a');gha.href='https://github.com/ChrisTorng/coding-agent-pareto/actions';gha.textContent='GHA artifacts';gha.target='_blank';gha.rel='noopener';$('asset-links').append(gha);
 renderSources();if(platform==='Copilot'&&c.id==='aa_coding_agent_v21'){const shortcut=document.createElement('button');shortcut.textContent='Fusion Standard / High / Max → DeepSWE';shortcut.type='button';shortcut.className='subtle';shortcut.onclick=()=>setChart('fusion_deepswe_11');$('asset-links').prepend(shortcut)}renderContent();}
function setChart(id,skipQuery=false){if(!charts().some(c=>c.id===id))return;chartId=id;renderSnapshotOptions();rangeReset();renderAll();if(!skipQuery)writeQuery()}
function save(blob,name){const u=URL.createObjectURL(blob),a=document.createElement('a');a.href=u;a.download=name;document.body.append(a);a.click();a.remove();setTimeout(()=>URL.revokeObjectURL(u),5000)}
function svgText(){let root=$('chart-area').querySelector('svg');if(!root)return null;let copy=root.cloneNode(true),style=document.createElementNS($ns,'style');const css=getComputedStyle(document.documentElement);
 const plot=css.getPropertyValue('--plot').trim()||'#fff',grid=css.getPropertyValue('--grid').trim()||'#ddd',tick=css.getPropertyValue('--tick').trim()||'#333',border=css.getPropertyValue('--border').trim()||'#ccc';
 style.textContent=`.svg-panel{fill:${plot};stroke:${border}}.svg-grid{stroke:${grid};stroke-width:1}.svg-label{font:16px Arial;paint-order:stroke;stroke:${plot};stroke-width:3px;stroke-linejoin:round}.svg-tick{font:15px Arial;fill:${tick}}.svg-axislabel{font:17px Arial;fill:${tick}}.svg-frontier{stroke:#20b2a4;stroke-width:3;stroke-dasharray:8 5;fill:none}`;
 copy.insertBefore(style,copy.firstChild);copy.setAttribute('xmlns',$ns);return new XMLSerializer().serializeToString(copy)}
async function exportFile(){const k=$('export-kind').value,c=chart();if(k.startsWith('original')){let file=db.static_charts?.[c.id]?.[k.split('-')[1]];if(file){const a=document.createElement('a');a.href=file;a.download=file.split('/').pop();document.body.append(a);a.click();a.remove()}return}
 if(k==='view-csv'){const fields=['provider','country','model','effort','score','cost','base_cost','discount','harness','source'];const escCsv=v=>'"'+String(v??'').replaceAll('"','""')+'"';let csv=[fields.join(','),...visible().map(p=>fields.map(f=>escCsv(p[f])).join(','))].join('\r\n');save(new Blob([csv],{type:'text/csv;charset=utf-8'}),c.id+'-visible.csv');return}
 const serialized=svgText();if(!serialized)return;if(k==='view-svg'){save(new Blob([serialized],{type:'image/svg+xml'}),c.id+'-visible.svg');return}
 const url=URL.createObjectURL(new Blob([serialized],{type:'image/svg+xml'}));const image=new Image();try{await new Promise((res,rej)=>{image.onload=res;image.onerror=rej;image.src=url});const canvas=document.createElement('canvas');canvas.width=2880;canvas.height=1470;const ctx=canvas.getContext('2d');const bg=getComputedStyle(document.documentElement).getPropertyValue('--plot').trim()||'#fff';ctx.fillStyle=bg;ctx.fillRect(0,0,canvas.width,canvas.height);ctx.drawImage(image,0,0,canvas.width,canvas.height);const png=await new Promise(res=>canvas.toBlob(res,'image/png'));if(png)save(png,c.id+'-visible.png')}finally{URL.revokeObjectURL(url)}}
async function fullscreenToggle(){const card=$('chart-card');if(document.fullscreenElement){await document.exitFullscreen()}else if(card.requestFullscreen){await card.requestFullscreen()}else{card.classList.toggle('fullscreen-fallback');}setTimeout(()=>renderContent(),100)}
function attachEvents(){document.querySelectorAll('.platform-btn').forEach(b=>b.addEventListener('click',()=>choosePlatform(b.dataset.platform)));$('platform-full').addEventListener('change',e=>choosePlatform(e.target.value));$('benchmark-picker').addEventListener('change',e=>{const c=charts().find(c=>c.benchmark===e.target.value);if(c)setChart(c.id)});$('snapshot-picker').addEventListener('change',e=>setChart(e.target.value));$('cost-scale').addEventListener('change',e=>setCostScale(e.target.value));$('label-mode').addEventListener('change',e=>{labelMode=e.target.value;renderContent();writeQuery()});$('model-search').addEventListener('input',renderTree);
 $('collapse-all').addEventListener('click',()=>{expanded.clear();renderTree()});$('expand-all').addEventListener('click',()=>{expanded=new Set(catalogs().map(m=>m.provider));renderTree()});$('select-all').addEventListener('click',()=>{chosen=new Set(catalogs().map(key));saveExclusions();renderAll()});$('exclude-china').addEventListener('click',()=>{chosen=new Set(catalogs().filter(m=>m.country!=='CN').map(key));saveExclusions();renderAll()});$('reset-range').addEventListener('click',()=>{rangeReset();renderContent();writeQuery()});$('export-action').addEventListener('click',exportFile);$('fullscreen-toggle').addEventListener('click',fullscreenToggle);document.addEventListener('fullscreenchange',()=>{$('fullscreen-toggle').textContent=document.fullscreenElement?'✕ Exit fullscreen':'⛶ Fullscreen';renderContent()});bindAxes();bindSidebar();}
async function main(){try{const res=await fetch('./data.json',{cache:'no-store'});if(!res.ok)throw Error('HTTP '+res.status);db=await res.json();if(!db.catalog?.length||!db.charts?.length)throw Error('Missing catalog data');attachEvents();const query=new URLSearchParams(location.search);choosePlatform(['Copilot','Kiro','Claude Code'].includes(query.get('agent'))?query.get('agent'):'Copilot',true);restoreQuery(query)}catch(e){$('chart-area').textContent='Data unavailable: '+e.message;console.error(e)}}
main();