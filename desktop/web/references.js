'use strict';

// 外部原文和拆解一律按文本渲染；这里只调用本机服务，不执行资料中的指令。
(() => {
  const host = $('references-space');
  const ref = {active:false, loaded:false, items:[], categories:[], mode:'discover', category:'all', query:'', favorites:false, selected:null, detail:null, request:0, status:null, poll:null, candidates:[], candidateOrigin:null, relatedEntry:null, preview:null, previewRequest:0, importing:false};
  const esc = escapeHTML;
  const materialNames = {prompt:'提示词',skill:'技能指令',workflow:'制作工作流',method:'设计方法'};
  const selectionNames = {selected:'精选',candidate:'候选',observing:'待观察',rejected:'未采用'};
  const statusNames = {unchanged:'检查成功 · 无变化',changed:'发现变化',failed:'抓取失败',pending:'待分析',partial:'部分完成',success:'检查完成',completed:'检查完成',running:'检查中',skipped:'已跳过',interrupted:'已中断'};
  const weekdays = ['星期一','星期二','星期三','星期四','星期五','星期六','星期日'];
  const nameOf = id => ref.categories.find(item=>item.id===id)?.name || categoryName(id);
  const textOf = value => {
    if(value===null || value===undefined || value==='') return '未说明';
    if(typeof value==='string') return value;
    if(Array.isArray(value)) return value.map(textOf).join('\n');
    if(typeof value==='object') return value.note || value.reason || value.text || Object.entries(value).map(([key,val])=>`${key}：${textOf(val)}`).join('\n');
    return String(value);
  };
  const timeOf = value => {if(!value)return '尚无记录';const date=new Date(value);return Number.isNaN(date.valueOf())?'时间未知':date.toLocaleString('zh-CN',{timeZone:'Asia/Shanghai',year:'numeric',month:'2-digit',day:'2-digit',hour:'2-digit',minute:'2-digit'});};
  const link = (url,label,cls='') => {const safe=safeURL(url);return safe?`<a class="${cls}" href="${esc(safe)}" target="_blank" rel="noopener noreferrer">${esc(label)} ↗</a>`:`<span class="${cls}">${esc(label)}</span>`;};
  const block = (value,cls='') => `<div class="reference-prose ${cls}">${esc(textOf(value))}</div>`;
  const pre = (value,cls='') => `<pre class="reference-code ${cls}">${esc(textOf(value))}</pre>`;
  const button = (action,label,extra='',cls='reference-button') => `<button class="${cls}" data-ref-action="${action}" ${extra}>${label}</button>`;
  const post = (path,data) => api('/api/references/'+path,{method:'POST',headers:{'Content-Type':'application/json','X-Prompt-Library':'1'},body:JSON.stringify(data)});
  function message(text){$('reference-error').textContent=text;$('reference-error').hidden=!text;}
  function failure(error,prefix=''){message(prefix+(navigator.onLine===false?'当前离线。':'')+error.message);}
  function empty(title,body=''){return `<div class="reference-empty"><strong>${esc(title)}</strong>${body?`<p>${esc(body)}</p>`:''}</div>`;}

  host.innerHTML=`<header class="reference-heading"><h1>参考库 <span id="reference-total"></span></h1><button class="reference-button" data-ref-action="add">${icon('plus')}添加来源</button></header>
    <div class="reference-tools"><nav class="reference-tabs" aria-label="参考视图">${[['discover','发现'],['following','已关注'],['updates','更新']].map(([id,label])=>`<button data-ref-mode="${id}" aria-pressed="${id==='discover'}" class="${id==='discover'?'active':''}">${label}</button>`).join('')}</nav><form id="reference-search-form" class="reference-search-form"><div class="search-wrap">${icon('search')}<input id="reference-search" type="search" aria-label="搜索参考库或 GitHub" placeholder="搜索参考或 GitHub" autocomplete="off"></div><button type="submit" id="reference-github-search" class="reference-button">搜索 GitHub</button></form></div>
    <div id="reference-error" class="reference-error" role="alert" hidden></div>
    <div id="reference-browse" class="reference-browse"><div class="reference-filterbar"><label class="reference-select-label"><span class="sr-only">参考分类</span><select id="reference-category" aria-label="参考分类"><option value="all">全部分类</option></select></label><button data-ref-action="favorites" id="reference-favorites" aria-pressed="false" class="reference-button subtle">${icon('star')}收藏</button><span id="reference-filter-count"></span></div><section id="reference-candidates" class="reference-candidates" aria-label="GitHub 搜索结果" hidden></section><div class="reference-workspace"><section class="reference-list" id="reference-list" aria-label="参考列表"></section><section class="reference-detail" id="reference-detail" aria-label="参考详情" aria-busy="false">${empty('选择一份参考')}</section></div></div>
    <section id="reference-updates" class="reference-updates" aria-label="更新与跟踪" hidden></section>`;

  const dialogs=document.createElement('div');
  dialogs.innerHTML=`<dialog id="reference-add-dialog" class="reference-dialog"><div class="dialog-top"><h2>添加 GitHub 来源</h2><button class="icon-button" data-ref-close="reference-add-dialog" aria-label="关闭添加来源">×</button></div><form id="reference-add-form"><label for="reference-source-url">仓库或文件链接</label><input id="reference-source-url" type="url" placeholder="https://github.com/作者/仓库" required><label for="reference-import-category">归入分类</label><select id="reference-import-category"></select><div id="reference-add-error" class="reference-error" role="alert" hidden></div><div id="reference-file-choices"></div><div class="reference-dialog-actions"><button type="button" class="reference-button" data-ref-close="reference-add-dialog">取消</button><button id="reference-add-submit" type="submit" class="reference-button primary">读取来源</button></div></form></dialog>
    <dialog id="reference-adopt-dialog" class="reference-dialog adoption-dialog"><div class="dialog-top"><h2>采用到我的素材</h2><button class="icon-button" data-ref-close="reference-adopt-dialog" aria-label="关闭采用预览">×</button></div><label for="reference-adopt-target">保存位置</label><select id="reference-adopt-target"><option value="">新建素材</option></select><div id="reference-adopt-preview" aria-live="polite"></div><div id="reference-adopt-error" class="reference-error" role="alert" hidden></div><div class="reference-dialog-actions"><button class="reference-button" data-ref-close="reference-adopt-dialog">取消</button><button id="reference-adopt-confirm" class="reference-button primary" data-ref-action="adopt-confirm" disabled>确认采用</button></div></dialog>`;
  document.body.append(dialogs);

  function decorateNavigation(){
    $('reference-space-button').setAttribute('aria-pressed',String(ref.active));
    $('reference-space-button').classList.toggle('active',ref.active);
    $('personal-space-button').setAttribute('aria-pressed',String(!ref.active));
    $('personal-space-button').classList.toggle('active',!ref.active);
    if(ref.active)document.querySelectorAll('#space-nav .active,#category-nav .active').forEach(node=>{node.classList.remove('active');node.removeAttribute('aria-current');});
  }
  async function enter(id=null){
    ref.active=true;$('personal-space').hidden=true;host.hidden=false;decorateNavigation();
    if(!ref.loaded)await refresh(false);
    else if(ref.mode==='updates')await loadStatus();
    if(id){ref.mode='discover';ref.category='all';ref.query='';$('reference-category').value='all';$('reference-search').value='';ref.favorites=false;$('reference-favorites').setAttribute('aria-pressed','false');setMode('discover');await select(id);}
  }
  function leave(){ref.active=false;$('personal-space').hidden=false;host.hidden=true;clearTimeout(ref.poll);decorateNavigation();renderNavigation();}
  async function refresh(reselect=true){
    $('refresh-button').disabled=true;message('');
    if(!ref.loaded)$('reference-list').innerHTML=empty('正在读取参考…');
    try{
      const data=await api('/api/references');ref.items=data.references||[];ref.categories=data.categories||state.categories;ref.loaded=true;
      if(data.schedule)ref.status=data.schedule;
      renderScheduledCandidates();
      renderFilters();renderList();
      if(reselect&&ref.selected&&ref.items.some(item=>item.id===ref.selected))await select(ref.selected,false,ref.detail?.snapshot?.id);
      if(ref.mode==='updates')await loadStatus();
    }catch(error){failure(error);if(!ref.loaded)$('reference-list').innerHTML=empty('暂时无法读取参考','点击顶部刷新重试。');}
    finally{$('refresh-button').disabled=false;}
  }
  function renderFilters(){
    const options=ref.categories.map(item=>`<option value="${esc(item.id)}">${esc(item.name)}</option>`).join('');
    $('reference-category').innerHTML=`<option value="all">全部分类</option>${options}`;$('reference-category').value=ref.category;
    $('reference-import-category').innerHTML=options;$('reference-import-category').value=ref.category==='all'?'uncategorized':ref.category;
    $('reference-total').textContent=ref.items.length;
  }
  function visibleItems(){
    const words=ref.query.toLocaleLowerCase().trim().split(/\s+/).filter(Boolean);
    return ref.items.filter(item=>(ref.mode!=='following'||item.followed)&&(ref.category==='all'||item.category_id===ref.category)&&(!ref.favorites||item.favorite)&&words.every(word=>[item.title,item.summary,item.id,item.source?.repository,(item.tags||[]).join(' '),nameOf(item.category_id),item.search_text].join(' ').toLocaleLowerCase().includes(word)));
  }
  function renderList(){
    const rows=visibleItems();$('reference-filter-count').textContent=`${rows.length} 份`;
    $('reference-list').innerHTML=rows.length?rows.map(item=>`<button class="reference-card ${ref.selected===item.id?'selected':''}" data-ref-id="${esc(item.id)}" aria-pressed="${ref.selected===item.id}"><span class="reference-card-meta"><span>${esc(nameOf(item.category_id))}</span><span>${esc(materialNames[item.material_type]||'参考')}</span></span><h2>${esc(item.title)}</h2><span class="reference-repository">${esc(item.source?.repository||'来源待核对')}</span><span class="reference-card-bottom"><span class="reference-badge">${item.analysis_status==='ready'?esc(selectionNames[item.selection_status]||'已拆解'):'待分析'}</span>${item.favorite?`<span aria-label="已收藏">${icon('star')}</span>`:''}${item.followed?'<span class="reference-following">已关注</span>':''}</span></button>`).join(''):empty(ref.mode==='following'?'还没有关注的来源':'没有匹配的参考',ref.mode==='following'?'在参考详情中点击“关注来源”。':'调整关键词或分类，也可搜索 GitHub。');
    if(!rows.some(item=>item.id===ref.selected)){
      if(rows.length)select(rows[0].id,false);
      else{ref.selected=null;ref.detail=null;ref.request++;$('reference-detail').innerHTML=empty('选择一份参考');$('reference-detail').setAttribute('aria-busy','false');document.querySelector('.reference-workspace').classList.remove('show-detail');}
    }
  }
  function setMode(mode){
    ref.mode=mode;document.querySelectorAll('[data-ref-mode]').forEach(node=>{const selected=node.dataset.refMode===mode;node.classList.toggle('active',selected);node.setAttribute('aria-pressed',String(selected));});
    $('reference-browse').hidden=mode==='updates';$('reference-updates').hidden=mode!=='updates';$('reference-search-form').hidden=mode==='updates';
    if(mode==='updates')loadStatus();else{clearTimeout(ref.poll);renderList();if(mode==='discover')renderScheduledCandidates();}
  }
  async function select(id,reveal=true,snapshot=null){
    ref.selected=id;ref.detail=null;const request=++ref.request;$('reference-detail').setAttribute('aria-busy','true');$('reference-detail').innerHTML=empty('正在读取原文…');
    document.querySelectorAll('[data-ref-id]').forEach(node=>{node.classList.toggle('selected',node.dataset.refId===id);node.setAttribute('aria-pressed',String(node.dataset.refId===id));});
    if(reveal)document.querySelector('.reference-workspace').classList.add('show-detail');
    try{const data=await api('/api/references/'+encodeURIComponent(id)+(snapshot?'?snapshot='+encodeURIComponent(snapshot):''));if(request!==ref.request)return;ref.detail=data;renderReference();}
    catch(error){if(request!==ref.request)return;$('reference-detail').innerHTML=empty('参考未能打开',error.message)+button('retry-detail','重试');failure(error);}
    finally{if(request===ref.request)$('reference-detail').setAttribute('aria-busy','false');}
  }
  function section(title,content){return `<section class="reference-section"><h3>${title}</h3>${content}</section>`;}
  function renderAnalysis(a){
    if(!a)return section('写法拆解',`<div class="reference-pending">待分析</div><p class="reference-prose">这份快照还没有完成拆解，通用模板与采用暂不可用。</p>`);
    const structure=(a.structure||[]).map(row=>`<tr><th scope="row">${esc(row.part)}</th><td>${esc(textOf(row.observation))}</td><td>${esc(textOf(row.evidence))}</td></tr>`).join('');
    const keys=(a.key_sentences||[]).map((row,index)=>`<article class="reference-key"><blockquote>${esc(row.quote)}</blockquote><button class="reference-inline" data-ref-quote="${index}">${esc(row.location||'定位到原文')} ↑</button><dl><dt>作用</dt><dd>${esc(textOf(row.reason))}</dd><dt>删改后可能</dt><dd>${esc(textOf(row.without))}</dd></dl></article>`).join('');
    const reason=a.design_reasoning||{},sample=a.example||{},contrast=a.counterexample||{},loop=a.loop||{};
    const dimensions=[['来源成熟度',a.maturity],['任务匹配度',a.fit],['使用证据',a.evidence],['本库实测',{reason:a.evaluation_status==='untested'?'尚未进行真实任务评测':'请查看对应评测记录'}]];
    const qualityNames={goal_clarity:'目标明确',input_clarity:'输入明确',constraint_quality:'约束合理',output_checkability:'输出可检查',usage_evidence:'使用证据',task_fit:'任务适配'};
    return section('适用场景',block(a.use_cases)+`<h4>不适用情境</h4>`+block(a.not_for))
      +section('结构地图',`<div class="reference-table-wrap"><table class="reference-table"><thead><tr><th>模块</th><th>写法</th><th>原文依据</th></tr></thead><tbody>${structure}</tbody></table></div>`)
      +section('关键句的作用',keys||block('原文没有独立关键句记录。'))
      +section('设计依据',`<h4>作者公开说明</h4>${block(reason.author_stated)}<h4>整理者分析</h4>${block(reason.inferred)}<h4>实际证据</h4>${block(reason.evidence)}`)
      +section('通用模板',button('copy-template',`${icon('copy')}复制模板`,'','reference-button section-copy')+pre(a.template))
      +section('改写示例',`<span class="reference-badge">示意 · 未实测</span><h4>${esc(sample.task||'应用示例')}</h4>${pre(sample.prompt)}<h4>修改理由</h4>${block(sample.changes)}`)
      +section('对照与反例',`<span class="reference-badge">预期差异 · 未实测</span><h4>调整前</h4>${pre(contrast.before)}<h4>调整后</h4>${pre(contrast.after)}<h4>唯一改变的变量</h4>${block(contrast.changed_variable)}<h4>预期影响</h4>${block(contrast.expected_effect)}`)
      +section('Loop',`<div class="reference-loop-meta"><span>${esc({none:'无需循环',conditional:'按条件启用',recommended:'建议使用'}[loop.applicability]||textOf(loop.applicability))}</span>${loop.max_rounds?`<span>最多 ${esc(loop.max_rounds)} 轮</span>`:''}${button('copy-loop',`${icon('copy')}复制 Loop`,'','reference-button subtle')}</div>${pre(loop.text||'单次处理，无需循环。')}`)
      +section('筛选依据',`<dl class="reference-quality">${dimensions.map(([title,value])=>`<div><dt>${title}</dt><dd>${esc(textOf(value))}</dd></div>`).join('')}</dl><details class="reference-subdetails"><summary>六项质量检查</summary><dl class="reference-quality">${Object.entries(a.quality_review||{}).map(([key,value])=>`<div><dt>${esc(qualityNames[key]||key)}</dt><dd>${esc(textOf(value))}</dd></div>`).join('')}</dl></details>`);
  }
  function renderReference(){
    const d=ref.detail;if(!d)return;const item=d.item||{},snapshot=d.snapshot||{},source=snapshot.source||item.source||{},a=d.analysis;
    const original=typeof d.original==='string'?d.original:'';const lines=original.split('\n').length;const long=lines>14||original.length>1600;
    const excerpt=snapshot.is_excerpt||source.is_excerpt||source.retention==='excerpt'||source.extraction?.kind==='notebook_cells'||['lines','notebook_cells'].includes(source.extraction?.type);
    const originalTitle=excerpt?'原文节选':item.material_type==='method'?'设计方法原文':item.material_type==='workflow'?'工作流原文':'原文';
    const preserved=original.length>0;const old=snapshot.id&&snapshot.id!==item.current_snapshot_id;
    const snapshots=d.snapshots||[];const diff=d.diff||{};
    $('reference-detail').innerHTML=`<header class="reference-detail-header"><div class="reference-detail-controls"><button class="icon-button reference-back" data-ref-action="back" aria-label="返回参考列表">${icon('back')}</button><span class="reference-badge">${esc(nameOf(item.category_id))}</span><span class="reference-badge">${esc(materialNames[item.material_type]||'参考')}</span><div class="reference-actions">${button('favorite',icon('star'),`aria-label="${item.favorite?'取消收藏参考':'收藏参考'}" aria-pressed="${!!item.favorite}"`,'icon-button '+(item.favorite?'saved':''))}${button('follow',item.followed?'已关注':'关注来源',`aria-pressed="${!!item.followed}"`)}${button('adopt','采用',old?'disabled title="请切换到最新快照后采用"':'','reference-button primary')}</div></div><h2>${esc(item.title)}</h2><div class="reference-source-line">${link(snapshot.source_url||source.url,source.repository||'查看来源')}<code title="固定 commit">${esc((snapshot.commit||source.commit||'版本待核对').slice(0,12))}</code><span>${esc(source.license||'许可待核对')}</span>${old?'<span class="reference-badge">历史快照</span>':''}</div></header>
      <div class="reference-reading" id="reference-reading"><section class="reference-section reference-original-section" aria-labelledby="reference-original-title"><div class="reference-section-top"><h3 id="reference-original-title">${originalTitle}</h3>${button('copy-original',`${icon('copy')}复制原文`,preserved?'':'disabled')}</div>${preserved?`<p class="reference-original-range">${source.source_span?esc(textOf(source.source_span)):excerpt?esc(textOf(source.excerpt_scope||snapshot.excerpt_scope||'节选范围见来源记录')):'完整已收录原文'} · ${lines} 行${long?' · 区内可滚动':''}</p><pre id="reference-original" class="reference-original ${long?'scrollable':''}" tabindex="0" aria-label="${originalTitle}，${lines} 行">${esc(original)}</pre>${long?button('expand-original','展开全文','aria-expanded="false" aria-controls="reference-original"','reference-inline'):''}`:`<div class="reference-pending">原文未收录</div>${block(snapshot.original_unavailable_reason||source.retention_reason||snapshot.retention_reason||'复制许可尚未确认，仅保留来源信息。')}${link(source.url,'查看来源')}`}${source.license_status!=='allowed'?`<p class="reference-license-note">${source.license_status==='restricted'?'使用受限，请核对来源许可。':'复制与采用条件待核对。'}</p>`:''}</section>
      ${a?.translation?section('中文译文',pre(a.translation)):''}${renderAnalysis(a)}
      ${section('版本变化',`<label class="reference-version-picker" for="reference-snapshot">来源快照<select id="reference-snapshot">${snapshots.map(s=>`<option value="${esc(s.id)}" ${s.id===snapshot.id?'selected':''}>${esc(s.id)} · ${esc((s.commit||'').slice(0,8))} · ${dateLabel(s.created_at)}</option>`).join('')}</select></label>${diff.text?`<p class="reference-prose">${esc(diff.from_snapshot||'前版')} → ${esc(diff.to_snapshot||snapshot.id)}</p>${pre(diff.text,'reference-diff')}${diff.impact?`<h4>影响说明</h4>${block(diff.impact)}`:''}${diff.analysis_status==='pending'?'<p class="reference-prose">变更影响待分析。</p>':''}`:block('当前快照没有可展示的内容差异。')}`)}
      ${section('来源与关联',`<dl class="reference-quality"><div><dt>来源文件</dt><dd>${esc(source.path||'未说明')}</dd></div><div><dt>固定版本</dt><dd>${esc(snapshot.commit||source.commit||'未说明')}</dd></div><div><dt>内容校验</dt><dd>${esc(snapshot.sha256||'未说明')}</dd></div><div><dt>最近成功检查</dt><dd>${timeOf(item.last_success)}</dd></div><div><dt>收录时间</dt><dd>${timeOf(snapshot.created_at||source.retrieved_at||item.created_at)}</dd></div><div><dt>拆解版本</dt><dd>${esc(a?.version||'待分析')}</dd></div></dl>${(item.related_ids||[]).length?`<div class="reference-related-links">${item.related_ids.map(id=>button('open-personal',esc(id),`data-personal-id="${esc(id)}"`)).join('')}</div>`:''}`)}
      </div><footer class="reference-detail-footer"><a class="reference-button" href="/download/reference/${encodeURIComponent(item.id)}/card?snapshot=${encodeURIComponent(snapshot.id||item.current_snapshot_id)}" download>${icon('download')}导出完整卡片</a><span>实测状态：${item.evaluation_status==='untested'?'待实测':'查看记录'}</span></footer>`;
  }
  async function copyReference(kind){
    const d=ref.detail;if(!d)return;const value=kind==='original'?d.original:kind==='loop'?(d.analysis?.loop?.text||d.loop?.text):(d.analysis?.template||d.template);
    if(!value)return toast('当前内容尚不可复制');
    try{await navigator.clipboard.writeText(value);toast('已复制'+({original:'原文',template:'模板',loop:'Loop'}[kind]));}
    catch{const area=document.createElement('textarea');area.value=value;area.setAttribute('aria-label','待复制参考');document.body.append(area);area.select();const success=document.execCommand('copy');area.remove();toast(success?'已复制':'复制未成功，请选中文本后按 Ctrl+C');}
  }
  async function flag(kind,node){
    if(!ref.detail)return;const id=ref.detail.item.id;node.disabled=true;const scroll=$('reference-reading')?.scrollTop||0;
    try{const data=await post('flags',{id,[kind]:!ref.detail.item[kind]});const updated=data.item;const index=ref.items.findIndex(item=>item.id===id);if(index>=0)ref.items[index]={...ref.items[index],...updated};if(ref.detail?.item.id===id)ref.detail.item=updated;renderList();if(ref.detail?.item.id===id){renderReference();$('reference-reading').scrollTop=scroll;}toast(kind==='favorite'?(updated.favorite?'已收藏':'已取消收藏'):(updated.followed?'已关注来源':'已取消关注'));}
    catch(error){failure(error,'未保存：');node.disabled=false;}
  }
  function renderScheduledCandidates(){
    if(ref.candidateOrigin==='manual'||!ref.status?.discovery?.candidates?.length)return;
    ref.candidates=ref.status.discovery.candidates;ref.candidateOrigin='scheduled';renderCandidates();
  }
  function renderCandidates(partial=false){
    $('reference-candidates').hidden=false;
    $('reference-candidates').innerHTML=`<div class="reference-candidate-heading"><strong>${ref.candidateOrigin==='scheduled'?'定期发现':'GitHub 候选'} <span>${ref.candidates.length}</span></strong>${button('close-candidates','关闭结果','','reference-inline')}</div>${partial?'<p class="reference-prose">搜索部分完成，可稍后重试。</p>':''}${ref.candidates.length?`<div class="reference-candidate-list">${ref.candidates.map((item,index)=>`<article><div><h3>${link(item.url,item.repository||item.title)}</h3>${block(item.description||item.reason||'请查看来源文件')}<span class="reference-candidate-meta">${esc(item.license||'许可待核对')} · ${item.updated_at?dateLabel(item.updated_at):'维护时间待核对'}</span></div>${button('candidate-files','查看文件',`data-candidate-index="${index}"`)}</article>`).join('')}</div>`:empty('没有找到可靠匹配','换一个更具体的任务词再试。')}`;
  }
  async function discover(event){
    event?.preventDefault();const query=$('reference-search').value.trim();if(!query){$('reference-search').focus();return toast('先输入任务或关键词');}
    const node=$('reference-github-search');node.disabled=true;node.textContent='搜索中…';message('');$('reference-candidates').hidden=false;$('reference-candidates').innerHTML=empty('正在搜索 GitHub…');
    try{const data=await post('discover',{query,category_id:ref.category==='all'?undefined:ref.category,entry_id:ref.relatedEntry||undefined});ref.candidates=data.candidates||[];ref.candidateOrigin='manual';renderCandidates(data.partial);
    }catch(error){$('reference-candidates').innerHTML=empty('GitHub 搜索失败',error.message);failure(error);}
    finally{node.disabled=false;node.textContent='搜索 GitHub';}
  }
  function openAdd(url=''){$('reference-source-url').value=url;$('reference-file-choices').replaceChildren();$('reference-add-error').hidden=true;$('reference-add-dialog').showModal();$('reference-source-url').focus();}
  async function importSource(url){
    if(ref.importing)return;ref.importing=true;
    const submit=$('reference-add-submit');submit.disabled=true;$('reference-add-error').hidden=true;
    $('reference-file-choices').setAttribute('aria-busy','true');
    try{const result=await post('import',{url,category_id:$('reference-import-category').value});
      if(result.choose_file){const files=result.candidates||[];$('reference-file-choices').innerHTML=`<h3>选择来源文件</h3><div class="reference-file-list">${files.length?files.map(file=>`<button type="button" data-import-url="${esc(file.url)}" class="reference-file"><strong>${esc(file.title||file.path)}</strong><span>${esc(file.path)}</span></button>`).join(''):empty('未找到可归档文件','请直接添加具体文件链接。')}</div>`;}
      else{$('reference-add-dialog').close();toast(result.duplicate?'该来源已在参考库中':'来源已归档，等待拆解');ref.query='';$('reference-search').value='';ref.category='all';ref.favorites=false;setMode('discover');await refresh(false);if(result.id)await select(result.id);}
    }catch(error){$('reference-add-error').textContent=error.message;$('reference-add-error').hidden=false;}
    finally{ref.importing=false;submit.disabled=false;$('reference-file-choices').setAttribute('aria-busy','false');}
  }
  async function openAdopt(){
    if(!ref.detail)return;ref.preview=null;$('reference-adopt-target').innerHTML='<option value="">新建素材</option>'+state.entries.map(item=>`<option value="${esc(item.id)}">${esc(item.id+' · '+item.title)}（新增版本）</option>`).join('');$('reference-adopt-dialog').showModal();await previewAdoption();
  }
  async function previewAdoption(){
    if(!ref.detail)return;const request=++ref.previewRequest;ref.preview=null;$('reference-adopt-confirm').disabled=true;$('reference-adopt-preview').innerHTML=empty('正在读取采用预览…');$('reference-adopt-error').hidden=true;
    try{const preview=await post('adopt-preview',{id:ref.detail.item.id,target_id:$('reference-adopt-target').value||null});if(request!==ref.previewRequest)return;ref.preview=preview;if(preview.target_id)$('reference-adopt-target').value=preview.target_id;
      const previewSource=preview.source||ref.detail.item.source||{};
      const usageConditions=[['使用限制',previewSource.usage_restrictions],['适用模型',previewSource.applicable_models],['所需依赖',previewSource.dependencies]].filter(([,value])=>value!==null&&value!==undefined&&value!==''&&(!Array.isArray(value)||value.length>0));
      $('reference-adopt-preview').innerHTML=`<h3>${esc(preview.title)}</h3><div class="reference-preview-meta"><span>${esc(nameOf(preview.category_id))}</span><span>${esc(preview.reference_id)} / ${esc(preview.snapshot_id)}</span><span>${esc(preview.license||'许可待核对')}</span><span>待实测</span></div>${preview.can_adopt?'':`<p class="reference-error">${esc(preview.reason||'当前参考尚不满足采用条件。')}</p>`}<h4>来源</h4>${link(previewSource.url,previewSource.repository||'查看原始来源')}${usageConditions.length?`<dl class="reference-quality reference-usage-conditions">${usageConditions.map(([label,value])=>`<div><dt>${label}</dt><dd>${esc(textOf(value))}</dd></div>`).join('')}</dl>`:''}<h4>改编内容</h4>${preview.template?pre(preview.template):block('尚无可采用的通用模板。')}<p class="reference-prose">${preview.target_id?'保留已有原文与历史，追加一个优化版本。':'新条目保留参考原文、改编模板与来源关系。'}</p>`;
      $('reference-adopt-confirm').disabled=!preview.can_adopt;
    }catch(error){if(request!==ref.previewRequest)return;$('reference-adopt-preview').replaceChildren();$('reference-adopt-error').textContent=error.message;$('reference-adopt-error').hidden=false;}
  }
  async function adopt(){
    const preview=ref.preview;if(!preview?.can_adopt)return;const node=$('reference-adopt-confirm');node.disabled=true;$('reference-adopt-target').disabled=true;
    try{const result=await post('adopt',{id:preview.reference_id,target_id:preview.target_id||null,expected_snapshot:preview.snapshot_id,expected_analysis_version:preview.analysis_version});$('reference-adopt-dialog').close();toast(result.duplicate?'已采用过此版本':`已保存为 ${result.entry_id} · ${result.version}`);leave();await loadLibrary();if(result.entry_id)await selectEntry(result.entry_id);ref.loaded=false;}
    catch(error){$('reference-adopt-error').textContent=error.message;$('reference-adopt-error').hidden=false;node.disabled=false;}
    finally{$('reference-adopt-target').disabled=false;}
  }
  function renderStatus(){
    const s=ref.status;if(!s)return;
    const stateLabel=s.running?'检查中':!s.enabled?'采集已暂停':s.registration_status!=='active'?'定时执行待就绪':'定时采集已启用';
    const runs=s.runs||[],updates=s.updates||[];
    $('reference-updates').innerHTML=`<div class="reference-schedule"><div class="reference-schedule-heading"><h2>${stateLabel}</h2><div>${button('check-now',s.running?'检查中…':'立即检查',s.running?'disabled':'')}${button('schedule-toggle',s.enabled?'暂停采集':'恢复采集')}</div></div><form id="reference-schedule-form" class="reference-schedule-form"><label>频率<select id="reference-frequency" name="frequency"><option value="daily" ${s.frequency==='daily'?'selected':''}>每天</option><option value="weekly" ${s.frequency==='weekly'?'selected':''}>每周</option></select></label><label id="reference-weekday-label" ${s.frequency==='weekly'?'':'hidden'}>日期<select id="reference-weekday" name="weekday">${weekdays.map((day,index)=>`<option value="${index}" ${Number(s.weekday??6)===index?'selected':''}>${day}</option>`).join('')}</select></label><span class="reference-fixed-time">09:00 · Asia/Shanghai</span><button class="reference-button" type="submit">保存频率</button></form><dl class="reference-status-grid"><div><dt>最近尝试</dt><dd>${timeOf(s.last_attempt)}</dd></div><div><dt>最近成功</dt><dd>${timeOf(s.last_success)}</dd></div><div><dt>下次计划</dt><dd>${s.enabled?timeOf(s.next_run):'已暂停'}</dd></div><div><dt>待分析</dt><dd>${typeof s.pending_analysis==='number'?s.pending_analysis:Array.isArray(s.pending_analysis)?s.pending_analysis.length:0} 份</dd></div></dl>${s.last_error?`<div class="reference-error">${esc(s.last_error)}</div>`:''}<p class="reference-dependency">${esc(s.dependency||'执行依赖本机与 Codex；关闭或离线后恢复时合并补跑。')}</p><details class="reference-subdetails"><summary>执行方式与单次上限</summary><dl class="reference-quality"><div><dt>调度入口</dt><dd>${esc(s.engine||'尚未配置')} · ${s.registration_status==='active'?'已注册':'待注册'}</dd></div>${Object.entries(s.limits||{}).map(([key,value])=>`<div><dt>${esc({repositories:'仓库',max_repositories:'仓库',files:'文件',max_files:'文件',max_file_bytes:'单文件字节',max_bytes:'单文件字节',max_seconds:'运行秒数',max_retries:'失败重试',max_analyses:'深度分析',max_analysis:'深度分析'}[key]||key)}</dt><dd>${esc(textOf(value))}</dd></div>`).join('')}</dl></details></div>
      <section class="reference-update-section"><h2>来源动态</h2>${updates.length?updates.map(update=>`<button class="reference-update-row" data-open-reference="${esc(update.reference_id)}"><span><strong>${esc(update.title||update.reference_id)}</strong><small>${esc(statusNames[update.status]||update.status)}${update.error?' · '+esc(update.error):''}</small></span><time>${timeOf(update.checked_at)}</time>${icon('external')}</button>`).join(''):empty('还没有来源动态')}</section>
      <section class="reference-update-section"><h2>运行记录</h2>${runs.length?`<div class="reference-table-wrap"><table class="reference-table"><thead><tr><th>开始时间</th><th>触发</th><th>结果</th><th>检查详情</th></tr></thead><tbody>${runs.map(run=>`<tr><td>${timeOf(run.started_at)}</td><td>${esc({manual:'手动',scheduled:'定时',heartbeat:'定时',codex_heartbeat:'定时',codex_heartbeat_acceptance:'定时验收',catchup:'补跑'}[run.trigger]||run.trigger)}</td><td>${esc(statusNames[run.status]||run.status)}</td><td>无变化 ${Number(run.unchanged)||0} · 变化 ${Number(run.changed)||0} · 失败 ${Number(run.failed)||0}${run.errors?.length?`<details><summary>失败原因</summary>${block(run.errors)}</details>`:''}</td></tr>`).join('')}</tbody></table></div>`:empty('还没有执行记录')}</section>`;
  }
  async function loadStatus(){
    clearTimeout(ref.poll);
    if(!ref.status)$('reference-updates').innerHTML=empty('正在读取跟踪状态…');
    try{ref.status=await api('/api/references/status');if(!$('reference-schedule-form')?.contains(document.activeElement))renderStatus();if(ref.active&&ref.mode==='updates'&&ref.status.running)ref.poll=setTimeout(loadStatus,3000);}
    catch(error){failure(error,'状态读取失败：');if(!ref.status)$('reference-updates').innerHTML=empty('状态暂不可用','点击顶部刷新重试。');}
  }
  async function checkNow(node){node.disabled=true;message('');try{const data=await post('check',{force:true});toast(data.started?'已开始检查':data.reason==='busy'?'已有检查正在运行':data.reason||'检查未启动');await loadStatus();}catch(error){failure(error);node.disabled=false;}}
  async function saveSchedule(values,node){node.disabled=true;message('');try{const status=await post('schedule',values);ref.status=status.schedule||status;renderStatus();toast(values.enabled===false?'采集已暂停':values.enabled===true?'采集已恢复':'更新频率已保存');}catch(error){failure(error);node.disabled=false;}}

  async function renderRelated(entryId){
    const content=$('detail-content');if(!content)return;const target=document.createElement('section');target.className='personal-reference-links';target.id='personal-reference-links';content.append(target);
    try{const data=await api('/api/references/related/'+encodeURIComponent(entryId));if(state.selected!==entryId||!target.isConnected)return;const rows=(data.references||[]).slice(0,3);target.innerHTML=`<h3>参考写法</h3>${rows.length?rows.map(item=>`<button data-open-reference="${esc(item.id)}"><strong>${esc(item.title)}</strong><span>${esc(item.reason||'查看原文与拆解')}</span></button>`).join(''):'<p>暂未找到可靠匹配。</p>'}<button class="reference-inline" data-discover-for="${esc(entryId)}">为这条素材寻找参考 ↗</button>`;}
    catch{if(target.isConnected)target.innerHTML='<p>参考关联暂不可用。</p>';}
  }
  document.addEventListener('click',async event=>{
    const close=event.target.closest('[data-ref-close]');if(close){$(close.dataset.refClose).close();return;}
    const mode=event.target.closest('[data-ref-mode]');if(mode){setMode(mode.dataset.refMode);return;}
    const row=event.target.closest('[data-ref-id]');if(row){select(row.dataset.refId);return;}
    const open=event.target.closest('[data-open-reference]');if(open){await enter(open.dataset.openReference);return;}
    const related=event.target.closest('[data-discover-for]');if(related){ref.relatedEntry=related.dataset.discoverFor;const entry=state.entries.find(item=>item.id===ref.relatedEntry);await enter();setMode('discover');ref.category=entry?.category_id||'all';$('reference-category').value=ref.category;ref.query=entry?.title||'';$('reference-search').value=ref.query;renderList();discover();return;}
    const file=event.target.closest('[data-import-url]');if(file){file.disabled=true;await importSource(file.dataset.importUrl);file.disabled=false;return;}
    const quote=event.target.closest('[data-ref-quote]');if(quote){const q=ref.detail?.analysis?.key_sentences?.[Number(quote.dataset.refQuote)]?.quote||'';const original=$('reference-original');if(original){const raw=ref.detail.original;const pos=raw.indexOf(q);if(pos>=0&&q){const mark=document.createElement('mark');mark.className='reference-quote-mark';mark.textContent=q;original.replaceChildren(document.createTextNode(raw.slice(0,pos)),mark,document.createTextNode(raw.slice(pos+q.length)));mark.scrollIntoView({block:'center'});}else{$('reference-reading').scrollTop=0;toast('原文中未匹配到完整句子，请按标注位置核对。');}original.focus({preventScroll:true});}return;}
    const action=event.target.closest('[data-ref-action]');if(!action)return;const name=action.dataset.refAction;
    if(name==='back')document.querySelector('.reference-workspace').classList.remove('show-detail');
    if(name==='retry-detail'&&ref.selected)select(ref.selected);
    if(name.startsWith('copy-'))copyReference(name.slice(5));
    if(name==='favorite')flag('favorite',action);
    if(name==='follow')flag('followed',action);
    if(name==='favorites'){ref.favorites=!ref.favorites;action.setAttribute('aria-pressed',String(ref.favorites));renderList();}
    if(name==='expand-original'){const expanded=action.getAttribute('aria-expanded')!=='true';action.setAttribute('aria-expanded',String(expanded));action.textContent=expanded?'收起全文':'展开全文';$('reference-original').classList.toggle('expanded',expanded);}
    if(name==='add')openAdd();
    if(name==='candidate-files'){const candidate=ref.candidates[Number(action.dataset.candidateIndex)];if(candidate){openAdd(candidate.url);await importSource(candidate.url);}}
    if(name==='close-candidates')$('reference-candidates').hidden=true;
    if(name==='adopt')openAdopt();
    if(name==='adopt-confirm')adopt();
    if(name==='open-personal'){leave();state.category='all';state.view='all';state.query='';$('search').value='';updateView();selectEntry(action.dataset.personalId);}
    if(name==='check-now')checkNow(action);
    if(name==='schedule-toggle')saveSchedule({enabled:!ref.status?.enabled},action);
  });
  document.addEventListener('change',event=>{
    if(event.target.id==='reference-snapshot')select(ref.selected,false,event.target.value);
    if(event.target.id==='reference-frequency')$('reference-weekday-label').hidden=event.target.value!=='weekly';
  });
  document.addEventListener('focusout',event=>{if(event.target.closest('#reference-schedule-form'))setTimeout(()=>{if(ref.active&&ref.mode==='updates'&&ref.status&&!$('reference-schedule-form')?.contains(document.activeElement))renderStatus();},0);});
  document.addEventListener('submit',event=>{if(event.target.id==='reference-schedule-form'){event.preventDefault();saveSchedule({frequency:$('reference-frequency').value,weekday:Number($('reference-weekday').value)},event.target.querySelector('button[type="submit"]'));}});
  $('reference-search-form').addEventListener('submit',discover);
  $('reference-search').addEventListener('input',event=>{ref.query=event.target.value;ref.relatedEntry=null;renderList();});
  $('reference-category').addEventListener('change',event=>{ref.category=event.target.value;renderList();});
  $('reference-add-form').addEventListener('submit',event=>{event.preventDefault();importSource($('reference-source-url').value.trim());});
  $('reference-adopt-target').addEventListener('change',previewAdoption);
  $('reference-space-button').addEventListener('click',()=>enter());$('personal-space-button').addEventListener('click',leave);
  window.addEventListener('offline',()=>{if(ref.active)message('当前离线。已打开的参考仍可阅读，联网后点击刷新。');});
  window.ReferenceLibrary={active:()=>ref.active,enter,leave,refresh,decorateNavigation,renderRelated};
  if(state.detail)renderRelated(state.detail.item.id);
})();
