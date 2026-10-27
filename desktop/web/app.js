'use strict';

const paths = {
  grid:'M3 3h7v7H3zM14 3h7v7h-7zM3 14h7v7H3zM14 14h7v7h-7z',
  star:'m12 3 2.8 5.7 6.2.9-4.5 4.4 1.1 6.2-5.6-3-5.6 3 1.1-6.2L3 9.6l6.2-.9L12 3Z',
  clock:'M12 8v5l3 2M21 12a9 9 0 1 1-18 0 9 9 0 0 1 18 0',
  taste:'m12 3 2.6 6.4L21 12l-6.4 2.6L12 21l-2.6-6.4L3 12l6.4-2.6L12 3Z',
  ui:'M3 5h18v14H3zM3 9h18M8 9v10',
  code:'m8 7-5 5 5 5m8-10 5 5-5 5m-3-13-2 16',
  folder:'M3 7h7l2 2h9v11H3zM3 7V4h7l2 3h9v2',
  search:'M17 17l4 4M19 10.5a8.5 8.5 0 1 1-17 0 8.5 8.5 0 0 1 17 0',
  refresh:'M20 7v5h-5M4 17v-5h5M6.1 6.1A8 8 0 0 1 20 12M4 12a8 8 0 0 0 13.9 5.9',
  sort:'M5 4v16m-3-3 3 3 3-3M11 5h10M11 10h7M11 15h4',
  copy:'M9 8h12v13H9zM15 8V3H3v13h6',
  download:'M12 3v12m-5-5 5 5 5-5M4 16v5h16v-5',
  external:'M14 3h7v7m-1-6-9 9M10 3H3v18h18v-7',
  back:'m14 6-6 6 6 6', plus:'M12 5v14M5 12h14', check:'m5 12 4 4L19 6',
};
const icon = name => `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="${paths[name] || paths.folder}"/></svg>`;
const $ = id => document.getElementById(id);
const state = {entries:[],categories:[],favorites:[],view:'all',category:'all',query:'',sort:'updated',selected:null,detail:null,tab:'optimized',expanded:false,request:0};
const categoryIcon = id => ({taste:'taste',ui_design:'ui',development:'code'})[id] || 'folder';
const categoryName = id => state.categories.find(c=>c.id===id)?.name || '待分类';
const escapeHTML = value => String(value ?? '').replace(/[&<>"']/g, char=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[char]));
const dateLabel = value => {const date = new Date(value); return Number.isNaN(date.valueOf()) ? '日期未知' : date.toLocaleDateString('zh-CN',{timeZone:'Asia/Shanghai',year:'numeric',month:'2-digit',day:'2-digit'});};
const safeURL = value => {try {const url = new URL(value,location.origin); return ['http:','https:'].includes(url.protocol)&&(value.startsWith('http')||(/^\/\?entry=PRM-\d+/.test(value)&&url.origin===location.origin))?url.href:null;}catch{return null;}};

async function api(path, options={}) {
  let response;
  try {response = await fetch(path,options);}
  catch {throw new Error('无法连接本机素材库。请重新启动留白，再点击重试或刷新；已保存的素材仍在本机。');}
  let data;
  try {data = await response.json();}
  catch {throw new Error('本机服务返回了无法识别的内容，请重启留白后重试。');}
  if (!response.ok) throw new Error(data.error || '暂时无法读取素材');
  return data;
}

let toastTimer;
function toast(message) {$('toast').textContent=message; $('toast').hidden=false; clearTimeout(toastTimer); toastTimer=setTimeout(()=>$('toast').hidden=true,3000);}
function error(message) {$('error-banner').textContent=message; $('error-banner').hidden=!message;}
function putIcons(root=document){root.querySelectorAll('[data-icon]').forEach(node=>node.innerHTML=icon(node.dataset.icon));}

function filteredEntries() {
  const query=state.query.toLocaleLowerCase().trim();
  let rows=state.entries.filter(e=>(state.category==='all'||e.category_id===state.category)&&(state.view!=='favorites'||state.favorites.includes(e.id)));
  if(query){const words=query.split(/\s+/); rows=rows.filter(e=>{const text=[e.title,e.summary,e.id,e.tags.join(' '),categoryName(e.category_id),e.search_text].join(' ').toLocaleLowerCase(); return words.every(word=>text.includes(word));});}
  if(state.sort==='title')rows.sort((a,b)=>a.title.localeCompare(b.title,'zh-CN'));
  else if(state.sort==='recent')rows.sort((a,b)=>String(b.created_at||'').localeCompare(String(a.created_at||''))||b.id.localeCompare(a.id));
  else rows.sort((a,b)=>String(b.updated_at||b.created_at||'').localeCompare(String(a.updated_at||a.created_at||''))||b.id.localeCompare(a.id));
  return rows;
}

function renderNavigation() {
  const count=id=>state.entries.filter(e=>e.category_id===id).length;
  const navButton=(label,glyph,num,active,kind,value)=>`<button class="nav-button ${active?'active':''}" data-${kind}="${value}" ${active?'aria-current="page"':''}><span class="icon">${icon(glyph)}</span><span>${escapeHTML(label)}</span><span class="count">${num}</span></button>`;
  $('space-nav').innerHTML=[['全部素材','grid',state.entries.length,'all'],['我的收藏','star',state.favorites.length,'favorites'],['最近收录','clock',state.entries.length,'recent']].map(([label,glyph,num,value])=>navButton(label,glyph,num,state.view===value&&state.category==='all','view',value)).join('');
  const activeCategories=state.categories.filter(c=>count(c.id)>0);
  const shown=state.expanded?state.categories:activeCategories;
  $('category-nav').innerHTML=shown.map(c=>navButton(c.name,categoryIcon(c.id),count(c.id),state.category===c.id,'category',c.id)).join('');
  $('category-total').textContent=state.categories.length;
  $('more-categories').innerHTML=`${state.expanded?'收起空分类':'查看全部分类'} <span>${state.expanded?'⌃':'⌄'}</span>`;
  $('more-categories').setAttribute('aria-expanded',String(state.expanded));
  $('quick-filters').innerHTML=[{id:'all',name:'全部'},...activeCategories].map(c=>`<button class="filter-chip ${state.category===c.id?'active':''}" data-category="${c.id}" aria-pressed="${state.category===c.id}">${escapeHTML(c.name)}<span class="chip-count">${c.id==='all'?state.entries.length:count(c.id)}</span></button>`).join('');
  $('mobile-browse').innerHTML='<optgroup label="我的素材"><option value="view:all">全部素材</option><option value="view:favorites">我的收藏</option><option value="view:recent">最近收录</option></optgroup><optgroup label="全部分类">'+state.categories.map(c=>`<option value="category:${escapeHTML(c.id)}">${escapeHTML(c.name)} · ${count(c.id)}</option>`).join('')+'</optgroup>';
  $('mobile-browse').value=state.category==='all'?'view:'+state.view:'category:'+state.category;
}

function emptyCollection() {
  if(state.query.trim())return '<div class="empty-list"><strong>没有找到相关素材</strong><p>换个关键词，或查看全部素材。</p><button class="reference-button" data-action="clear-filters">清空筛选</button></div>';
  if(state.view==='favorites')return '<div class="empty-list"><strong>还没有收藏</strong><p>打开素材后，点击星标收藏。</p><button class="reference-button" data-action="clear-filters">浏览全部素材</button></div>';
  const first=state.entries.length===0&&state.category==='all';
  return `<div class="empty-list welcome-empty"><span class="empty-symbol">${icon('folder')}</span><strong>${first?'保存你的第一条提示词':'这个分类还没有素材'}</strong><p>粘贴原文或导入文件，选择分类后保存到本机。</p><div class="empty-actions"><button class="reference-button primary" data-prompt-action="new">${first?'保存第一条素材':'新建素材'}</button><button class="reference-button" data-prompt-action="import">导入文本文件</button></div></div>`;
}

function renderList() {
  const rows=filteredEntries();
  const title=state.category!=='all'?categoryName(state.category):({all:'全部素材',favorites:'我的收藏',recent:'最近收录'}[state.view]);
  $('view-title').replaceChildren(document.createTextNode(title));
  const badge=document.createElement('span');badge.id='title-count';badge.textContent=rows.length;$('view-title').append(badge);
  $('result-count').textContent=`${rows.length} 条素材${state.query?' · 搜索结果':''}`;
  $('footer-count').textContent=`${state.entries.length} 条已留存 / ${state.categories.length} 个分类`;
  $('entry-list').innerHTML=rows.length?rows.map(e=>`<button class="entry-card ${state.selected===e.id?'selected':''}" data-entry="${e.id}" aria-pressed="${state.selected===e.id}" aria-label="${escapeHTML(e.id+' '+e.title)}"><div class="entry-card-top"><span class="entry-category">${icon(categoryIcon(e.category_id))}${escapeHTML(categoryName(e.category_id))}</span><span class="entry-id">${e.id.replace('PRM-','#')}</span></div><h3>${escapeHTML(e.title)}</h3>${String(e.summary||'').trim()?`<p>${escapeHTML(e.summary)}</p>`:''}<div class="entry-card-bottom">${e.tags.slice(0,2).map(t=>`<span class="tiny-tag">${escapeHTML(t)}</span>`).join('')}${state.favorites.includes(e.id)?`<span class="saved-star">${icon('star')}</span>`:''}</div></button>`).join(''):emptyCollection();
  document.querySelector('.workspace').classList.toggle('is-empty',rows.length===0);
  if(!rows.some(e=>e.id===state.selected)) {
    if(rows.length)selectEntry(rows[0].id,false);
    else {state.selected=null;state.detail=null;state.request++;$('detail-pane').replaceChildren();$('detail-pane').setAttribute('aria-busy','false');document.querySelector('.workspace').classList.remove('show-detail');}
  }
}

function updateView(){renderNavigation();renderList();window.ReferenceLibrary?.decorateNavigation();}

function returnToList() {
  document.querySelector('.workspace').classList.remove('show-detail');
  const selected=Array.from(document.querySelectorAll('[data-entry]')).find(node=>node.dataset.entry===state.selected);
  (selected||$('search')).focus({preventScroll:true});
}

async function selectEntry(id, reveal=true, version=null, tab='optimized') {
  state.selected=id;state.detail=null;state.tab=tab;const request=++state.request;
  $('detail-pane').setAttribute('aria-busy','true');
  $('detail-pane').innerHTML='<div id="detail-loading" class="detail-message" tabindex="-1"><p role="status">正在读取素材…</p><button class="reference-button mobile-back" data-action="back">返回素材列表</button></div>';
  document.querySelectorAll('[data-entry]').forEach(node=>{node.classList.toggle('selected',node.dataset.entry===id);node.setAttribute('aria-pressed',String(node.dataset.entry===id));});
  if(reveal){document.querySelector('.workspace').classList.add('show-detail');if(matchMedia('(max-width:900px)').matches)$('detail-loading').focus({preventScroll:true});}
  try {const detail=await api('/api/entries/'+encodeURIComponent(id)+(version?'?version='+encodeURIComponent(version):''));if(request!==state.request)return;state.detail=detail;renderDetail();if(reveal&&matchMedia('(max-width:900px)').matches&&document.querySelector('.workspace').classList.contains('show-detail'))$('detail-title')?.focus({preventScroll:true});}
  catch(e){if(request!==state.request)return;$('detail-pane').innerHTML=`<div id="detail-error" class="detail-message" tabindex="-1"><p role="alert">${escapeHTML(e.message)}</p><div class="empty-actions"><button class="reference-button" data-action="retry-detail" data-version="${escapeHTML(version||'')}">重试</button><button class="reference-button mobile-back" data-action="back">返回素材列表</button></div></div>`;if(reveal&&document.querySelector('.workspace').classList.contains('show-detail'))$('detail-error').focus({preventScroll:true});}
  finally{if(request===state.request)$('detail-pane').setAttribute('aria-busy','false');}
}

// 素材来自外部仓库：只生成受控 DOM，不把原文当 HTML 执行。
function inline(parent,text) {
  const regex=/(\*\*([^*]+)\*\*|`([^`]+)`|\[([^\]]+)\]\(([^)]+)\))/g;let offset=0;
  for(const match of text.matchAll(regex)){
    parent.append(document.createTextNode(text.slice(offset,match.index)));
    let node;
    if(match[2]){node=document.createElement('strong');node.textContent=match[2];}
    else if(match[3]){node=document.createElement('code');node.textContent=match[3];}
    else {const url=safeURL(match[5]);node=document.createElement(url?'a':'span');node.textContent=match[4];if(url){node.href=url;node.target='_blank';node.rel='noopener noreferrer';}}
    parent.append(node);offset=match.index+match[0].length;
  }
  parent.append(document.createTextNode(text.slice(offset)));
}

function markdown(text) {
  const root=document.createElement('div');root.className='reading';const lines=text.split(/\r?\n/);let code=null;let list=null;let table=null;
  for(const line of lines){
    if(line.trim().startsWith('```')){if(code){root.append(code);code=null;}else{code=document.createElement('pre');}list=null;table=null;continue;}
    if(code){code.textContent+=line+'\n';continue;}
    if(!line.trim()){list=null;table=null;continue;}
    if(/^\|/.test(line)){
      if(/^\|[\s:|\-]+\|\s*$/.test(line))continue;
      if(!table){table=document.createElement('table');root.append(table);}
      const row=document.createElement('tr');const tag=table.childElementCount?'td':'th';line.trim().replace(/^\||\|$/g,'').split('|').forEach(t=>{const cell=document.createElement(tag);inline(cell,t.trim());row.append(cell);});table.append(row);continue;
    }
    table=null;
    const heading=line.match(/^(#{1,3})\s+(.*)$/);
    if(heading){const node=document.createElement('h'+heading[1].length);inline(node,heading[2]);root.append(node);list=null;continue;}
    const bullet=line.match(/^\s*(?:[-*]|\d+\.)\s+(.*)$/);
    if(bullet){if(!list){list=document.createElement('ul');root.append(list);}const li=document.createElement('li');inline(li,bullet[1]);list.append(li);continue;}
    list=null;const node=document.createElement(line.startsWith('>')?'blockquote':'p');inline(node,line.replace(/^>\s?/,''));root.append(node);
  }
  if(code)root.append(code);return root;
}

const tabs=[['optimized','优化版'],['original','原文'],['analysis','设计逻辑'],['loop','Loop'],['source','来源']];
function renderDetail() {
  const d=state.detail;if(!d)return;const e=d.item,r=d.record;const saved=state.favorites.includes(e.id);
  const selectedVersion=d.selected_version||e.latest_version;
  const versionRecord=(r.versions||[]).find(v=>v.version===selectedVersion);
  const notOptimized=versionRecord?.optimization_status==='not_optimized';
  const optimizedLabel=versionRecord?.public_template?'中文复用版':notOptimized?'保存版':'优化版';
  queueMicrotask(()=>{window.ReferenceLibrary?.renderRelated(e.id);window.PromptEditor?.decorateDetail();});
  $('detail-pane').innerHTML=`<div class="detail-header"><div class="detail-topline"><div class="detail-controls"><button class="icon-button mobile-back" data-action="back" aria-label="返回素材列表">${icon('back')}</button><div class="detail-symbol">${icon(categoryIcon(e.category_id))}</div></div><div class="detail-controls"><button class="icon-button ${saved?'saved':''}" data-action="favorite" aria-label="${saved?'取消收藏':'收藏这条素材'}" aria-pressed="${saved}">${icon('star')}</button><button class="icon-button" data-action="download" aria-label="导出${state.tab==='original'?'原文':optimizedLabel} Markdown">${icon('download')}</button></div></div><h2 id="detail-title" tabindex="-1">${escapeHTML(e.title)}</h2>${String(e.summary||'').trim()?`<p class="detail-summary">${escapeHTML(e.summary)}</p>`:''}<div class="detail-meta"><span class="meta-tag">${escapeHTML(categoryName(e.category_id))}</span><span>${e.id}</span><span class="meta-dot"></span><span>${dateLabel(e.created_at)}</span><span class="meta-dot"></span><span>${notOptimized?'尚未优化':e.evaluation_status==='untested'?'待实测':'查看评测记录'}</span></div></div><div class="detail-tabs" role="tablist" aria-label="素材内容">${tabs.map(([value,label])=>`<button id="tab-${value}" class="detail-tab ${state.tab===value?'active':''}" role="tab" aria-selected="${state.tab===value}" aria-controls="detail-content" tabindex="${state.tab===value?'0':'-1'}" data-tab="${value}">${value==='optimized'?optimizedLabel:label}</button>`).join('')}</div><div id="detail-content" class="detail-content" role="tabpanel" aria-labelledby="tab-${state.tab}" tabindex="0"></div><div class="detail-bottom"><button class="copy-button" data-action="copy">${icon('copy')}<span>${state.tab==='optimized'?'复制提示词':state.tab==='loop'?'复制 Loop':'复制'+tabs.find(t=>t[0]===state.tab)[1]}</span></button></div>`;
  const content=$('detail-content');
  if(['optimized','original'].includes(state.tab)){
    const versions=r.versions||[];
    const versionControl=state.tab==='optimized'&&versions.length>1?`<label class="personal-version-picker"><span>优化版本</span><select id="personal-version" aria-label="优化版本">${versions.map(v=>`<option value="${escapeHTML(v.version)}" ${v.version===selectedVersion?'selected':''}>${escapeHTML(v.version)}${v.version===e.latest_version?' · 最新':''}</option>`).join('')}</select></label>`:`<span class="version-pill">${state.tab==='optimized'?escapeHTML(selectedVersion):'ORIGINAL'}</span>`;
    const caption=document.createElement('div');caption.className='content-caption';caption.innerHTML=`<span>${state.tab==='optimized'?(notOptimized?'原文副本 · 尚未优化':'可直接复制 · 填写变量后使用'):'完整原文 · 原始内容留存'}</span>${versionControl}`;
    const pre=document.createElement('pre');pre.className='prompt-text '+(state.tab==='original'?'original':'');pre.textContent=d[state.tab];content.append(caption,pre);
  }else if(state.tab==='analysis'){
    if(d.analysis){content.append(markdown(d.analysis));}
    else {const message=document.createElement('p');message.className='empty-detail';message.textContent=d.teaching_status==='version_mismatch'?'这份正文或版本已变化，教学拆解尚未更新。':d.teaching_status==='unavailable'?'教学文件暂时无法读取，原文和保存版仍可使用。':'这条素材还没有教学拆解。保存提示词不会自动生成分析。';content.append(message);}
  }else if(state.tab==='loop'){
    const loop=d.loop;content.innerHTML=`<div class="content-caption"><span>有边界的迭代</span><span class="version-pill">${loop.explicit_loop_present?'已写入优化版':'附加建议'}</span></div><div class="loop-facts"><div class="loop-fact"><small>使用方式</small><strong>${loop.applicability==='conditional'?'按任务条件启用':'查看适用条件'}</strong></div><div class="loop-fact"><small>迭代上限</small><strong>${loop.max_rounds?'最多 '+loop.max_rounds+' 轮':'以具体任务为准'}</strong></div></div>`;
    const reminder=document.createElement('p');reminder.className='loop-reminder';reminder.textContent=loop.reminder||'本条尚未记录 Loop 建议。';content.append(reminder);
    const body=document.createElement('div');body.className='loop-prompt';body.textContent=loop.copyable_loop||loop.reminder||'暂无 Loop 内容';content.append(body);
  }else{
    let source=r.source||{};
    const chosenVersion=(r.versions||[]).find(v=>v.version===(d.selected_version||e.latest_version));
    const reference=chosenVersion?.reference_provenance;
    if(reference){
      source={url:reference.source_url,commit:reference.source_commit,license:'请查看绑定来源的使用许可',note:'此版本的详细来源记录未能解析，请查看绑定来源核对。'};
      try{const text=d.source_markdown||'';const provenance=JSON.parse(text.slice(text.indexOf('{'),text.lastIndexOf('}')+1));if(provenance.source&&typeof provenance.source==='object')source={...provenance.source,license:provenance.license||provenance.source.license};}catch{}
    }
    const url=safeURL(source.url);
    const rows=[['来源',source.repository||(reference?'采用的参考来源':'用户提交')],['收录时间',dateLabel(source.retrieved_at||r.created_at)],['许可',source.license||'用户提供的个人素材'],['固定版本',source.commit||'原始用户提交文本'],[reference?'参考原文校验':'原文校验',reference?.source_sha256||r.original.sha256]];
    const dl=document.createElement('dl');dl.className='source-grid';rows.forEach(([name,value])=>{const row=document.createElement('div');row.className='source-row';const dt=document.createElement('dt');dt.textContent=name;const dd=document.createElement('dd');if(name==='来源'&&url){const a=document.createElement('a');a.href=url;a.target='_blank';a.rel='noopener noreferrer';a.textContent=value+' ↗';dd.append(a);}else dd.textContent=value;row.append(dt,dd);dl.append(row);});content.append(dl);
    const note=document.createElement('div');note.className='source-note';note.textContent=source.usage_evidence?.note||source.note||'原文、优化版与使用反馈分别保存。';content.append(note);
    if(source.dependencies?.length)content.append(markdown('## 原版依赖\n\n'+source.dependencies.map(v=>'- '+v).join('\n')));
  }
}

function copyText(){const d=state.detail;if(!d)return '';if(state.tab==='loop')return d.loop.copyable_loop||d.loop.reminder||'';if(state.tab==='analysis')return d.analysis||$('detail-content').innerText;if(state.tab==='source')return d.source_markdown||$('detail-content').innerText;return d[state.tab];}
async function copyCurrent() {
  const text=copyText();if(!text)return toast('当前内容为空');
  try{await navigator.clipboard.writeText(text);toast('已复制，可以粘贴到你的项目里');}
  catch{const area=document.createElement('textarea');area.value=text;area.setAttribute('aria-label','待复制内容');document.body.append(area);area.select();const copied=document.execCommand('copy');area.remove();toast(copied?'已复制':'复制未成功，请选中文本后按 Ctrl+C');}
}

async function toggleFavorite(button){
  const id=state.selected;button.disabled=true;
  try{const result=await api('/api/favorites',{method:'POST',headers:{'Content-Type':'application/json','X-Prompt-Library':'1'},body:JSON.stringify({id,favorite:!state.favorites.includes(id)})});state.favorites=result.favorites;updateView();if(state.detail)renderDetail();toast(state.favorites.includes(id)?'已加入我的收藏':'已取消收藏');}
  catch(e){toast('未保存：'+e.message);button.disabled=false;}
}

async function loadLibrary(){
  const button=$('refresh-button');button.disabled=true;error('');
  try{const data=await api('/api/library');state.entries=data.entries;state.categories=data.categories;state.favorites=data.favorites;$('local-caption').textContent=`${data.entry_count} 条素材 · 已连接`;
    const params=new URLSearchParams(location.search);
    const linked=!state.selected&&state.entries.some(e=>e.id===params.get('entry'))?params.get('entry'):null;
    const existing=state.selected||linked;const tab=linked&&tabs.some(t=>t[0]===params.get('tab'))?params.get('tab'):state.tab;
    if(linked)state.selected=linked;
    updateView();if(existing&&state.selected===existing)await selectEntry(existing,!!linked,null,tab);
  }catch(e){error(e.message+'。确认本机服务已启动，再点击刷新。');$('local-caption').textContent='连接异常 · 可重试';if(!state.entries.length){$('entry-list').textContent='暂时无法读取素材';$('detail-pane').innerHTML='<div class="empty-detail">连接恢复后，素材会重新显示。</div>';$('detail-pane').setAttribute('aria-busy','false');}}
  finally{button.disabled=false;}
}

let appInfo=null;
async function loadAppInfo(){
  $('app-info-section').setAttribute('aria-busy','true');$('app-info-error').hidden=true;$('app-info-retry').hidden=true;
  $('backup-download').disabled=true;$('copy-mcp-config').disabled=true;
  try{
    appInfo=await api('/api/app-info');
    $('library-location').textContent=appInfo.library_root;$('app-version').textContent=appInfo.version;
    $('mcp-config').value=appInfo.mcp_config||'';$('copy-mcp-config').disabled=!$('mcp-config').value;
    $('backup-download').disabled=appInfo.backup_url!=='/download/library-backup';
  }catch(e){appInfo=null;$('library-location').textContent='暂不可用';$('mcp-config').value='';$('mcp-config').placeholder='配置读取失败，请重试';$('app-info-error').textContent='读取应用信息失败：'+e.message;$('app-info-error').hidden=false;$('app-info-retry').hidden=false;}
  finally{$('app-info-section').setAttribute('aria-busy','false');}
}
function openHelp(){if(!$('help-dialog').open)$('help-dialog').showModal();loadAppInfo();}
async function downloadBackup(){
  if(!appInfo||$('backup-download').disabled)return;
  const button=$('backup-download');button.disabled=true;$('app-info-error').hidden=true;
  try{
    const response=await fetch(appInfo.backup_url);
    if(!response.ok){const data=await response.json().catch(()=>({}));throw new Error(data.error||'备份暂时无法下载');}
    const blob=await response.blob();const url=URL.createObjectURL(blob);const link=document.createElement('a');
    const name=response.headers.get('Content-Disposition')?.match(/filename="?([^";]+)"?/)?.[1];
    link.href=url;link.download=name||'liubai-backup.zip';document.body.append(link);link.click();link.remove();setTimeout(()=>URL.revokeObjectURL(url),1000);toast('备份文件已准备，请在浏览器下载中查看');
  }catch(e){$('app-info-error').textContent='导出备份失败：'+e.message;$('app-info-error').hidden=false;}
  finally{button.disabled=false;}
}
async function copyMcpConfig(){
  const field=$('mcp-config');if(!field.value)return;
  try{await navigator.clipboard.writeText(field.value);toast('配置已复制，请在客户端添加并重载');}
  catch{field.focus();field.select();let copied=false;try{copied=document.execCommand('copy');}catch{}toast(copied?'配置已复制':'请选中配置后手动复制');}
}

document.addEventListener('click',event=>{
  const learningLink=event.target.closest('#detail-content a');
  if(learningLink&&!event.ctrlKey&&!event.metaKey&&!event.shiftKey){
    const url=new URL(learningLink.href);const id=url.searchParams.get('entry');
    if(url.origin===location.origin&&url.pathname==='/'&&id){
      event.preventDefault();
      if(!state.entries.some(e=>e.id===id))return toast('当前库没有这条素材');
      state.category='all';state.view='all';state.query='';$('search').value='';state.selected=id;updateView();
      return selectEntry(id,true,null,'analysis');
    }
  }
  const view=event.target.closest('[data-view]');if(view){window.ReferenceLibrary?.leave();state.view=view.dataset.view;state.category='all';if(state.view==='recent'){state.sort='recent';$('sort').value='recent';}document.querySelector('.workspace').classList.remove('show-detail');return updateView();}
  const category=event.target.closest('[data-category]');if(category){window.ReferenceLibrary?.leave();state.category=category.dataset.category;state.view='all';document.querySelector('.workspace').classList.remove('show-detail');return updateView();}
  const entry=event.target.closest('[data-entry]');if(entry)return selectEntry(entry.dataset.entry);
  const tab=event.target.closest('[data-tab]');if(tab){state.tab=tab.dataset.tab;renderDetail();$('tab-'+state.tab).focus({preventScroll:true});return;}
  const action=event.target.closest('[data-action]');if(!action)return;
  if(action.dataset.action==='copy')copyCurrent();
  if(action.dataset.action==='favorite')toggleFavorite(action);
  if(action.dataset.action==='back')returnToList();
  if(action.dataset.action==='retry-detail')selectEntry(state.selected,true,action.dataset.version||null);
  if(action.dataset.action==='clear-filters'){state.query='';$('search').value='';state.view='all';state.category='all';updateView();$('search').focus();}
  if(action.dataset.action==='download'){const a=document.createElement('a');const version=state.detail?.selected_version;a.href=`/download/${state.selected}/${state.tab==='original'?'original':'optimized'}`+(state.tab!=='original'&&version?'?version='+encodeURIComponent(version):'');a.download='';a.click();}
});
document.addEventListener('change',event=>{if(event.target.id==='personal-version')selectEntry(state.selected,false,event.target.value);});
document.addEventListener('keydown',event=>{
  if((event.ctrlKey||event.metaKey)&&event.key.toLowerCase()==='k'&&!document.querySelector('dialog[open]')){event.preventDefault();const search=window.ReferenceLibrary?.active() ? $('reference-search') : $('search');search?.focus();search?.select();}
  if(event.key==='Escape'&&!document.querySelector('dialog[open]')&&document.querySelector('.workspace').classList.contains('show-detail')&&matchMedia('(max-width:900px)').matches){event.preventDefault();returnToList();}
  if(event.target.matches('[data-tab][role="tab"]')&&['ArrowRight','ArrowLeft','Home','End'].includes(event.key)){event.preventDefault();const at=tabs.findIndex(t=>t[0]===state.tab);const next=event.key==='Home'?0:event.key==='End'?tabs.length-1:(at+(event.key==='ArrowRight'?1:-1)+tabs.length)%tabs.length;state.tab=tabs[next][0];renderDetail();$('tab-'+state.tab).focus();}
});
$('search').addEventListener('input',event=>{state.query=event.target.value;document.querySelector('.workspace').classList.remove('show-detail');renderList();});
$('sort').addEventListener('change',event=>{state.sort=event.target.value;renderList();});
$('mobile-browse').addEventListener('change',event=>{const [kind,value]=event.target.value.split(':');window.ReferenceLibrary?.leave();state.view=kind==='view'?value:'all';state.category=kind==='category'?value:'all';if(state.view==='recent'){state.sort='recent';$('sort').value='recent';}document.querySelector('.workspace').classList.remove('show-detail');updateView();});
$('more-categories').addEventListener('click',()=>{state.expanded=!state.expanded;renderNavigation();});
$('refresh-button').addEventListener('click',()=>window.ReferenceLibrary?.active() ? window.ReferenceLibrary.refresh() : loadLibrary());
$('help-button').addEventListener('click',openHelp);
$('close-help').addEventListener('click',()=>$('help-dialog').close());
$('app-info-retry').addEventListener('click',loadAppInfo);
$('backup-download').addEventListener('click',downloadBackup);
$('copy-mcp-config').addEventListener('click',copyMcpConfig);
putIcons();loadLibrary();
