'use strict';
const data=window.CS_DATA;
const $=id=>document.getElementById(id);
const esc=s=>String(s??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const courseById=Object.fromEntries(data.courses.map(c=>[c.id,c]));
let bookmarks=[];try{bookmarks=JSON.parse(localStorage.getItem('cs-atlas-saved')||'[]');if(!Array.isArray(bookmarks))bookmarks=[];}catch{}
let selected='AI',selectedUnit=null,filtered=[];
const expandedAreas=new Set();
const allUnits=data.areas.flatMap(a=>a.units.map(u=>({...u,area:a})));
const unitById=new Map(allUnits.map(u=>[u.id,u]));
function selectUnit(id){const unit=unitById.get(id);if(!unit)return;selected=unit.area.id;selectedUnit=id;expandedAreas.add(selected);}
function syncDetailRoute(replace=false){if(!selected)return;const hash=selectedUnit?'#unit/'+encodeURIComponent(selectedUnit):'#area/'+encodeURIComponent(selected);if(location.hash!==hash)history[replace?'replaceState':'pushState'](null,'',hash);}
$('courseCount').textContent=data.courses.length;
[...new Set(data.areas.map(a=>a.group))].forEach(g=>$('group').add(new Option(g,g)));
function matches(a,u){const q=$('search').value.trim().toLowerCase();const linked=u.courseIds.map(id=>courseById[id]?.name+' '+id).join(' ');return (!$('group').value||a.group===$('group').value)&&(!$('core').checked||u.isCore)&&(!$('saved').checked||bookmarks.includes(u.id))&&(!q||[a.id,a.name,a.english,u.id,u.name,u.zh,linked].join(' ').toLowerCase().includes(q));}
function render(){
 const order=['数据与智能','基础与理论','系统与计算','人与软件'];
 filtered=data.areas.map(a=>({...a,visibleUnits:a.units.filter(u=>matches(a,u))})).filter(a=>a.visibleUnits.length).sort((a,b)=>order.indexOf(a.group)-order.indexOf(b.group));
 const count=filtered.reduce((n,a)=>n+a.visibleUnits.length,0);
 $('resultStatus').textContent=`当前匹配 ${filtered.length} 个知识领域 · ${count} 个知识单元 · 收藏 ${bookmarks.length} 个单元`;
 if(!filtered.some(a=>a.id===selected)){selected=filtered[0]?.id;selectedUnit=null;if(selected)expandedAreas.add(selected);}
 if(selectedUnit&&!filtered.find(a=>a.id===selected)?.visibleUnits.some(u=>u.id===selectedUnit))selectedUnit=null;
 let group='';$('tree').innerHTML=filtered.length?filtered.map(a=>{const head=group!==a.group?`<p class="groupname">${esc(a.group)}</p>`:'';group=a.group;return `${head}<div class="area-item"><button class="area-button ${selected===a.id?'active':''}" data-area="${a.id}" aria-expanded="${expandedAreas.has(a.id)}"><img class="arrow-icon" src="assets/icons/chevron.svg" width="16" height="16" alt="" aria-hidden="true"><span class="abbr">${a.id}</span>${esc(a.name)}<span class="count">${a.visibleUnits.length}</span></button>${expandedAreas.has(a.id)?`<div class="units">${a.visibleUnits.map(u=>`<button class="unit-button ${u.id===selectedUnit?'active':''}" data-unit="${u.id}">${bookmarks.includes(u.id)?'★ ':''}${esc(u.zh)}</button>`).join('')}</div>`:''}</div>`}).join(''):'<div class="empty">没有匹配的知识单元<br>试试清空搜索或取消筛选</div>';
 renderDetail();
 document.querySelectorAll('[data-area-shortcut]').forEach(button=>{
  button.dataset.expanded=String(expandedAreas.has(button.dataset.areaShortcut));
  button.removeAttribute('aria-current');
 });
}
function courseTable(ids){const courses=[...new Set(ids)].map(id=>courseById[id]).filter(Boolean);return courses.length?`<table class="course-table"><thead><tr><th>课程代码</th><th>交大课程</th><th>学分</th><th>建议修读</th></tr></thead><tbody>${courses.map(c=>`<tr><td>${c.id}</td><td><a href="${esc(c.source)}" target="_blank" rel="noopener">${esc(c.name)} <img class="arrow-icon" src="assets/icons/external.svg" width="16" height="16" alt="" aria-hidden="true"></a><br><small>${esc(c.type)}</small></td><td>${c.credits}</td><td>大${c.year} / ${c.semester}学期</td></tr>`).join('')}</tbody></table>`:'<p class="mapping-note">当前选取的2026级课程表中未找到可直接确认的学习入口，保留待核验，不推定学校未开设该课程。</p>';}
function renderDetail(){const a=filtered.find(a=>a.id===selected);if(!a){$('detail').innerHTML='<div class="empty"><h3>暂时没有匹配结果</h3><p>搜索内容不会改变原始数据；点击“重置筛选”即可恢复。</p></div>';return;}
const u=a.visibleUnits.find(u=>u.id===selectedUnit);
if(u){$('detail').innerHTML=`<button class="breadcrumb textbutton" id="backArea"><img class="arrow-icon" src="assets/icons/back.svg" width="16" height="16" alt="" aria-hidden="true"> ${esc(a.name)} / ${a.id}</button><div class="detail-top"><div><span class="tag">${u.id}</span><h2>${esc(u.zh)}</h2></div><button class="star" id="saveUnit" aria-label="${bookmarks.includes(u.id)?'取消收藏':'收藏'}知识单元">${bookmarks.includes(u.id)?'★':'☆'}</button></div><p class="en">${esc(u.name)}</p><p class="description">所属知识领域：${esc(a.name)}。${esc(a.description)}</p><div class="hoursbox"><div><span>CS Core 原表学时</span><strong>${esc(u.coreHours||'未列独立学时')}</strong></div><div><span>KA Core 原表学时</span><strong>${esc(u.kaHours||'未列独立学时')}</strong></div></div><p class="smallnote">括号内为跨领域复用学时；“Included in SEP hours”表示计入SEP，不能重复累加。未列学时不代表该知识单元不重要。</p><a class="source-link" target="_blank" rel="noopener" href="${esc(u.source)}">阅读官方知识单元 · 报告第${u.page}页 <img class="arrow-icon" src="assets/icons/external.svg" width="16" height="16" alt="" aria-hidden="true"></a><h3 class="subhead">典型课程与交大学习入口</h3>${courseTable(u.courseIds)}<p class="mapping-note">${esc(u.mappingNote)}</p>`;
$('backArea').onclick=()=>{selectedUnit=null;render();syncDetailRoute()};$('saveUnit').onclick=()=>{bookmarks=bookmarks.includes(u.id)?bookmarks.filter(x=>x!==u.id):[...bookmarks,u.id];try{localStorage.setItem('cs-atlas-saved',JSON.stringify(bookmarks));notify('收藏已保存在此浏览器')}catch{notify('浏览器未允许保存，收藏仅在本次会话有效')}render();syncDetailRoute(true)};
}else{$('detail').innerHTML=`<div class="detail-top"><div><span class="tag">${a.id}</span><span class="tag">${esc(a.group)}</span><h2>${esc(a.name)}</h2></div><span class="badge">${a.visibleUnits.length} / ${a.units.length} KU</span></div><p class="en">${esc(a.english)}</p><p class="description">${esc(a.description)}</p><div class="badge">领域CS Core ${a.hours}小时 · KA Core ${a.kaHours??'未单列'}${a.kaHours!==null?'小时':''} · 点击单元查看课程</div><div class="unitgrid">${a.visibleUnits.map(u=>`<button class="unitcard" data-unit="${u.id}"><span class="tiny">${u.id}</span><b>${esc(u.zh)}</b><small>${u.isCore?'含本KA的CS Core学时':'KA Core / 选修 / 跨领域内容'} ${bookmarks.includes(u.id)?'★':''}</small></button>`).join('')}</div><h3 class="subhead">领域关联的交大课程</h3>${courseTable(a.courseIds)}`;}}
$('tree').addEventListener('click',e=>{
 const b=e.target.closest('button');if(!b)return;
 const areaId=b.dataset.area,unitId=b.dataset.unit;
 if(areaId){
  if(expandedAreas.has(areaId))expandedAreas.delete(areaId);else expandedAreas.add(areaId);
  selected=areaId;selectedUnit=null;
 }
 if(unitId)selectUnit(unitId);
 render();
 syncDetailRoute();
 const selector=areaId?'[data-area="'+areaId+'"]':'[data-unit="'+unitId+'"]';
 $('tree').querySelector(selector)?.focus({preventScroll:true});
});
$('detail').addEventListener('click',e=>{const b=e.target.closest('[data-unit]');if(b){selectUnit(b.dataset.unit);render();syncDetailRoute()}});
['search','group','core','saved'].forEach(id=>$(id).addEventListener(id==='search'?'input':'change',()=>{if(id==='group'&&$('group').value){expandedAreas.clear();data.areas.filter(a=>a.group===$('group').value).forEach(a=>expandedAreas.add(a.id));}render();syncDetailRoute(true)}));
function resetFilters(areaId='AI'){$('search').value='';$('group').value='';$('core').checked=false;$('saved').checked=false;selected=areaId;selectedUnit=null;expandedAreas.add(areaId);render();}
$('reset').onclick=()=>{resetFilters();syncDetailRoute()};
document.querySelector('.orbit').addEventListener('click',event=>{
 const button=event.target.closest('button');
 if(!button)return;
 const area=data.areas.find(a=>a.id===button.dataset.areaShortcut);
 if(!area)return;
 expandedAreas.clear();
 resetFilters(area.id);
 $('orbitStatus').textContent=`${area.id} · ${area.name}`;
 syncDetailRoute();
 const target=$('detail');
 target.focus({preventScroll:true});
 target.scrollIntoView({block:'start',behavior:'auto'});
 notify(`已打开${area.name}，显示该领域全部知识单元`);
});
$('bars').innerHTML=[...data.areas].sort((a,b)=>b.hours-a.hours).map(a=>`<div class="barrow" title="${esc(a.name)}：${a.hours}小时"><span class="label">${a.id}</span><div class="track"><div class="bar" style="width:${a.hours/55*100}%"></div></div><b>${a.hours}</b></div>`).join('');
function notify(t){$('toast').textContent=t;$('toast').style.display='block';setTimeout(()=>$('toast').style.display='none',2500)}
$('export').onclick=()=>{const rows=[['KA','领域','KU','知识单元','CS Core原表','KA Core原表','交大课程学习入口','原文来源','访问日期'],...filtered.flatMap(a=>a.visibleUnits.map(u=>[a.id,a.name,u.id,u.zh,u.coreHours,u.kaHours,u.courseIds.join(';'),u.source,data.version]))];const csv='\ufeff'+rows.map(r=>r.map(x=>'"'+String(x).replace(/"/g,'""')+'"').join(',')).join('\r\n');const url=URL.createObjectURL(new Blob([csv],{type:'text/csv;charset=utf-8'}));const link=document.createElement('a');link.href=url;link.download='cs2023-filtered.csv';link.click();setTimeout(()=>URL.revokeObjectURL(url),1000);notify('已导出当前筛选的知识单元')};
render();

// Pause across the orbit column for the full hero image height.
(() => {
 const hero=document.querySelector('.hero'),orbit=document.querySelector('.orbit');
 hero.addEventListener('pointermove',event=>{
  if(event.pointerType==='touch')return;
  const bounds=orbit.getBoundingClientRect(),imageBounds=hero.getBoundingClientRect();
  hero.classList.toggle('orbit-paused',event.clientX>=bounds.left&&event.clientX<=bounds.right&&event.clientY>=imageBounds.top&&event.clientY<=imageBounds.bottom);
 });
 hero.addEventListener('pointerleave',()=>hero.classList.remove('orbit-paused'));
})();
