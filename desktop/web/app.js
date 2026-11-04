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
const t = (key, vars={}) => window.LiubaiI18n.translate(window.LiubaiLanguage||'zh',key,vars);
const ui = (zh,en) => window.LiubaiLanguage==='en'?en:zh;
const state = {entries:[],categories:[],favorites:[],view:'all',category:'all',query:'',sort:'updated',selected:null,detail:null,tab:'original',expanded:false,request:0};
const categoryIcon = id => ({taste:'taste',ui_design:'ui',development:'code'})[id] || 'folder';
const categoryName = id => {
  const raw=state.categories.find(c=>c.id===id)?.name || '待分类';
  if(window.LiubaiLanguage!=='en')return raw;
  const builtins={'开发与编程':'Development','UI 设计':'UI design','审美 Taste':'Taste','视觉与视频':'Visuals & video','待分类':'Uncategorized','Prompt Motion · 动效视频':'Prompt Motion · Video','Motion Prompt · 动效与镜头':'Motion Prompt · Motion & camera'};
  return builtins[raw]||raw;
};
const displayTitle = e => window.LiubaiLanguage==='en' && e.english_catalogue ? e.english_catalogue.title : e.title;
const displaySummary = e => window.LiubaiLanguage==='en' && e.english_catalogue ? (e.english_catalogue.summary ?? e.summary) : e.summary;
const escapeHTML = value => String(value ?? '').replace(/[&<>"']/g, char=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[char]));
const dateLabel = value => {const date = new Date(value); return Number.isNaN(date.valueOf()) ? (window.LiubaiLanguage==='en'?'Unknown date':'日期未知') : date.toLocaleDateString(window.LiubaiLanguage==='en'?'en':'zh-CN',{year:'numeric',month:'2-digit',day:'2-digit'});};
const safeURL = value => {try {const url = new URL(value,location.origin); return ['http:','https:'].includes(url.protocol)&&(value.startsWith('http')||(/^\/\?entry=PRM-\d+/.test(value)&&url.origin===location.origin))?url.href:null;}catch{return null;}};

async function api(path, options={}) {
  let response;
  try {response = await fetch(path,options);}
  catch {throw new Error(ui("无法连接本机素材库。请重新启动留白，再点击重试或刷新；已保存的素材仍在本机。","Cannot connect to your local library. Restart Liubai and try again. Your saved items are still on this device."));}
  let data;
  try {data = await response.json();}
  catch {throw new Error(ui("本机服务返回了无法识别的内容，请重启留白后重试。","The local service returned an unexpected response. Restart Liubai and try again."));}
  if (!response.ok) throw new Error(window.LiubaiI18n.error(window.LiubaiLanguage,data.error,ui(ui("暂时无法读取素材","Could not load the library"),'Could not complete the local library request.')));
  return data;
}

let toastTimer;
function toast(message) {$('toast').textContent=message; $('toast').hidden=false; clearTimeout(toastTimer); toastTimer=setTimeout(()=>$('toast').hidden=true,3000);}
function error(message) {$('error-banner').textContent=message; $('error-banner').hidden=!message;}
function putIcons(root=document){root.querySelectorAll('[data-icon]').forEach(node=>node.innerHTML=icon(node.dataset.icon));}

function filteredEntries() {
  const query=state.query.toLocaleLowerCase().trim();
  let rows=state.entries.filter(e=>(state.category==='all'||e.category_id===state.category)&&(state.view!=='favorites'||state.favorites.includes(e.id)));
  if(query){const words=query.split(/\s+/); rows=rows.filter(e=>{const text=[e.title,e.summary,e.english_catalogue?.title,e.english_catalogue?.summary,e.id,e.tags.join(' '),categoryName(e.category_id),e.search_text].join(' ').toLocaleLowerCase(); return words.every(word=>text.includes(word));});}
  if(state.sort==='title')rows.sort((a,b)=>displayTitle(a).localeCompare(displayTitle(b),window.LiubaiLanguage==='en'?'en':'zh-CN'));
  else if(state.sort==='recent')rows.sort((a,b)=>String(b.created_at||'').localeCompare(String(a.created_at||''))||b.id.localeCompare(a.id));
  else rows.sort((a,b)=>String(b.updated_at||b.created_at||'').localeCompare(String(a.updated_at||a.created_at||''))||b.id.localeCompare(a.id));
  return rows;
}

function renderNavigation() {
  const count=id=>state.entries.filter(e=>e.category_id===id).length;
  const navButton=(label,glyph,num,active,kind,value)=>`<button class="nav-button ${active?'active':''}" data-${kind}="${value}" ${active?'aria-current="page"':''}><span class="icon">${icon(glyph)}</span><span>${escapeHTML(label)}</span><span class="count">${num}</span></button>`;
  $('space-nav').innerHTML=[[t('all'),'grid',state.entries.length,'all'],[t('favorite'),'star',state.favorites.length,'favorites'],[t('recent'),'clock',state.entries.length,'recent']].map(([label,glyph,num,value])=>navButton(label,glyph,num,state.view===value&&state.category==='all','view',value)).join('');
  const activeCategories=state.categories.filter(c=>count(c.id)>0);
  const shown=state.expanded?state.categories:activeCategories;
  $('category-nav').innerHTML=shown.map(c=>navButton(categoryName(c.id),categoryIcon(c.id),count(c.id),state.category===c.id,'category',c.id)).join('');
  $('category-total').textContent=state.categories.length;
  $('more-categories').innerHTML=`${state.expanded?(window.LiubaiLanguage==='en'?'Hide empty categories':'收起空分类'):(window.LiubaiLanguage==='en'?'Show all categories':'查看全部分类')} <span>${state.expanded?'⌃':'⌄'}</span>`;
  $('more-categories').setAttribute('aria-expanded',String(state.expanded));
  $('quick-filters').innerHTML=[{id:'all',name:'全部'},...activeCategories].map(c=>`<button class="filter-chip ${state.category===c.id?'active':''}" data-category="${c.id}" aria-pressed="${state.category===c.id}">${escapeHTML(c.id==='all'?(window.LiubaiLanguage==='en'?'All':'全部'):categoryName(c.id))}<span class="chip-count">${c.id==='all'?state.entries.length:count(c.id)}</span></button>`).join('');
  $('mobile-browse').innerHTML=`<optgroup label="${t('personal')}"><option value="view:all">${t('all')}</option><option value="view:favorites">${t('favorite')}</option><option value="view:recent">${t('recent')}</option></optgroup><optgroup label="${t('categories')}">`+state.categories.map(c=>`<option value="category:${escapeHTML(c.id)}">${escapeHTML(categoryName(c.id))} · ${count(c.id)}</option>`).join('')+'</optgroup>';
  $('mobile-browse').value=state.category==='all'?'view:'+state.view:'category:'+state.category;
}

function emptyCollection() {
  if(state.query.trim())return `<div class="empty-list"><strong>${ui("没有找到相关素材","No matching items")}</strong><p>${ui("换个关键词，或查看全部素材。","Try a different search or browse all items.")}</p><button class="reference-button" data-action="clear-filters">${ui("清空筛选","Clear filters")}</button></div>`;
  if(state.view==='favorites')return `<div class="empty-list"><strong>${ui("还没有收藏","No favorites yet")}</strong><p>${ui("打开素材后，点击星标收藏。","Open an item and select the star to save it.")}</p><button class="reference-button" data-action="clear-filters">${ui("浏览全部素材","Browse all items")}</button></div>`;
  const first=state.entries.length===0&&state.category==='all';
  return `<div class="empty-list welcome-empty"><span class="empty-symbol">${icon('folder')}</span><strong>${first?ui("保存你的第一条提示词","Save your first prompt"):ui("这个分类还没有素材","This category is empty")}</strong><p>${ui("粘贴原文或导入文件，选择分类后保存到本机。","Paste the original or import a file, choose a category and save it locally.")}</p><div class="empty-actions"><button class="reference-button primary" data-prompt-action="new">${first?ui("保存第一条素材","Save your first item"):ui("新建素材","New item")}</button><button class="reference-button" data-prompt-action="import">${ui("导入文本文件","Import text file")}</button></div></div>`;
}

function renderList() {
  const rows=filteredEntries();
  const title=state.category!=='all'?categoryName(state.category):({all:t('all'),favorites:t('favorite'),recent:t('recent')}[state.view]);
  $('view-title').replaceChildren(document.createTextNode(title));
  const badge=document.createElement('span');badge.id='title-count';badge.textContent=rows.length;$('view-title').append(badge);
  $('result-count').textContent=t('count',{count:rows.length})+(state.query?(window.LiubaiLanguage==='en'?' · Search results':' · 搜索结果'):'');
  $('footer-count').textContent=window.LiubaiLanguage==='en'?`${state.entries.length} items / ${state.categories.length} categories`:`${state.entries.length} 条已留存 / ${state.categories.length} 个分类`;
  $('entry-list').innerHTML=rows.length?rows.map(e=>`<button class="entry-card ${state.selected===e.id?'selected':''}" data-entry="${e.id}" aria-pressed="${state.selected===e.id}" aria-label="${escapeHTML(e.id+' '+displayTitle(e))}"><div class="entry-card-top"><span class="entry-category">${icon(categoryIcon(e.category_id))}${escapeHTML(categoryName(e.category_id))}</span><span class="entry-id">${e.id.replace('PRM-','#')}</span></div><h3>${escapeHTML(displayTitle(e))}</h3>${String(displaySummary(e)||'').trim()?`<p>${escapeHTML(displaySummary(e))}</p>`:''}<div class="entry-card-bottom">${e.tags.slice(0,2).map(t=>`<span class="tiny-tag">${escapeHTML(t)}</span>`).join('')}${state.favorites.includes(e.id)?`<span class="saved-star">${icon('star')}</span>`:''}</div></button>`).join(''):emptyCollection();
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

async function selectEntry(id, reveal=true, version=null, tab=null) {
  state.selected=id;state.detail=null;state.tab=tab||'original';const request=++state.request;
  $('detail-pane').setAttribute('aria-busy','true');
  $('detail-pane').innerHTML=`<div id="detail-loading" class="detail-message" tabindex="-1"><p role="status">${ui("正在读取素材…","Loading item…")}</p><button class="reference-button mobile-back" data-action="back">${ui("返回素材列表","Back to items")}</button></div>`;
  document.querySelectorAll('[data-entry]').forEach(node=>{node.classList.toggle('selected',node.dataset.entry===id);node.setAttribute('aria-pressed',String(node.dataset.entry===id));});
  if(reveal){document.querySelector('.workspace').classList.add('show-detail');if(matchMedia('(max-width:900px)').matches)$('detail-loading').focus({preventScroll:true});}
  try {const detail=await api('/api/entries/'+encodeURIComponent(id)+(version?'?version='+encodeURIComponent(version):''));if(request!==state.request)return;state.detail=detail;if(detail.source_prompt&&!tab)state.tab='original';renderDetail();if(reveal&&matchMedia('(max-width:900px)').matches&&document.querySelector('.workspace').classList.contains('show-detail'))$('detail-title')?.focus({preventScroll:true});}
  catch(e){if(request!==state.request)return;$('detail-pane').innerHTML=`<div id="detail-error" class="detail-message" tabindex="-1"><p role="alert">${escapeHTML(e.message)}</p><div class="empty-actions"><button class="reference-button" data-action="retry-detail" data-version="${escapeHTML(version||'')}">${ui("重试","Retry")}</button><button class="reference-button mobile-back" data-action="back">${ui("返回素材列表","Back to items")}</button></div></div>`;if(reveal&&document.querySelector('.workspace').classList.contains('show-detail'))$('detail-error').focus({preventScroll:true});}
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

const tabs=[['original','original'],['analysis','analysis'],['optimized','optimized'],['loop','Loop'],['source','source']];
function appendPromptLinks(parent,text){
  let offset=0;
  for(const match of text.matchAll(/https?:\/\/[^\s<>]+/g)){
    parent.append(document.createTextNode(text.slice(offset,match.index)));
    let linked=match[0].replace(/[.,;:!?。，；：！？、"'`]+$/g,'');
    for(const [left,right] of [['(',')'],['[',']'],['{','}'],['（','）'],['【','】'],['《','》'],['「','」'],['『','』'],['“','”'],['‘','’'],['«','»']]){
      while(linked.endsWith(right)&&linked.split(right).length>linked.split(left).length)linked=linked.slice(0,-1);
    }
    const url=safeURL(linked);
    if(url){const a=document.createElement('a');a.href=url;a.target='_blank';a.rel='noopener noreferrer';a.textContent=linked;parent.append(a,document.createTextNode(match[0].slice(linked.length)));}
    else parent.append(document.createTextNode(match[0]));
    offset=match.index+match[0].length;
  }
  parent.append(document.createTextNode(text.slice(offset)));
}

function renderBilingualReading(content,pair,englishOriginal=false){
  if(window.LiubaiLanguage==='en' && pair.original && !pair.is_source_prompt){
    const view=window.LiubaiI18n.readingView('en',pair,englishOriginal);
    const stack=document.createElement('div');stack.className='bilingual-stack';
    const main=document.createElement('section');main.className='source-block';
    const title=document.createElement('h3');title.textContent=view.kind==='translation'?'English translation':'Original prompt';main.append(title);
    const body=document.createElement('pre');body.className='prompt-text';body.dir='auto';body.lang=englishOriginal||view.kind==='translation'?'en':'und';appendPromptLinks(body,view.primary);main.append(body);stack.append(main);
    if(view.kind==='translation'){
      const copy=document.createElement('button');copy.className='reference-button';copy.type='button';copy.textContent=t('copyTranslation');copy.addEventListener('click',()=>copyCurrent(view.primary));main.append(copy);
    }
    if(view.foldOriginal){
      const details=document.createElement('details');details.className='source-block';
      try{details.open=localStorage.getItem('liubai.showChinese')==='true';}catch(_){}
      const summary=document.createElement('summary');summary.textContent=englishOriginal?'Chinese translation':'Original text';details.append(summary);
      const text=document.createElement('pre');text.className='prompt-text';text.lang=englishOriginal?'zh':'und';appendPromptLinks(text,view.original);details.append(text);
      if(englishOriginal){const copy=document.createElement('button');copy.type='button';copy.className='reference-button';copy.textContent=t('copyTranslation');copy.addEventListener('click',()=>copyCurrent(view.original));details.append(copy);}
      details.addEventListener('toggle',()=>{try{localStorage.setItem('liubai.showChinese',String(details.open));}catch(_){}});stack.append(details);
    }else if(!englishOriginal){const note=document.createElement('p');note.className='source-note';note.textContent=t('missingEnglish');stack.append(note);}
    content.append(stack);return;
  }
  const notice=document.createElement('p');notice.className='source-note';notice.textContent=pair.notice;content.append(notice);
  const stack=document.createElement('div');stack.className='bilingual-stack';stack.dataset.translationStatus=pair.translation_status||'';
  const isChinese=pair.translation_status==='already_chinese';
  const translated=pair.translation||pair.excerpt_translation;
  const translationLabel=pair.translation_label||(isChinese?'中文说明':translated?'中文翻译':['unavailable','source_changed'].includes(pair.translation_status)?'中文翻译 · 需要核对':'中文翻译 · 尚未补充');
  for(const [key,label,text] of [
    ['original',pair.original_label||'原文提示词',pair.original||pair.excerpt],
    ['translation',translationLabel,translated||pair.notice]
  ]){
    const block=document.createElement('section');block.className='source-block source-block-'+key;
    const heading=document.createElement('h3');heading.textContent=label;block.append(heading);
    const pre=document.createElement('pre');pre.className='prompt-text source-'+key;pre.dir='auto';
    if(key==='translation')pre.lang='zh-Hans';
    appendPromptLinks(pre,text||ui('没有可核验的来源正文；请从原网页查看。','No verified source text is available; consult the original page.'));block.append(pre);
    if(key==='translation'&&pair.translation_status==='ready'&&pair.translation){
      const copy=document.createElement('button');copy.className='reference-button';copy.type='button';copy.textContent=t('copyTranslation');
      copy.addEventListener('click',()=>copyCurrent(pair.translation));block.append(copy);
    }
    stack.append(block);
  }
  content.append(stack);
}

function panelCopyLabel(){return {optimized:ui('复制复用改写','Copy adaptation'),analysis:ui('复制分析','Copy analysis'),loop:ui('复制 Loop','Copy Loop'),source:ui('复制来源说明','Copy source notes')}[state.tab]||ui('复制当前内容','Copy current content');}

function renderMotionDetail(d){
  const m=d.source_prompt,e=d.item;
  if(state.tab==='translation')state.tab='original';
  if(!['original','translation','analysis','optimized','loop','source'].includes(state.tab)){state.tab='original';}
  const motionTabs=[['original',t('original')],['analysis',t('analysis')],['optimized',t('optimized')],['loop','Loop'],['source',ui('来源与完整性','Source & integrity')]];
  const url=safeURL(m.url),post=safeURL(m.post_url);
  const curated=d.record.publication?.original_kind==='curation';
  const english=window.LiubaiLanguage==='en';
  const saved=state.favorites.includes(e.id);
  $('detail-pane').innerHTML=`<div class="detail-header"><div class="detail-topline"><div class="detail-controls"><button class="reference-button mobile-back" data-action="back">${ui("返回素材列表","Back to items")}</button></div><div class="detail-controls"><button class="icon-button ${saved?'saved':''}" data-action="favorite" aria-label="${saved?ui("取消收藏","Remove from favorites"):ui("收藏这条素材","Add to favorites")}" aria-pressed="${saved}">${icon('star')}</button><button class="icon-button" data-action="download" aria-label="${ui("导出正文","Export text")}" ${state.tab==='original'&&!m.copyable||!['original','optimized'].includes(state.tab)?'disabled':''}>${icon('download')}</button></div></div><h2 id="detail-title" tabindex="-1">${escapeHTML(displayTitle(state.entries.find(row=>row.id===e.id)||e))}</h2><div class="detail-meta"><span>${escapeHTML(e.id)}</span><span>${m.copyable?ui("来源全文已收录","Full source text available"):m.status==='source_index'?ui("来源索引 · 不是提示词","Source index · no prompt text"):m.excerpt?ui("仅摘录 · 来源全文未收录","Excerpt only · full text unavailable"):ui("来源全文未收录","Full source text unavailable")}</span><span>${ui("效果未实测","Untested")}</span></div><p>${url?`<a href="${escapeHTML(url)}" target="_blank" rel="noopener noreferrer">${ui("打开原网页 ↗","Open source page ↗")}</a>`:''} ${post?` · <a href="${escapeHTML(post)}" target="_blank" rel="noopener noreferrer">${ui("作者原帖 ↗","Author’s original post ↗")}</a>`:''}</p></div><div class="detail-tabs" role="tablist" aria-label="${ui("素材内容","Item content")}">${motionTabs.map(([key,label])=>`<button id="tab-${key}" class="detail-tab ${state.tab===key?'active':''}" role="tab" aria-selected="${state.tab===key}" aria-controls="detail-content" tabindex="${state.tab===key?'0':'-1'}" data-tab="${key}">${label}</button>`).join('')}</div><div id="detail-content" class="detail-content" role="tabpanel" aria-labelledby="tab-${state.tab}" tabindex="0"></div><div class="detail-bottom"><button class="copy-button" data-action="copy" ${m.copyable?'':'disabled'}>${icon('copy')}<span>${m.copyable?ui("复制原提示词","Copy original"):ui("全文未收录，暂不可复制原文","Original unavailable")}</span></button><button class="reference-button" data-action="copy-panel">${!m.copyable&&['original','translation'].includes(state.tab)?ui("复制摘录（非全文）","Copy excerpt"):ui("复制当前内容","Copy current content")}</button></div>`;
  queueMicrotask(()=>{window.ReferenceLibrary?.renderRelated(e.id);window.PromptEditor?.decorateDetail();});
  const content=$('detail-content');
  if(state.tab==='original'){
    if(m.copyable||!m.excerpt)$('detail-pane').querySelector('[data-action="copy-panel"]').hidden=true;
    if(english && curated && d.reading_pair_en?.translation_status==='ready'){
      const section=document.createElement('section');section.className='source-block';
      const heading=document.createElement('h3');heading.textContent="Curator's guide · English translation";section.append(heading);
      const note=document.createElement('p');note.className='source-note';note.textContent="English edition of the curator's independently written guide.";section.append(note);
      const body=document.createElement('pre');body.className='prompt-text';body.lang='en';appendPromptLinks(body,d.reading_pair_en.translation);section.append(body);
      const copy=document.createElement('button');copy.type='button';copy.className='reference-button';copy.textContent=t('copyTranslation');copy.addEventListener('click',()=>copyCurrent(d.reading_pair_en.translation));section.append(copy);content.append(section);
      const details=document.createElement('details');details.className='source-block';
      try{details.open=localStorage.getItem('liubai.showChinese')==='true';}catch(_){}
      const summary=document.createElement('summary');summary.textContent=t(details.open?'hideChinese':'showChinese');details.append(summary);
      const original=document.createElement('pre');original.className='prompt-text';original.lang='zh';appendPromptLinks(original,d.original);details.append(original);
      details.addEventListener('toggle',()=>{
        summary.textContent=t(details.open?'hideChinese':'showChinese');
        try{localStorage.setItem('liubai.showChinese',String(details.open));}catch(_){}
      });
      content.append(details);
    }
    if(english && m.copyable){
      renderBilingualReading(content,m,true);
    }else if(!english || m.excerpt){
      const excerptPanel=english?document.createElement('details'):content;
      if(english){
        const summary=document.createElement('summary');summary.textContent='Source excerpt';excerptPanel.append(summary);content.append(excerptPanel);
      }
      renderBilingualReading(excerptPanel,{...m,is_source_prompt:true,
        notice:ui(m.translation_status==='ready'?'原文在上，中文在下。复制按钮只复制原文提示词，不包含译文或分析。':m.notice,'The upstream text below is an excerpt. Consult the source for the complete text.'),
        original_label:m.copyable?'原文提示词':ui('原文摘录 · 非全文','Source excerpt'),
        translation_label:m.copyable?(m.translation?'中文翻译':'中文翻译 · 需要核对'):ui('摘录释义 · 非全文翻译','Excerpt explanation')});
    }

  }else if(state.tab==='analysis')content.append(markdown(m.analysis||(curated&&d.analysis?ui('以下是对公开复用方案的拆解。\n\n','Analysis of the curator’s guide.\n\n')+d.analysis:ui('暂无与来源绑定的拆解。','No source-bound analysis is available.'))));
  else if(state.tab==='optimized'){content.append(markdown(ui("这是整理者的复用改写。","Adaptation written by the curator.")));const versions=d.record.versions||[];if(versions.length>1){const label=document.createElement('label');label.className='personal-version-picker';label.innerHTML=`${ui("优化版本","Adaptation version")} <select id="personal-version" aria-label="${ui("优化版本","Adaptation version")}">${versions.map(v=>`<option value="${escapeHTML(v.version)}" ${v.version===d.selected_version?'selected':''}>${escapeHTML(v.version)}</option>`).join('')}</select>`;content.append(label);}const pre=document.createElement('pre');pre.className='prompt-text';appendPromptLinks(pre,d.optimized);content.append(pre);}
  else if(state.tab==='loop')content.append(markdown(d.loop?.copyable_loop||d.loop?.reminder||ui("本条未设置 Loop。","This item has no Loop.")));
  else {
    const basis={
      preserved_short_prompt_hash_verified:ui('既有完整短原文，与此前保存的来源校验值一致；未重新抓取网页','Archived text matches the stored checksum.'),
      user_supplied_screenshot:ui('本次用户提供的网页截图，并与页面正文核对','User-supplied screenshot checked against the source page.'),
      verified_short_web_prompt:ui('已核对的短网页提示词','Verified short web prompt.'),
      preserved_excerpt_only:ui('既有短摘录与历史整理记录，未核对来源全文','Archived excerpt and curation notes.')
    };
    const author=m.author||ui('见原网页','See source page');
    const evidence=basis[m.evidence_basis]||ui('未核对全文','Full text unverified');
    const checked=m.checked_at?dateLabel(m.checked_at):ui('未记录','Unrecorded');
    const integrity=m.copyable?ui('该条提示词全文已收录；创作上下文仍需单独核对','Full prompt available. Consult the source for creative context.'):ui('原文不完整','Full source text unavailable.');
    content.append(markdown(`- ${ui('来源作者','Author')} — ${author}\n- ${ui('核对依据','Evidence')} — ${evidence}\n- ${ui('核对时间','Date checked')} — ${checked}\n- ${ui('完整性','Integrity')} — ${integrity}`));
    if(!english)content.append(markdown(m.notice));
  }
  if(state.tab!=='original')$('detail-pane').querySelector('[data-action="copy-panel"]').textContent=panelCopyLabel();
}
function renderDetail() {
  const d=state.detail;if(!d)return;const e=d.item,r=d.record;const saved=state.favorites.includes(e.id);
  $('detail-pane').classList.add('reading-detail');
  if(state.tab==='translation'||!tabs.some(([key])=>key===state.tab))state.tab='original';
  if(d.source_prompt)return renderMotionDetail(d);
  const selectedVersion=d.selected_version||e.latest_version;
  const versionRecord=(r.versions||[]).find(v=>v.version===selectedVersion);
  const notOptimized=versionRecord?.optimization_status==='not_optimized';
  const optimizedLabel=versionRecord?.public_template?ui('中文复用版','Chinese adaptation'):notOptimized?ui('保存版','Saved version'):ui('优化版','Adaptation');
  queueMicrotask(()=>{window.ReferenceLibrary?.renderRelated(e.id);window.PromptEditor?.decorateDetail();});
  $('detail-pane').innerHTML=`<div class="detail-header"><div class="detail-topline"><div class="detail-controls"><button class="icon-button mobile-back" data-action="back" aria-label="${ui("返回素材列表","Back to items")}">${icon('back')}</button><div class="detail-symbol">${icon(categoryIcon(e.category_id))}</div></div><div class="detail-controls"><button class="icon-button ${saved?'saved':''}" data-action="favorite" aria-label="${saved?ui("取消收藏","Remove from favorites"):ui("收藏这条素材","Add to favorites")}" aria-pressed="${saved}">${icon('star')}</button><button class="icon-button" data-action="download" aria-label="${ui('导出 Markdown','Export Markdown')}">${icon('download')}</button></div></div><h2 id="detail-title" tabindex="-1">${escapeHTML(displayTitle(state.entries.find(row=>row.id===e.id)||e))}</h2>${String(displaySummary(state.entries.find(row=>row.id===e.id)||e)||'').trim()?`<p class="detail-summary">${escapeHTML(displaySummary(state.entries.find(row=>row.id===e.id)||e))}</p>`:''}<div class="detail-meta"><span class="meta-tag">${escapeHTML(categoryName(e.category_id))}</span><span>${e.id}</span><span class="meta-dot"></span><span>${dateLabel(e.created_at)}</span><span class="meta-dot"></span><span>${notOptimized?ui("尚未优化","No adaptation"):e.evaluation_status==='untested'?ui("待实测","Untested"):ui("查看评测记录","See evaluation notes")}</span></div></div><div class="detail-tabs" role="tablist" aria-label="${ui("素材内容","Item content")}">${tabs.map(([value,label])=>`<button id="tab-${value}" class="detail-tab ${state.tab===value?'active':''}" role="tab" aria-selected="${state.tab===value}" aria-controls="detail-content" tabindex="${state.tab===value?'0':'-1'}" data-tab="${value}">${value==='optimized'?optimizedLabel:(value==='loop'?'Loop':t(label))}</button>`).join('')}</div><div id="detail-content" class="detail-content" role="tabpanel" aria-labelledby="tab-${state.tab}" tabindex="0"></div><div class="detail-bottom"><button class="copy-button" data-action="copy">${icon('copy')}<span>${t('copyOriginal')}</span></button></div>`;
  const content=$('detail-content');
  $('detail-pane').querySelector('[data-action="copy"] span').textContent=t('copyOriginal');
  $('detail-pane').querySelector('[data-action="copy"]').disabled=!d.original;
  $('detail-pane').querySelector('[data-action="download"]').disabled=!['original','optimized'].includes(state.tab);
  const sourceURL=safeURL(versionRecord?.reference_provenance?.source_url||r.source?.url);
  if(sourceURL){const p=document.createElement('p');p.className='reading-source-link';const a=document.createElement('a');a.href=sourceURL;a.target='_blank';a.rel='noopener noreferrer';a.textContent=ui("打开原网页 ↗","Open source page ↗");p.append(a);$('detail-pane').querySelector('.detail-header').append(p);}
  if(state.tab!=='original'){const button=document.createElement('button');button.className='reference-button';button.dataset.action='copy-panel';button.textContent=panelCopyLabel();$('detail-pane').querySelector('.detail-bottom').append(button);}
  if(state.tab==='original'){
    const englishOriginal=state.entries.find(row=>row.id===e.id)?.english_catalogue?.original_language==='en';
    const reading=window.LiubaiLanguage==='en'&&!englishOriginal?d.reading_pair_en:d.reading_pair;
    renderBilingualReading(content,reading||{original:d.original,translation:'',notice:'对应中文译文尚未补充；复用改写不作为翻译。'},englishOriginal);
  }else if(state.tab==='optimized'){
    const versions=r.versions||[];
    const versionControl=state.tab==='optimized'&&versions.length>1?`<label class="personal-version-picker"><span>${ui("优化版本","Adaptation version")}</span><select id="personal-version" aria-label="${ui("优化版本","Adaptation version")}">${versions.map(v=>`<option value="${escapeHTML(v.version)}" ${v.version===selectedVersion?'selected':''}>${escapeHTML(v.version)}${v.version===e.latest_version?ui(" · 最新"," · Latest"):''}</option>`).join('')}</select></label>`:`<span class="version-pill">${state.tab==='optimized'?escapeHTML(selectedVersion):'ORIGINAL'}</span>`;
    const caption=document.createElement('div');caption.className='content-caption';caption.innerHTML=`<span>${state.tab==='optimized'?(notOptimized?ui("原文副本 · 尚未优化","Saved original · no adaptation"):ui("可直接复制 · 填写变量后使用","Copy and fill in the variables")):ui("完整原文 · 原始内容留存","Full original · preserved")}</span>${versionControl}`;
    const pre=document.createElement('pre');pre.className='prompt-text';appendPromptLinks(pre,d[state.tab]);content.append(caption,pre);
  }else if(state.tab==='analysis'){
    if(d.analysis){content.append(markdown(d.analysis));}
    else {const message=document.createElement('p');message.className='empty-detail';message.textContent=d.teaching_status==='version_mismatch'?ui("这份正文或版本已变化，教学拆解尚未更新。","The text or version changed. Its analysis needs an update."):d.teaching_status==='unavailable'?ui("教学文件暂时无法读取，原文和保存版仍可使用。","The analysis could not be read. The original and saved version are still available."):ui("这条素材还没有教学拆解。保存提示词不会自动生成分析。","This item has no analysis. Saving a prompt does not generate one.");content.append(message);}
  }else if(state.tab==='loop'){
    const loop=d.loop;content.innerHTML=`<div class="content-caption"><span>${ui("有边界的迭代","Bounded iteration")}</span><span class="version-pill">${loop.explicit_loop_present?ui("已写入优化版","Included in the adaptation"):ui("附加建议","Additional suggestion")}</span></div><div class="loop-facts"><div class="loop-fact"><small>${ui("使用方式","When to use")}</small><strong>${loop.applicability==='conditional'?ui("按任务条件启用","Use when the task warrants it"):ui("查看适用条件","See conditions")}</strong></div><div class="loop-fact"><small>${ui("迭代上限","Iteration limit")}</small><strong>${loop.max_rounds?ui(`最多 ${loop.max_rounds} 轮`,`Up to ${loop.max_rounds} rounds`):ui("以具体任务为准","Depends on the task")}</strong></div></div>`;
    const reminder=document.createElement('p');reminder.className='loop-reminder';reminder.textContent=loop.reminder||ui("本条尚未记录 Loop 建议。","This item has no Loop recommendation.");content.append(reminder);
    const body=document.createElement('div');body.className='loop-prompt';body.textContent=loop.copyable_loop||loop.reminder||ui("暂无 Loop 内容","No Loop content");content.append(body);
  }else{
    let source=r.source||{};
    const chosenVersion=(r.versions||[]).find(v=>v.version===(d.selected_version||e.latest_version));
    const reference=chosenVersion?.reference_provenance;
    if(reference){
      source={url:reference.source_url,commit:reference.source_commit,license:ui("请查看绑定来源的使用许可","See the linked source for license terms"),note:ui("此版本的详细来源记录未能解析，请查看绑定来源核对。","The source record for this version could not be read. Consult the linked source.")};
      try{const text=d.source_markdown||'';const provenance=JSON.parse(text.slice(text.indexOf('{'),text.lastIndexOf('}')+1));if(provenance.source&&typeof provenance.source==='object')source={...provenance.source,license:provenance.license||provenance.source.license};}catch{}
    }
    const url=safeURL(source.url);
    const rows=[[ui("来源","Source"),source.repository||(reference?ui("采用的参考来源","Imported reference"):ui("用户提交","User submission"))],[ui("收录时间","Date added"),dateLabel(source.retrieved_at||r.created_at)],[ui("许可","License"),source.license||ui("用户提供的个人素材","Personal material supplied by the user")],[ui("固定版本","Pinned version"),source.commit||ui("原始用户提交文本","Original user submission")],[reference?ui("参考原文校验","Reference text checksum"):ui("原文校验","Original checksum"),reference?.source_sha256||r.original.sha256]];
    const dl=document.createElement('dl');dl.className='source-grid';rows.forEach(([name,value])=>{const row=document.createElement('div');row.className='source-row';const dt=document.createElement('dt');dt.textContent=name;const dd=document.createElement('dd');if(name===rows[0][0]&&url){const a=document.createElement('a');a.href=url;a.target='_blank';a.rel='noopener noreferrer';a.textContent=value+' ↗';dd.append(a);}else dd.textContent=value;row.append(dt,dd);dl.append(row);});content.append(dl);
    const note=document.createElement('div');note.className='source-note';note.textContent=source.usage_evidence?.note||source.note||ui("原文、优化版与使用反馈分别保存。","The original, adaptations and feedback are stored separately.");content.append(note);
    if(source.dependencies?.length)content.append(markdown(ui("## 原版依赖\n\n","## Source dependencies\n\n")+source.dependencies.map(v=>'- '+v).join('\n')));
  }
}

function copyText(){const d=state.detail;if(!d)return '';if(d.source_prompt){const m=d.source_prompt;if(state.tab==='original')return m.original||(m.excerpt?'[来源摘录，非完整原文]\n'+m.excerpt:'');if(state.tab==='translation')return m.translation||(m.excerpt_translation?'[摘录释义，非全文翻译]\n'+m.excerpt_translation:'');if(state.tab==='analysis')return m.analysis||(d.record.publication?.original_kind==='curation'?d.analysis:'');return state.tab==='optimized'?d.optimized:$('detail-content').innerText;}if(state.tab==='loop')return d.loop.copyable_loop||d.loop.reminder||'';if(state.tab==='analysis')return d.analysis||$('detail-content').innerText;if(state.tab==='source')return d.source_markdown||$('detail-content').innerText;return d[state.tab];}
async function copyCurrent(text) {
  text=text??copyText();if(!text)return toast(ui('当前内容为空','Nothing to copy.'));
  try{await navigator.clipboard.writeText(text);toast(ui('已复制，可以粘贴到你的项目里','Copied. You can paste it into your project.'));}
  catch{const area=document.createElement('textarea');area.value=text;area.setAttribute('aria-label',ui("待复制内容","Text to copy"));document.body.append(area);area.select();const copied=document.execCommand('copy');area.remove();toast(copied?ui("已复制","Copied"):ui("复制未成功，请选中文本后按 Ctrl+C","Copy failed. Select the text and copy it manually."));}
}

async function toggleFavorite(button){
  const id=state.selected;button.disabled=true;
  try{const result=await api('/api/favorites',{method:'POST',headers:{'Content-Type':'application/json','X-Prompt-Library':'1'},body:JSON.stringify({id,favorite:!state.favorites.includes(id)})});state.favorites=result.favorites;updateView();if(state.detail)renderDetail();toast(state.favorites.includes(id)?ui("已加入我的收藏","Added to favorites"):ui("已取消收藏","Removed from favorites"));}
  catch(e){toast(ui("未保存：","Could not save: ")+e.message);button.disabled=false;}
}

async function loadLibrary(){
  const button=$('refresh-button');button.disabled=true;error('');
  try{const data=await api('/api/library');state.entries=data.entries;state.categories=data.categories;state.favorites=data.favorites;state.connection='ready';renderConnection();
    const params=new URLSearchParams(location.search);
    const linked=!state.selected&&state.entries.some(e=>e.id===params.get('entry'))?params.get('entry'):null;
    const existing=state.selected||linked;const tab=linked&&tabs.some(t=>t[0]===params.get('tab'))?params.get('tab'):state.tab;
    if(linked)state.selected=linked;
    updateView();if(existing&&state.selected===existing)await selectEntry(existing,!!linked,null,tab);
  }catch(e){state.connection='error';renderConnection();error(e.message+ui("。确认本机服务已启动，再点击刷新。"," Make sure Liubai is running, then refresh."));if(!state.entries.length){$('entry-list').textContent=ui("暂时无法读取素材","Could not load the library");$('detail-pane').innerHTML=`<div class="empty-detail">${ui("连接恢复后，素材会重新显示。","Your items will reappear once the connection is restored.")}</div>`;$('detail-pane').setAttribute('aria-busy','false');}}
  finally{button.disabled=false;}
}

function renderConnection(){
  if(state.connection==='ready')$('local-caption').textContent=ui(`${state.entries.length} 条素材 · 已连接`,`${state.entries.length} items · Connected`);
  if(state.connection==='error')$('local-caption').textContent=ui('连接异常 · 可重试','Connection unavailable · try again');
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
    window.LiubaiGuide?.updateConnection(appInfo);
  }catch(e){appInfo=null;window.LiubaiGuide?.updateConnection(null);$('library-location').textContent=ui("暂不可用","Unavailable");$('mcp-config').value='';$('mcp-config').placeholder=ui("配置读取失败，请重试","Could not load configuration. Try again.");$('app-info-error').textContent=ui("读取应用信息失败：","Could not load app information: ")+e.message;$('app-info-error').hidden=false;$('app-info-retry').hidden=false;}
  finally{$('app-info-section').setAttribute('aria-busy','false');}
}
function openHelp(section='start'){window.LiubaiGuide?.rememberOpener(document.activeElement);if(!$('help-dialog').open)$('help-dialog').showModal();window.LiubaiGuide?.select(typeof section==='string'?section:'start');loadAppInfo();}
async function downloadBackup(){
  if(!appInfo||$('backup-download').disabled)return;
  const button=$('backup-download');button.disabled=true;$('app-info-error').hidden=true;
  try{
    const response=await fetch(appInfo.backup_url);
    if(!response.ok){const data=await response.json().catch(()=>({}));throw new Error(window.LiubaiI18n.error(window.LiubaiLanguage,data.error,ui(ui("备份暂时无法下载","Backup download unavailable"),'Backup download unavailable')));}
    const blob=await response.blob();const url=URL.createObjectURL(blob);const link=document.createElement('a');
    const name=response.headers.get('Content-Disposition')?.match(/filename="?([^";]+)"?/)?.[1];
    link.href=url;link.download=name||'liubai-backup.zip';document.body.append(link);link.click();link.remove();setTimeout(()=>URL.revokeObjectURL(url),1000);toast(ui("备份文件已准备，请在浏览器下载中查看","Backup is ready. Check your browser downloads."));
  }catch(e){$('app-info-error').textContent=ui("导出备份失败：","Backup export failed: ")+e.message;$('app-info-error').hidden=false;}
  finally{button.disabled=false;}
}
async function copyMcpConfig(){
  const field=$('mcp-config');if(!field.value)return;
  try{await navigator.clipboard.writeText(field.value);toast(ui("配置已复制，请在客户端添加并重载","Configuration copied. Add it to your client and reload."));}
  catch{field.focus();field.select();let copied=false;try{copied=document.execCommand('copy');}catch{}toast(copied?ui("配置已复制","Configuration copied"):ui("请选中配置后手动复制","Select the configuration and copy it manually."));}
}

document.addEventListener('click',event=>{
  const learningLink=event.target.closest('#detail-content a');
  if(learningLink&&!event.ctrlKey&&!event.metaKey&&!event.shiftKey){
    const url=new URL(learningLink.href);const id=url.searchParams.get('entry');
    if(url.origin===location.origin&&url.pathname==='/'&&id){
      event.preventDefault();
      if(!state.entries.some(e=>e.id===id))return toast(ui("当前库没有这条素材","This item is missing from your library"));
      state.category='all';state.view='all';state.query='';$('search').value='';state.selected=id;updateView();
      return selectEntry(id,true,null,'analysis');
    }
  }
  const view=event.target.closest('[data-view]');if(view){window.ReferenceLibrary?.leave();state.view=view.dataset.view;state.category='all';if(state.view==='recent'){state.sort='recent';$('sort').value='recent';}document.querySelector('.workspace').classList.remove('show-detail');return updateView();}
  const category=event.target.closest('[data-category]');if(category){window.ReferenceLibrary?.leave();state.category=category.dataset.category;state.view='all';document.querySelector('.workspace').classList.remove('show-detail');return updateView();}
  const entry=event.target.closest('[data-entry]');if(entry)return selectEntry(entry.dataset.entry);
  const tab=event.target.closest('[data-tab]');if(tab){state.tab=tab.dataset.tab;renderDetail();$('tab-'+state.tab).focus({preventScroll:true});return;}
  const action=event.target.closest('[data-action]');if(!action)return;
  if(action.dataset.action==='copy')copyCurrent(state.detail?.source_prompt?state.detail.source_prompt.original:state.detail?.original);
  if(action.dataset.action==='copy-panel')copyCurrent();
  if(action.dataset.action==='favorite')toggleFavorite(action);
  if(action.dataset.action==='back')returnToList();
  if(action.dataset.action==='retry-detail')selectEntry(state.selected,true,action.dataset.version||null);
  if(action.dataset.action==='clear-filters'){state.query='';$('search').value='';state.view='all';state.category='all';updateView();$('search').focus();}
  if(action.dataset.action==='download'){const a=document.createElement('a');const version=state.detail?.selected_version;a.href=`/download/${state.selected}/${state.tab==='original'?'original':'optimized'}`+(state.tab!=='original'&&version?'?version='+encodeURIComponent(version):'');a.download='';a.click();}
});
document.addEventListener('change',event=>{if(event.target.id==='personal-version')selectEntry(state.selected,false,event.target.value,state.tab);});
document.addEventListener('keydown',event=>{
  if((event.ctrlKey||event.metaKey)&&event.key.toLowerCase()==='k'&&!document.querySelector('dialog[open]')){event.preventDefault();const search=window.ReferenceLibrary?.active() ? $('reference-search') : $('search');search?.focus();search?.select();}
  if(event.key==='Escape'&&!document.querySelector('dialog[open]')&&document.querySelector('.workspace').classList.contains('show-detail')&&matchMedia('(max-width:900px)').matches){event.preventDefault();returnToList();}
  if(event.target.matches('[data-tab][role="tab"]')&&['ArrowRight','ArrowLeft','Home','End'].includes(event.key)){event.preventDefault();const visibleTabs=Array.from(document.querySelectorAll('[data-tab][role="tab"]')).map(t=>t.dataset.tab);const at=visibleTabs.indexOf(state.tab);const next=event.key==='Home'?0:event.key==='End'?visibleTabs.length-1:(at+(event.key==='ArrowRight'?1:-1)+visibleTabs.length)%visibleTabs.length;state.tab=visibleTabs[next];renderDetail();$('tab-'+state.tab).focus();}
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
window.addEventListener('liubai-language-change',()=>{renderConnection();if(state.connection!=='error'||state.entries.length)updateView();if(state.detail)renderDetail();});
putIcons();loadLibrary().then(()=>{const guide=new URLSearchParams(location.search).get('guide');if(guide)openHelp(guide);});
