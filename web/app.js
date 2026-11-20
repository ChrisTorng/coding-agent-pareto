/* Browser Pareto explorer: source-of-truth datasets are built by web/build_site.py. */
'use strict';
const $=id=>document.getElementById(id);
const palette={'OpenAI':'#198c75','Anthropic':'#db8655','Google':'#588bc6','Microsoft':'#a576d1','GitHub':'#825bdf','xAI':'#718c9d','Alibaba':'#c49c40','DeepSeek':'#d06565','Moonshot AI':'#c55f96','MiniMax':'#b58645','Z.ai':'#be6565','ByteDance':'#ce8552'};
const $ns='http://www.w3.org/2000/svg';
let db=null, platform='Copilot', chartId='', chosen=new Set(), expanded=new Set(), labelMode='on', bounds=null, limits=null, costScale='linear', sidebarWidth=275, sidebarHidden=false, sidebarScroll=0;
let rangeMode='pareto', pointMode='all', paretoLabelsOnly=false, autoBounds=null, draggingAxis=false, previewFrame=0, lastPreviewAt=0;
const costDecimals=x=>Math.abs(x)<1e-9?0:Math.abs(x)<0.1?3:2;
const money=x=>'$'+Number(x).toLocaleString('en-US',{maximumFractionDigits:costDecimals(x),minimumFractionDigits:0});
const shortCost=x=>Number(Number(x).toFixed(costDecimals(x)));
const pct=x=>Number(x).toLocaleString('en-US',{maximumFractionDigits:1});
const fmt=x=>Number(x).toLocaleString('en-US',{maximumFractionDigits:2});
const esc=x=>String(x??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;','"':'&quot;',"'":'&#39;'}[c]));
const key=m=>m.provider+'\0'+m.model;
// Leave all models in data.json for price/promotion monitoring, but only
// show models with valid benchmark score and task cost in the filter tree.
const scoredModelCache=new Map();
function eligibleScoredKeys(){
 if(!scoredModelCache.has(platform)){
  const keys=new Set();
  for(const c of charts())for(const p of c.points){
   if(Number.isFinite(p.score)&&Number.isFinite(p.cost))keys.add(key(p));
  }
  scoredModelCache.set(platform,keys);
 }
 return scoredModelCache.get(platform);
}
function catalogs(){const keys=eligibleScoredKeys();return db.catalog.filter(m=>m.platforms?.[platform]&&keys.has(key(m)));}
function charts(){return db.charts.filter(c=>c.platforms?.includes(platform));}
function chart(){return charts().find(c=>c.id===chartId)||charts()[0];}
function scored(){return chart().points.filter(p=>chosen.has(key(p)));}
function visible(){
 const base=scored(), unique=new Set(frontier(base));
 return base.filter(p=>(pointMode==='all'||unique.has(p))&&p.cost>=bounds.xmin-1e-8&&p.cost<=bounds.xmax+1e-8&&p.score>=bounds.ymin-1e-8&&p.score<=bounds.ymax+1e-8);
}
function latestChart(list){return [...list].sort((a,b)=>String(b.snapshot).localeCompare(String(a.snapshot))||String(b.version).localeCompare(String(a.version)))[0]}
function defaultChart(){return charts()[0] && latestChart(charts().filter(c=>c.benchmark===charts()[0].benchmark))}
function setAutoRangeFromSelection(){rangeReset();}
function numericEquals(a,b){return Math.abs(a-b)<=Math.max(1e-6,Math.abs(b)*1e-6)}
const preferenceKey='coding-agent-pareto.sidebar.v1';
const exclusionKey='coding-agent-pareto.model-exclusions.v1';
// Browser URL records the shared view; excluded model choices stay private in localStorage.
function getExclusions(){try{const v=JSON.parse(localStorage.getItem(exclusionKey)||'{}');return new Set(v[platform]||[])}catch{return new Set()}}
function saveExclusions(){try{const all=JSON.parse(localStorage.getItem(exclusionKey)||'{}');all[platform]=catalogs().filter(m=>!chosen.has(key(m))).map(key);localStorage.setItem(exclusionKey,JSON.stringify(all))}catch{}}
// Only nondefault choices become URL parameters. A clean homepage is always the latest snapshot.
function writeQuery(){
 if(!db||!location.protocol.startsWith('http'))return;
 const q=new URLSearchParams(),defaultPlatform='Copilot';
 const def=platform==='Copilot'?db.charts.filter(c=>c.platforms?.includes('Copilot')):charts();
 const defaultForPlatform=latestChart(def.filter(c=>c.benchmark===def[0]?.benchmark))||def[0];
 const c=chart();
 if(platform!==defaultPlatform)q.set('agent',platform);
 if(c.benchmark!==defaultForPlatform?.benchmark)q.set('benchmark',c.benchmark);
 if(c.id!==latestChart(charts().filter(x=>x.benchmark===c.benchmark))?.id)q.set('snapshot',c.id);
 if(costScale!=='linear')q.set('scale',costScale);
 if(labelMode!=='on')q.set('labels','off');
 if(rangeMode!=='pareto')q.set('range',rangeMode);
 if(pointMode!=='all')q.set('points',pointMode);
 if(paretoLabelsOnly)q.set('paretoLabels','1');
 for(const a of ['x','y'])for(const side of ['min','max']){
   const field=a+side,v=bounds[field],d=autoBounds[field];
   if(!numericEquals(v,d))q.set(field,String(Number(v.toPrecision(6))));
 }
 const qs=q.toString();history.replaceState(null,'',location.pathname+(qs?'?'+qs:'')+location.hash);
}
function restoreQuery(q){
 const target=charts().find(c=>c.id===q.get('snapshot'))||
     (q.has('benchmark')?latestChart(charts().filter(c=>c.benchmark===q.get('benchmark'))):null);
 if(target){chartId=target.id;renderSnapshotOptions();}
 costScale=q.get('scale')==='log'?'log':'linear';
 document.querySelector(`input[name="cost-scale"][value="${costScale}"]`).checked=true;
 rangeMode=q.get('range')==='all'?'all':'pareto';$('range-mode').value=rangeMode;
 pointMode=q.get('points')==='pareto'?'pareto':'all';$('point-mode').value=pointMode;
 labelMode=(q.get('labels')==='off'||q.get('labels')==='none')?'none':'on';$('label-mode').checked=labelMode==='on';
 paretoLabelsOnly=q.get('paretoLabels')==='1';$('pareto-labels').checked=paretoLabelsOnly;
 rangeReset();
 for(const side of ['min','max'])for(const a of ['x','y']){
  const field=a+side,v=Number(q.get(field));if(!q.has(field)||!Number.isFinite(v))continue;
  bounds[field]=Math.max(limits[a+'min'],Math.min(limits[a+'max'],v));
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
function logFloor(){
 const ps=scored().filter(p=>p.cost>0);const all=ps.length?ps:chart().points.filter(p=>p.cost>0);
 return Math.max(0.000001,Math.min(...all.map(p=>p.cost))*.93);
}
function rangeReset(){
 const all=chart().points;const selected=scored();
 const costs=all.map(p=>p.cost).filter(x=>x>0),scores=all.map(p=>p.score);
 const costHigh=Math.max(1,...costs),scoreLow=Math.min(...scores),scoreHigh=Math.max(...scores);
 limits={xmin:costScale==='log'?logFloor():0,xmax:Number((costHigh*1.07).toPrecision(6)),ymin:0,ymax:100};
 const pareto=frontier(selected.length?selected:all);
 const focus=rangeMode==='pareto'?pareto:(selected.length?selected:all);
 const fcost=focus.map(p=>p.cost),fscores=focus.map(p=>p.score);
 const lo=Math.min(...fcost),hi=Math.max(...fcost),ys=Math.min(...fscores),yh=Math.max(...fscores);
 const costSpan=Math.max(hi-lo,hi*.02,.01);const ySpan=Math.max(yh-ys,2);
 let xmin=costScale==='log'?Math.max(limits.xmin,lo/(10**.06)):Math.max(0,lo-costSpan*.035);
 let xmax=Math.min(limits.xmax,hi+costSpan*.045);
 if(xmax-xmin<.00001)xmax=Math.min(limits.xmax,xmin+.01);
 bounds={xmin,xmax,ymin:Math.max(0,Math.floor(ys-ySpan*.07)),ymax:Math.min(100,Math.ceil(yh+ySpan*.07))};
 autoBounds={...bounds};syncAxisInputs();
}
function syncAxisInputs(){for(const a of ['x','y']){
  const min=scaleValue(a,limits[a+'min']),max=scaleValue(a,limits[a+'max']),step=a==='x'&&costScale==='log'?0.001:a==='x'?Math.max(.001,(max-min)/2000):.1;
  for(const side of ['min','max']){const slider=$(a+'-'+side);slider.min=min;slider.max=max;slider.step=step;slider.value=scaleValue(a,bounds[a+side]);$(a+'-'+side+'-value').value=a==='x'?shortCost(bounds[a+side]):Number(bounds[a+side].toFixed(1));}
  const span=Math.max(1e-9,max-min),lo=100*(scaleValue(a,bounds[a+'min'])-min)/span,hi=100*(scaleValue(a,bounds[a+'max'])-min)/span;
  $(a+'-dual').style.setProperty('--lo',Math.max(0,Math.min(100,lo))+'%');$(a+'-dual').style.setProperty('--hi',Math.max(0,Math.min(100,hi))+'%');
  for(const side of ['min','max']){const g=$(a+'-'+side+'-grip');g.setAttribute('aria-valuemin',String(limits[a+'min']));g.setAttribute('aria-valuemax',String(limits[a+'max']));g.setAttribute('aria-valuenow',String(Number(bounds[a+side].toPrecision(7))));g.setAttribute('aria-valuetext',a==='x'?money(bounds[a+side]):fmt(bounds[a+side])+' percent');}
 }}
function updateRangeReadout(){
 $('axis-summary').textContent=`${money(bounds.xmin)}–${money(bounds.xmax)} (${costScale}) · ${pct(bounds.ymin)}–${pct(bounds.ymax)}%`;
}
function queueGraphPreview(){
 if(previewFrame)return;
 previewFrame=requestAnimationFrame(now=>{
   previewFrame=0;
   if(now-lastPreviewAt<40)return;
   lastPreviewAt=now;
   graph(visible());updateRangeReadout();
 });
}
function commitAxisChange(){draggingAxis=false;renderContent();writeQuery();}
function bindAxes(){for(const a of ['x','y'])for(const side of ['min','max']){
 const number=$(a+'-'+side+'-value'),grip=$(a+'-'+side+'-grip');let pointerActive=false;
 const on=(value,drag=false)=>{let n=Number(value);if(!Number.isFinite(n))return;
  const minimum=scaleValue(a,limits[a+'min']),maximum=scaleValue(a,limits[a+'max']);
  let v=Math.max(minimum,Math.min(maximum,scaleValue(a,n)));
  const minGap=a==='y'?.1:Math.max((maximum-minimum)*0.0001,0.000001);
  if(side==='min')v=Math.min(v,scaleValue(a,bounds[a+'max'])-minGap);
  else v=Math.max(v,scaleValue(a,bounds[a+'min'])+minGap);
  bounds[a+side]=unscaleValue(a,Math.max(minimum,Math.min(maximum,v)));
  if(drag){draggingAxis=true;syncAxisInputs();queueGraphPreview();}
  else{syncAxisInputs();commitAxisChange();}
 };
 number.addEventListener('change',()=>on(number.value));
 const pointerValue=e=>{const box=$(a+'-dual').getBoundingClientRect();let f=a==='x'?(e.clientX-box.left)/box.width:(box.bottom-e.clientY)/box.height;
   f=Math.max(0,Math.min(1,f));return unscaleValue(a,scaleValue(a,limits[a+'min'])+f*(scaleValue(a,limits[a+'max'])-scaleValue(a,limits[a+'min'])))};
 grip.addEventListener('pointerdown',e=>{pointerActive=true;grip.setPointerCapture(e.pointerId);on(pointerValue(e),true);e.preventDefault()});
 grip.addEventListener('pointermove',e=>{if(pointerActive)on(pointerValue(e),true)});
 grip.addEventListener('pointerup',e=>{if(!pointerActive)return;pointerActive=false;if(grip.hasPointerCapture(e.pointerId))grip.releasePointerCapture(e.pointerId);commitAxisChange()});
 grip.addEventListener('pointercancel',()=>{if(pointerActive){pointerActive=false;commitAxisChange()}});
 grip.addEventListener('keydown',e=>{const d=a==='x'?Math.max(.001,(limits.xmax-limits.xmin)/100):1;let n=bounds[a+side];
 if(e.key==='Home')n=limits[a+'min'];else if(e.key==='End')n=limits[a+'max'];
 else if(e.key==='ArrowLeft'||e.key==='ArrowDown')n=costScale==='log'&&a==='x'?n/1.2:n-d;
 else if(e.key==='ArrowRight'||e.key==='ArrowUp')n=costScale==='log'&&a==='x'?n*1.2:n+d;
 else return;e.preventDefault();on(n)});
 }}
function setCostScale(mode,skipQuery=false){if(!['log','linear'].includes(mode))return;costScale=mode;
 document.querySelector(`input[name="cost-scale"][value="${mode}"]`).checked=true;
 $('scale-explainer').textContent=mode==='log'?'Logarithmic: equal distance represents equal cost ratios.':'Linear: equal distance represents equal USD costs.';
 rangeReset();renderContent();if(!skipQuery)writeQuery();
}
function choosePlatform(name,skipQuery=false){if(!db||!['Copilot','Kiro','Claude Code'].includes(name))return;platform=name;const excluded=getExclusions();chosen=new Set(catalogs().filter(m=>!excluded.has(key(m))).map(key));expanded=new Set();$('model-search').value='';
 document.querySelectorAll('.platform-btn').forEach(b=>{b.classList.toggle('active',b.dataset.platform===platform);b.setAttribute('aria-pressed',b.dataset.platform===platform?'true':'false');});
 $('platform-full').value=platform;$('platform-heading').textContent=platform==='Copilot'?'GitHub Copilot':platform;
 chartId=defaultChart().id;renderBenchmarkOptions();rangeReset();renderAll();if(!skipQuery)writeQuery();requestAnimationFrame(()=>{$('filters').scrollTop=sidebarScroll});}
function renderTree(){const host=$('providers'),s=$('model-search').value.trim().toLowerCase(),oldScroll=$('filters').scrollTop;
 let prs=[...new Set(catalogs().map(m=>m.provider))].sort((a,b)=>a.localeCompare(b));
 host.replaceChildren(...prs.filter(pr=>{const models=catalogs().filter(m=>m.provider===pr);return !s||pr.toLowerCase().includes(s)||models.some(m=>m.model.toLowerCase().includes(s))}).map(pr=>{
  const models=catalogs().filter(m=>m.provider===pr).sort((a,b)=>a.model.localeCompare(b.model));const sel=models.filter(m=>chosen.has(key(m))).length;
  const country=models[0]?.country||'Unknown';const section=document.createElement('section');section.className='company';
  const head=document.createElement('div');head.className='company-head';
  const exp=document.createElement('button');exp.className='expand';exp.type='button';exp.textContent=expanded.has(pr)?'▾':'▸';exp.setAttribute('aria-label','Expand '+pr);exp.addEventListener('click',()=>{expanded.has(pr)?expanded.delete(pr):expanded.add(pr);renderTree()});
  const chk=document.createElement('input');chk.type='checkbox';chk.checked=sel===models.length;chk.indeterminate=sel>0&&sel<models.length;chk.setAttribute('aria-label','All models for '+pr);chk.addEventListener('change',()=>{models.forEach(m=>chk.checked?chosen.add(key(m)):chosen.delete(key(m)));saveExclusions();rangeReset();renderAll();writeQuery()});
  const name=document.createElement('span');name.className='company-name';name.textContent=pr;
  const countryTag=document.createElement('span');countryTag.className='country';countryTag.textContent=country;
  const count=document.createElement('span');count.className='company-count';count.textContent=sel+'/'+models.length;
  head.append(exp,chk,name,countryTag,count);section.append(head);
  const children=document.createElement('div');children.className='children';children.hidden=!(expanded.has(pr)||Boolean(s));
  for(const m of models.filter(m=>!s||pr.toLowerCase().includes(s)||m.model.toLowerCase().includes(s))){const row=document.createElement('label');row.className='child';const cb=document.createElement('input');cb.type='checkbox';cb.checked=chosen.has(key(m));cb.setAttribute('aria-label','Model '+m.model);cb.addEventListener('change',()=>{cb.checked?chosen.add(key(m)):chosen.delete(key(m));saveExclusions();rangeReset();renderAll();writeQuery()});const title=document.createElement('span');title.textContent=m.model;title.title=m.model;row.append(cb,title);children.append(row)}
  section.append(children);return section;
 }));
 $('filter-total').textContent=chosen.size+'/'+catalogs().length;
 $('filters').scrollTop=oldScroll;
}
function svg(tag,attrs={},parent){const e=document.createElementNS($ns,tag);for(const [k,v] of Object.entries(attrs))e.setAttribute(k,String(v));if(parent)parent.append(e);return e}
function txt(parent,x,y,s,attrs={}){const t=svg('text',{x,y,...attrs},parent);t.textContent=s;return t}
function frontier(points){let high=-Infinity;return [...points].sort((a,b)=>a.cost-b.cost||b.score-a.score).filter(p=>{if(p.score>high+1e-8){high=p.score;return true}return false})}
function vendorShape(provider){
 const providers=['OpenAI','Anthropic','Google','xAI','Microsoft','GitHub','Alibaba','DeepSeek','Moonshot AI','MiniMax','Z.ai','ByteDance'];
 return ['circle','square','triangle','diamond','hexagon','cross','pentagon','star','chevron','octagon','triangle-down','plus'][Math.max(0,providers.indexOf(provider))%12];
}
function markerPath(shape,x,y,r=8){
 const reg=(n,turn=-Math.PI/2)=>Array.from({length:n},(_,i)=>[x+Math.cos(turn+2*Math.PI*i/n)*r,y+Math.sin(turn+2*Math.PI*i/n)*r]).map(([a,b],i)=>(i?'L':'M')+a.toFixed(2)+','+b.toFixed(2)).join(' ')+'Z';
 if(shape==='square')return `M${x-r},${y-r}h${2*r}v${2*r}h${-2*r}Z`;
 if(shape==='triangle')return reg(3);
 if(shape==='triangle-down')return reg(3,Math.PI/2);
 if(shape==='diamond')return reg(4,0);
 if(shape==='pentagon')return reg(5);
 if(shape==='hexagon')return reg(6,Math.PI/6);
 if(shape==='octagon')return reg(8,Math.PI/8);
 if(shape==='star')return Array.from({length:10},(_,i)=>[x+Math.cos(-Math.PI/2+i*Math.PI/5)*(i%2?r*.5:r),y+Math.sin(-Math.PI/2+i*Math.PI/5)*(i%2?r*.5:r)]).map(([a,b],i)=>(i?'L':'M')+a.toFixed(2)+','+b.toFixed(2)).join(' ')+'Z';
 if(shape==='cross'||shape==='plus')return `M${x-r*.3},${y-r}h${r*.6}v${r*.7}h${r*.7}v${r*.6}h${-r*.7}v${r*.7}h${-r*.6}v${-r*.7}h${-r*.7}v${-r*.6}h${r*.7}Z`;
 if(shape==='chevron')return `M${x-r},${y-r*.5}L${x},${y+r*.45}L${x+r},${y-r*.5}L${x+r*.55},${y-r}L${x},${y-r*.05}L${x-r*.55},${y-r}Z`;
 return reg(12);
}
function modelHue(provider,model){let h=2166136261;for(const c of provider+' '+model){h=Math.imul(h^c.charCodeAt(0),16777619)}return (Math.abs(h>>>0)%360);}
function baseColor(p){return `hsl(${modelHue(p.provider,p.model)},68%,55%)`}
function pointColor(p,low,high){const rank=(p.score-low)/Math.max(1,high-low);return `hsl(${modelHue(p.provider,p.model)},76%,${Math.round(37+30*rank)}%)`}
const effortOrder=['low','medium','high','xhigh','max','standard','default'];
function showSeries(s,series){for(const group of s.querySelectorAll('[data-series]'))group.classList.toggle('faded-series',group.dataset.series!==series);
 for(const group of s.querySelectorAll('[data-series]'))group.classList.toggle('emphasis-series',group.dataset.series===series);
}
function clearSeries(s){s.querySelectorAll('.faded-series,.emphasis-series').forEach(x=>x.classList.remove('faded-series','emphasis-series'));}
function graph(points){
 const host=$('chart-area');host.replaceChildren();
 if(!points.length){host.innerHTML='<p class="empty">No measured points in this range. Widen the axes or choose another benchmark.</p>';$('chart-legend').replaceChildren();return}
 const fs=Boolean(document.fullscreenElement||$('chart-card').classList.contains('fullscreen-fallback'));
 const w=Math.max(750,Math.round(host.clientWidth)||1200),height=fs?Math.max(430,Math.round(host.clientHeight)||600):Math.max(430,Math.min(720,Math.round(w*.52)));
 const plot={x:67,y:19,w:w-83,h:height-92};
 const s=svg('svg',{viewBox:`0 0 ${w} ${height}`,role:'img','aria-label':chart().label+' interactive plot',preserveAspectRatio:'xMidYMid meet'},host);
 svg('rect',{x:plot.x,y:plot.y,width:plot.w,height:plot.h,class:'svg-panel'},s);
 const xp=x=>plot.x+(scaleValue('x',x)-scaleValue('x',bounds.xmin))/(scaleValue('x',bounds.xmax)-scaleValue('x',bounds.xmin))*plot.w;
 const yp=y=>plot.y+plot.h-(y-bounds.ymin)/(bounds.ymax-bounds.ymin)*plot.h;
 const niceStep=v=>{const m=10**Math.floor(Math.log10(Math.max(v,1e-10)));return [1,2,2.5,5,10].map(k=>k*m).find(k=>k>=v)||10*m};
 let ticks=[];
 if(costScale==='log'){
  for(let e=Math.floor(Math.log10(bounds.xmin))-1;e<=Math.ceil(Math.log10(bounds.xmax))+1;e++)for(const factor of [1,2,5]){
    const v=factor*10**e;if(v>=bounds.xmin-1e-9&&v<=bounds.xmax+1e-9)ticks.push(v)
  }
  ticks=ticks.filter((v,i,arr)=>i===0||xp(v)-xp(arr[i-1])>66)
 }else{const step=niceStep((bounds.xmax-bounds.xmin)/7);for(let v=Math.ceil(bounds.xmin/step)*step;v<=bounds.xmax+1e-9;v+=step)ticks.push(v)}
 for(const v of ticks){const x=xp(v);svg('line',{x1:x,x2:x,y1:plot.y,y2:plot.y+plot.h,class:'svg-grid'},s);txt(s,x,plot.y+plot.h+24,money(v),{'text-anchor':'middle',class:'svg-tick'})}
 const ystep=niceStep((bounds.ymax-bounds.ymin)/7);
 for(let v=Math.ceil(bounds.ymin/ystep)*ystep;v<=bounds.ymax+1e-9;v+=ystep){const y=yp(v);svg('line',{x1:plot.x,x2:plot.x+plot.w,y1:y,y2:y,class:'svg-grid'},s);txt(s,plot.x-11,y+4,pct(v)+'%',{'text-anchor':'end',class:'svg-tick'})}
 txt(s,plot.x+plot.w/2,height-14,'Estimated cost / task (USD, '+costScale+')',{'text-anchor':'middle',class:'svg-axislabel'});
 const scoreAll=scored();const hi=Math.max(...scoreAll.map(p=>p.score)),lo=Math.min(...scoreAll.map(p=>p.score));
 const front=new Set(frontier(scoreAll));const best=points.filter(p=>front.has(p)).sort((a,b)=>a.cost-b.cost);
 if(best.length>1)svg('path',{d:best.map((p,i)=>(i?'L':'M')+xp(p.cost).toFixed(2)+','+yp(p.score).toFixed(2)).join(' '),class:'svg-frontier'},s);
 const groups=new Map();for(const p of points){const k=key(p);if(!groups.has(k))groups.set(k,[]);groups.get(k).push(p)}
 const layers=svg('g',{class:'series-root'},s),labelBoxes=[];
 for(const [id,series] of groups){
  const ordered=[...series].sort((a,b)=>effortOrder.indexOf(a.effort)-effortOrder.indexOf(b.effort));const p0=series[0];
  const family=svg('g',{'data-series':id,class:'model-series'},layers);
  const col=baseColor(p0);family.style.color=col;
  if(ordered.length>1)svg('path',{d:ordered.map((p,i)=>(i?'L':'M')+xp(p.cost).toFixed(2)+','+yp(p.score).toFixed(2)).join(' '),class:'effort-connector',stroke:col},family);
  for(const p of series){const x=xp(p.cost),y=yp(p.score),col=pointColor(p,lo,hi),shape=vendorShape(p.provider);
    const d=shape==='circle'?null:markerPath(shape,x,y,8);
    const dot=d?svg('path',{d,fill:col,stroke:'var(--plot)','stroke-width':1.3,class:'svg-point',tabindex:0,role:'button','aria-label':`${p.model} ${p.effort}: score ${p.score}, cost ${p.cost}`},family):svg('circle',{cx:x,cy:y,r:7.5,fill:col,stroke:'var(--plot)','stroke-width':1.3,class:'svg-point',tabindex:0,role:'button','aria-label':`${p.model} ${p.effort}: score ${p.score}, cost ${p.cost}`},family);
    dot.addEventListener('mouseenter',e=>{showSeries(s,id);showTip(p,e)});dot.addEventListener('mousemove',moveTip);dot.addEventListener('mouseleave',()=>{clearSeries(s);hideTip()});dot.addEventListener('focus',e=>{showSeries(s,id);showTip(p,e)});dot.addEventListener('blur',()=>{clearSeries(s);hideTip()});
    if(labelMode==='none'||paretoLabelsOnly&&!front.has(p))continue;
    const label=p.model+(p.effort&&p.effort!=='default'?' / '+p.effort:'');const tw=Math.min(280,label.length*7.2+4);
    let lx=Math.max(plot.x+5,Math.min(plot.x+plot.w-tw-3,x+10)),ly=Math.max(plot.y+17,Math.min(plot.y+plot.h-7,y-10));
    let occupied=false;for(let attempt=0;attempt<58;attempt++){
      occupied=labelBoxes.some(q=>lx<q.x+q.w+5&&lx+tw+5>q.x&&Math.abs(ly-q.y)<16);
      if(!occupied)break;
      const shift=(attempt+1)*14;ly=Math.max(plot.y+15,Math.min(plot.y+plot.h-5,y+(attempt%2?shift:-shift)))
    }
    if(!occupied){labelBoxes.push({x:lx,y:ly,w:tw});txt(family,lx,ly,label,{class:'svg-label',fill:col})}
  }
 }
 const legend=$('chart-legend');legend.replaceChildren();const providers=[...new Set(points.map(p=>p.provider))].sort();
 const makeLegend=(label,title)=>{const group=document.createElement('span');group.className='legend-section';const h=document.createElement('b');h.textContent=title;group.append(h);legend.append(group);return group};
 const vendorLegend=makeLegend('vendor','Vendors');for(const pr of providers){const e=document.createElement('span');e.className='legend-item';const sample=document.createElementNS($ns,'svg');sample.setAttribute('viewBox','0 0 28 28');const shape=vendorShape(pr);const p=points.find(x=>x.provider===pr);if(shape==='circle')svg('circle',{cx:14,cy:14,r:8,fill:baseColor(p)},sample);else svg('path',{d:markerPath(shape,14,14,9),fill:baseColor(p)},sample);e.append(sample,document.createTextNode(pr));vendorLegend.append(e)}
 const modelLegend=makeLegend('models','Models');for(const [id,series] of groups){const p=series[0],e=document.createElement('span');e.className='legend-item';const sw=document.createElement('i');sw.style.background=baseColor(p);e.append(sw,document.createTextNode(p.model));modelLegend.append(e)}
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
function renderBenchmarkOptions(){
 const benchmarks=[...new Set(charts().map(c=>c.benchmark))];const sel=$('benchmark-picker');sel.replaceChildren();
 const aa=document.createElement('optgroup');aa.label='Artificial Analysis (AA)';
 const others=document.createElement('optgroup');others.label='Other benchmarks';
 for(const b of benchmarks){const o=document.createElement('option');o.value=b;o.textContent=b;(b.startsWith('AA ')?aa:others).append(o)}
 if(aa.children.length)sel.append(aa);if(others.children.length)sel.append(others);renderSnapshotOptions();
}
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
function attachEvents(){
 document.querySelectorAll('.platform-btn').forEach(b=>b.addEventListener('click',()=>choosePlatform(b.dataset.platform)));
 $('platform-full').addEventListener('change',e=>choosePlatform(e.target.value));
 $('benchmark-picker').addEventListener('change',e=>{const c=latestChart(charts().filter(c=>c.benchmark===e.target.value));if(c)setChart(c.id)});
 $('snapshot-picker').addEventListener('change',e=>setChart(e.target.value));
 document.querySelectorAll('input[name="cost-scale"]').forEach(r=>r.addEventListener('change',e=>{if(e.target.checked)setCostScale(e.target.value)}));
 $('label-mode').addEventListener('change',e=>{labelMode=e.target.checked?'on':'none';renderContent();writeQuery()});
 $('pareto-labels').addEventListener('change',e=>{paretoLabelsOnly=e.target.checked;renderContent();writeQuery()});
 $('range-mode').addEventListener('change',e=>{rangeMode=e.target.value;rangeReset();renderContent();writeQuery()});
 $('point-mode').addEventListener('change',e=>{pointMode=e.target.value;renderContent();writeQuery()});
 $('model-search').addEventListener('input',renderTree);
 $('collapse-all').addEventListener('click',()=>{expanded.clear();renderTree()});
 $('expand-all').addEventListener('click',()=>{expanded=new Set(catalogs().map(m=>m.provider));renderTree()});
 function changeSelection(){saveExclusions();rangeReset();renderAll();writeQuery()}
 $('select-all').addEventListener('click',()=>{chosen=new Set(catalogs().map(key));changeSelection()});
 $('exclude-china').addEventListener('click',()=>{chosen=new Set(catalogs().filter(m=>m.country!=='CN').map(key));changeSelection()});
 $('reset-range').addEventListener('click',()=>{rangeReset();renderContent();writeQuery()});
 $('export-action').addEventListener('click',exportFile);
 $('fullscreen-toggle').addEventListener('click',fullscreenToggle);
 document.addEventListener('fullscreenchange',()=>{$('fullscreen-toggle').textContent=document.fullscreenElement?'✕ Exit fullscreen':'⛶ Fullscreen';renderContent()});
 bindAxes();bindSidebar();
 let oldW=0,oldH=0;
 const obs=new ResizeObserver(entries=>{const box=entries[0]?.contentRect;if(!box)return;if(Math.abs(box.width-oldW)<12&&Math.abs(box.height-oldH)<12)return;oldW=box.width;oldH=box.height;if(!draggingAxis)requestAnimationFrame(()=>{if(db)renderContent()})});
 obs.observe($('chart-area'));
}
async function main(){try{
 const res=await fetch('./data.json',{cache:'no-store'});if(!res.ok)throw Error('HTTP '+res.status);
 db=await res.json();if(!db.catalog?.length||!db.charts?.length)throw Error('Missing catalog data');
 attachEvents();const q=new URLSearchParams(location.search);
 choosePlatform(['Copilot','Kiro','Claude Code'].includes(q.get('agent'))?q.get('agent'):'Copilot',true);
 restoreQuery(q);
 }catch(e){$('chart-area').textContent='Data unavailable: '+e.message;console.error(e)}
}
main();