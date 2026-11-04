'use strict';
(() => {
 const groups=['数据与智能','基础与理论','系统与计算','人与软件'];
 function applyRoute(focus=true){
  const match=/^#(area|unit|group)\/(.+)$/.exec(location.hash);
  if(!match)return false;
  let id;try{id=decodeURIComponent(match[2]);}catch{return false;}
  const kind=match[1],unit=kind==='unit'?unitById.get(id):null;
  const area=kind==='unit'?unit?.area:kind==='area'?data.areas.find(a=>a.id===id):data.areas.find(a=>a.group===id);
  if(!area||(kind==='group'&&!groups.includes(id)))return false;
  $('search').value='';$('group').value=kind==='group'?id:'';$('core').checked=false;$('saved').checked=false;
  selected=area.id;selectedUnit=unit?.id||null;if(kind==='group'){expandedAreas.clear();data.areas.filter(a=>a.group===id).forEach(a=>expandedAreas.add(a.id));}else expandedAreas.add(area.id);render();
  const target=kind==='group'?$('explore'):$('detail');
  requestAnimationFrame(()=>{if(focus)target.focus({preventScroll:true});target.scrollIntoView({block:'start',behavior:'auto'});});
  return true;
 }
 window.addEventListener('hashchange',()=>applyRoute());
 applyRoute(false);
})();
