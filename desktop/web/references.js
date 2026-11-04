'use strict';

// 外部原文和拆解一律按文本渲染；这里只调用本机服务，不执行资料中的指令。
(() => {
  const host = $('references-space');
  const ref = {active:false, loaded:false, items:[], categories:[], mode:'discover', category:'all', query:'', favorites:false, selected:null, detail:null, request:0, status:null, poll:null, candidates:[], candidateOrigin:null, relatedEntry:null, preview:null, previewRequest:0, importing:false};
  const esc = escapeHTML;
  const errorText = (error,fallback='The reference request failed. Try again.') => window.LiubaiI18n.error(window.LiubaiLanguage||'zh',error?.message||String(error),fallback);
  const adoptionReason = reason => {
    if(reason==='许可尚未明确允许采用原文')return ui(reason,'The license does not clearly permit reuse of the original.');
    if(reason==='此快照待分析，完成拆解和模板后才能采用')return ui(reason,'This snapshot needs a design analysis and template before it can be reused.');
    return reason||ui('当前参考尚不满足采用条件。','This reference is ineligible for reuse at the moment.');
  };
  const relatedReason = reason => {
    if(!reason)return ui('查看原文与拆解','View original and analysis');
    if(window.LiubaiLanguage!=='en')return reason;
    const parts=reason.match(/^(已有关联素材记录)?(?:；)?(同属当前任务分类)?(?:；)?(?:共同标签：(.*))?$/u);
    if(!parts)return reason;
    return [parts[1]&&'Linked to this item',parts[2]&&'Same category',parts[3]&&'Shared tags: '+parts[3]].filter(Boolean).join(' · ');
  };
  const materialNames = () => ({prompt:ui("提示词","Prompt"),skill:ui("技能指令","Skill instructions"),workflow:ui("制作工作流","Production workflow"),method:ui("设计方法","Design method")});
  const selectionNames = () => ({selected:ui("精选","Selected"),candidate:ui("候选","Candidate"),observing:ui("待观察","Under review"),rejected:ui("未采用","Passed over")});
  const statusNames = () => ({unchanged:ui("检查成功 · 无变化","Checked · no changes"),changed:ui("发现变化","Changes found"),failed:ui("抓取失败","Fetch failed"),pending:ui("待分析","Analysis pending"),partial:ui("部分完成","Partially complete"),success:ui("检查完成","Check complete"),completed:ui("检查完成","Check complete"),running:ui("检查中","Checking"),skipped:ui("已跳过","Skipped"),interrupted:ui("已中断","Interrupted")});
  const weekdays = () => [ui("星期一","Monday"),ui("星期二","Tuesday"),ui("星期三","Wednesday"),ui("星期四","Thursday"),ui("星期五","Friday"),ui("星期六","Saturday"),ui("星期日","Sunday")];
  const nameOf = id => ref.categories.find(item=>item.id===id)?.name || categoryName(id);
  const textOf = value => {
    if(value===null || value===undefined || value==='') return ui("未说明","Unspecified");
    if(typeof value==='string') return value;
    if(Array.isArray(value)) return value.map(textOf).join('\n');
    if(typeof value==='object') return value.note || value.reason || value.text || Object.entries(value).map(([key,val])=>`${key}：${textOf(val)}`).join('\n');
    return String(value);
  };
  const timeOf = value => {if(!value)return ui('尚无记录','No record');const date=new Date(value);return Number.isNaN(date.valueOf())?ui('时间未知','Unknown time'):date.toLocaleString(window.LiubaiLanguage==='en'?'en':'zh-CN',{year:'numeric',month:'2-digit',day:'2-digit',hour:'2-digit',minute:'2-digit'});};
  const link = (url,label,cls='') => {const safe=safeURL(url);return safe?`<a class="${cls}" href="${esc(safe)}" target="_blank" rel="noopener noreferrer">${esc(label)} ↗</a>`:`<span class="${cls}">${esc(label)}</span>`;};
  const block = (value,cls='') => `<div class="reference-prose ${cls}">${esc(textOf(value))}</div>`;
  const pre = (value,cls='') => `<pre class="reference-code ${cls}">${esc(textOf(value))}</pre>`;
  const button = (action,label,extra='',cls='reference-button') => `<button class="${cls}" data-ref-action="${action}" ${extra}>${label}</button>`;
  const post = (path,data) => api('/api/references/'+path,{method:'POST',headers:{'Content-Type':'application/json','X-Prompt-Library':'1'},body:JSON.stringify(data)});
  function message(text){$('reference-error').textContent=text;$('reference-error').hidden=!text;}
  function failure(error,prefix=''){message(prefix+(navigator.onLine===false?ui("当前离线。","You are offline. "):'') + errorText(error));}
  function empty(title,body=''){return `<div class="reference-empty"><strong>${esc(title)}</strong>${body?`<p>${esc(body)}</p>`:''}</div>`;}

  host.innerHTML=`<header class="reference-heading"><h1><span data-i18n="references">参考库</span> <span id="reference-total"></span></h1><button class="reference-button" data-ref-action="add">${icon('plus')}<span data-i18n="addSource">添加来源</span></button></header>
    <div class="reference-tools"><nav class="reference-tabs" aria-label="参考视图" data-en-aria-label="Reference views">${[['discover',t('discover')],['following',t('following')],['updates',t('updates')]].map(([id,label])=>`<button data-ref-mode="${id}" aria-pressed="${id==='discover'}" class="${id==='discover'?'active':''}">${label}</button>`).join('')}</nav><form id="reference-search-form" class="reference-search-form"><div class="search-wrap">${icon('search')}<input id="reference-search" type="search" aria-label="搜索参考库或 GitHub" placeholder="搜索参考或 GitHub" data-i18n-placeholder="searchReferences" data-i18n-aria="searchReferences" autocomplete="off"></div><button type="submit" id="reference-github-search" class="reference-button" data-i18n="searchGithub">搜索 GitHub</button></form></div>
    <div id="reference-error" class="reference-error" role="alert" hidden></div>
    <div id="reference-browse" class="reference-browse"><div class="reference-filterbar"><label class="reference-select-label"><span class="sr-only" data-en="Reference category">参考分类</span><select id="reference-category" aria-label="参考分类" data-en-aria-label="Reference category"><option value="all" data-en="All categories">全部分类</option></select></label><button data-ref-action="favorites" id="reference-favorites" aria-pressed="false" class="reference-button subtle">${icon('star')}<span data-en="Favorites">收藏</span></button><span id="reference-filter-count"></span></div><section id="reference-candidates" class="reference-candidates" aria-label="GitHub 搜索结果" data-en-aria-label="GitHub search results" hidden></section><div class="reference-workspace"><section class="reference-list" id="reference-list" aria-label="参考列表" data-en-aria-label="Reference list"></section><section class="reference-detail" id="reference-detail" aria-label="参考详情" data-en-aria-label="Reference details" aria-busy="false">${empty(ui("选择一份参考","Select a reference"))}</section></div></div>
    <section id="reference-updates" class="reference-updates" aria-label="更新与跟踪" data-en-aria-label="Updates and tracking" hidden></section>`;

  const dialogs=document.createElement('div');
  dialogs.innerHTML=`<dialog id="reference-add-dialog" class="reference-dialog"><div class="dialog-top"><h2 data-en="Add GitHub source">添加 GitHub 来源</h2><button class="icon-button" data-ref-close="reference-add-dialog" aria-label="关闭添加来源" data-en-aria-label="Close source dialog">×</button></div><form id="reference-add-form"><label for="reference-source-url" data-en="Repository or file URL">仓库或文件链接</label><input id="reference-source-url" type="url" placeholder="https://github.com/作者/仓库" data-en-placeholder="https://github.com/owner/repository" required><label for="reference-import-category" data-en="Category">归入分类</label><select id="reference-import-category"></select><div id="reference-add-error" class="reference-error" role="alert" hidden></div><div id="reference-file-choices"></div><div class="reference-dialog-actions"><button type="button" class="reference-button" data-ref-close="reference-add-dialog" data-en="Cancel">取消</button><button id="reference-add-submit" type="submit" class="reference-button primary" data-en="Read source">读取来源</button></div></form></dialog>
    <dialog id="reference-adopt-dialog" class="reference-dialog adoption-dialog"><div class="dialog-top"><h2 data-en="Add to my items">采用到我的素材</h2><button class="icon-button" data-ref-close="reference-adopt-dialog" aria-label="关闭采用预览" data-en-aria-label="Close adoption preview">×</button></div><label for="reference-adopt-target" data-en="Save location">保存位置</label><select id="reference-adopt-target"><option value="" data-en="New item">新建素材</option></select><div id="reference-adopt-preview" aria-live="polite"></div><div id="reference-adopt-error" class="reference-error" role="alert" hidden></div><div class="reference-dialog-actions"><button class="reference-button" data-ref-close="reference-adopt-dialog" data-en="Cancel">取消</button><button id="reference-adopt-confirm" class="reference-button primary" data-ref-action="adopt-confirm" disabled data-en="Confirm">确认采用</button></div></dialog>`;
  document.body.append(dialogs);

  function localizeReferences(){
    window.LiubaiI18n.localize(host,window.LiubaiLanguage||'zh');
    window.LiubaiI18n.localize(dialogs,window.LiubaiLanguage||'zh');
    for(const [id,key] of [['discover','discover'],['following','following'],['updates','updates']]){
      const target=host.querySelector(`[data-ref-mode="${id}"]`);if(target)target.textContent=t(key);
    }
    if(ref.loaded){renderFilters();renderList();}
    if(ref.detail){
      const scroll=$('reference-reading')?.scrollTop||0;
      renderReference();
      $('reference-reading').scrollTop=scroll;
    }else if(!ref.selected){
      $('reference-detail').innerHTML=empty(ui('选择一份参考','Select a reference'));
    }
    if(!$('reference-candidates').hidden&&ref.candidateOrigin)renderCandidates(ref.partialCandidates);
    if(ref.mode==='updates'&&ref.status)renderStatus();
  }
  window.addEventListener('liubai-language-change',localizeReferences);
  localizeReferences();

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
    if(!ref.loaded)$('reference-list').innerHTML=empty(ui("正在读取参考…","Loading references…"));
    try{
      const data=await api('/api/references');ref.items=data.references||[];ref.categories=data.categories||state.categories;ref.loaded=true;
      if(data.schedule)ref.status=data.schedule;
      renderScheduledCandidates();
      renderFilters();renderList();
      if(reselect&&ref.selected&&ref.items.some(item=>item.id===ref.selected))await select(ref.selected,false,ref.detail?.snapshot?.id);
      if(ref.mode==='updates')await loadStatus();
    }catch(error){failure(error);if(!ref.loaded)$('reference-list').innerHTML=empty(ui("暂时无法读取参考","Could not load references"),ui("点击顶部刷新重试。","Use the Refresh button to retry."));}
    finally{$('refresh-button').disabled=false;}
  }
  function renderFilters(){
    const options=ref.categories.map(item=>`<option value="${esc(item.id)}">${esc(categoryName(item.id))}</option>`).join('');
    $('reference-category').innerHTML=`<option value="all">${t('allCategories')}</option>${options}`;$('reference-category').value=ref.category;
    $('reference-import-category').innerHTML=options;$('reference-import-category').value=ref.category==='all'?'uncategorized':ref.category;
    $('reference-total').textContent=ref.items.length;
  }
  function visibleItems(){
    const words=ref.query.toLocaleLowerCase().trim().split(/\s+/).filter(Boolean);
    return ref.items.filter(item=>(ref.mode!=='following'||item.followed)&&(ref.category==='all'||item.category_id===ref.category)&&(!ref.favorites||item.favorite)&&words.every(word=>[item.title,item.summary,item.id,item.source?.repository,(item.tags||[]).join(' '),nameOf(item.category_id),item.search_text].join(' ').toLocaleLowerCase().includes(word)));
  }
  function renderList(){
    const rows=visibleItems();$('reference-filter-count').textContent=`${rows.length}${ui(" 份"," items")}`;
    $('reference-list').innerHTML=rows.length?rows.map(item=>`<button class="reference-card ${ref.selected===item.id?'selected':''}" data-ref-id="${esc(item.id)}" aria-pressed="${ref.selected===item.id}"><span class="reference-card-meta"><span>${esc(nameOf(item.category_id))}</span><span>${esc(materialNames()[item.material_type]||ui("参考","Reference"))}</span></span><h2>${esc(item.title)}</h2><span class="reference-repository">${esc(item.source?.repository||ui("来源待核对","Source needs review"))}</span><span class="reference-card-bottom"><span class="reference-badge">${item.analysis_status==='ready'?esc(selectionNames()[item.selection_status]||ui("已拆解","Analyzed")):ui("待分析","Analysis pending")}</span>${item.favorite?`<span aria-label="${ui("已收藏","Saved to favorites")}">${icon('star')}</span>`:''}${item.followed?ui("<span class=\"reference-following\">已关注</span>","<span class=\"reference-following\">Following</span>"):''}</span></button>`).join(''):empty(ref.mode==='following'?ui("还没有关注的来源","No followed sources"):ui("没有匹配的参考","No matching references"),ref.mode==='following'?ui("在参考详情中点击“关注来源”。","Choose Follow source in the reference details."):ui("调整关键词或分类，也可搜索 GitHub。","Try different keywords or categories, or search GitHub."));
    if(!rows.some(item=>item.id===ref.selected)){
      if(rows.length)select(rows[0].id,false);
      else{ref.selected=null;ref.detail=null;ref.request++;$('reference-detail').innerHTML=empty(ui("选择一份参考","Select a reference"));$('reference-detail').setAttribute('aria-busy','false');document.querySelector('.reference-workspace').classList.remove('show-detail');}
    }
  }
  function setMode(mode){
    ref.mode=mode;document.querySelectorAll('[data-ref-mode]').forEach(node=>{const selected=node.dataset.refMode===mode;node.classList.toggle('active',selected);node.setAttribute('aria-pressed',String(selected));});
    $('reference-browse').hidden=mode==='updates';$('reference-updates').hidden=mode!=='updates';$('reference-search-form').hidden=mode==='updates';
    if(mode==='updates')loadStatus();else{clearTimeout(ref.poll);renderList();if(mode==='discover')renderScheduledCandidates();}
  }
  async function select(id,reveal=true,snapshot=null){
    ref.selected=id;ref.detail=null;const request=++ref.request;$('reference-detail').setAttribute('aria-busy','true');$('reference-detail').innerHTML=empty(ui("正在读取原文…","Reading the original…"));
    document.querySelectorAll('[data-ref-id]').forEach(node=>{node.classList.toggle('selected',node.dataset.refId===id);node.setAttribute('aria-pressed',String(node.dataset.refId===id));});
    if(reveal)document.querySelector('.reference-workspace').classList.add('show-detail');
    try{const data=await api('/api/references/'+encodeURIComponent(id)+(snapshot?'?snapshot='+encodeURIComponent(snapshot):''));if(request!==ref.request)return;ref.detail=data;renderReference();}
    catch(error){if(request!==ref.request)return;$('reference-detail').innerHTML=empty(ui("参考未能打开","Could not open the reference"),errorText(error))+button('retry-detail',ui("重试","Retry"));failure(error);}
    finally{if(request===ref.request)$('reference-detail').setAttribute('aria-busy','false');}
  }
  function section(title,content){return `<section class="reference-section"><h3>${title}</h3>${content}</section>`;}
  function renderAnalysis(a){
    if(!a)return section(ui("写法拆解","Design analysis"),`<div class="reference-pending">${ui("待分析","Analysis pending")}</div><p class="reference-prose">${ui("这份快照还没有完成拆解，通用模板与采用暂不可用。","This snapshot needs analysis before you can use its template or add it to your items.")}</p>`);
    const structure=(a.structure||[]).map(row=>`<tr><th scope="row">${esc(row.part)}</th><td>${esc(textOf(row.observation))}</td><td>${esc(textOf(row.evidence))}</td></tr>`).join('');
    const keys=(a.key_sentences||[]).map((row,index)=>`<article class="reference-key"><blockquote>${esc(row.quote)}</blockquote><button class="reference-inline" data-ref-quote="${index}">${esc(row.location||ui("定位到原文","Find in original"))} ↑</button><dl><dt>${ui("作用","Purpose")}</dt><dd>${esc(textOf(row.reason))}</dd><dt>${ui("删改后可能","Effect of removal or editing")}</dt><dd>${esc(textOf(row.without))}</dd></dl></article>`).join('');
    const reason=a.design_reasoning||{},sample=a.example||{},contrast=a.counterexample||{},loop=a.loop||{};
    const dimensions=[[ui("来源成熟度","Source maturity"),a.maturity],[ui("任务匹配度","Task fit"),a.fit],[ui("使用证据","Usage evidence"),a.evidence],[ui("本库实测","Test results"),{reason:a.evaluation_status==='untested'?ui("尚未进行真实任务评测","No real-task evaluation yet"):ui("请查看对应评测记录","See the relevant evaluation record")}]];
    const qualityNames={goal_clarity:ui("目标明确","Clear goal"),input_clarity:ui("输入明确","Clear inputs"),constraint_quality:ui("约束合理","Appropriate constraints"),output_checkability:ui("输出可检查","Verifiable output"),usage_evidence:ui("使用证据","Usage evidence"),task_fit:ui("任务适配","Task fit")};
    return section(ui("适用场景","Use cases"),block(a.use_cases)+`<h4>${ui("不适用情境","When to avoid it")}</h4>`+block(a.not_for))
      +section(ui("结构地图","Structure map"),`<div class="reference-table-wrap"><table class="reference-table"><thead><tr><th>${ui("模块","Section")}</th><th>${ui("写法","Approach")}</th><th>${ui("原文依据","Evidence from the original")}</th></tr></thead><tbody>${structure}</tbody></table></div>`)
      +section(ui("关键句的作用","What key sentences do"),keys||block(ui("原文没有独立关键句记录。","The original has no individual key sentence notes.")))
      +section(ui("设计依据","Design rationale"),`<h4>${ui("作者公开说明","Public notes from the author")}</h4>${block(reason.author_stated)}<h4>${ui("整理者分析","Curator’s analysis")}</h4>${block(reason.inferred)}<h4>${ui("实际证据","Supporting evidence")}</h4>${block(reason.evidence)}`)
      +section(ui("通用模板","Reusable template"),button('copy-template',`${icon('copy')}${ui("复制模板","Copy template")}`,'','reference-button section-copy')+pre(a.template))
      +section(ui("改写示例","Adaptation example"),`<span class="reference-badge">${ui("示意 · 未实测","Illustration · untested")}</span><h4>${esc(sample.task||ui("应用示例","Example task"))}</h4>${pre(sample.prompt)}<h4>${ui("修改理由","Why it changed")}</h4>${block(sample.changes)}`)
      +section(ui("对照与反例","Comparison and counterexample"),`<span class="reference-badge">${ui("预期差异 · 未实测","Expected difference · untested")}</span><h4>${ui("调整前","Before")}</h4>${pre(contrast.before)}<h4>${ui("调整后","After")}</h4>${pre(contrast.after)}<h4>${ui("唯一改变的变量","Only variable changed")}</h4>${block(contrast.changed_variable)}<h4>${ui("预期影响","Expected impact")}</h4>${block(contrast.expected_effect)}`)
      +section('Loop',`<div class="reference-loop-meta"><span>${esc({none:ui("无需循环","No iteration needed"),conditional:ui("按条件启用","Iterate if needed"),recommended:ui("建议使用","Iteration recommended")}[loop.applicability]||textOf(loop.applicability))}</span>${loop.max_rounds?`<span>${ui("最多 ","Up to ")}${esc(loop.max_rounds)}${ui(" 轮"," rounds")}</span>`:''}${button('copy-loop',`${icon('copy')}${ui("复制 Loop","Copy loop")}`,'','reference-button subtle')}</div>${pre(loop.text||ui("单次处理，无需循环。","One pass is enough."))}`)
      +section(ui("筛选依据","Selection criteria"),`<dl class="reference-quality">${dimensions.map(([title,value])=>`<div><dt>${title}</dt><dd>${esc(textOf(value))}</dd></div>`).join('')}</dl><details class="reference-subdetails"><summary>${ui("六项质量检查","Six quality checks")}</summary><dl class="reference-quality">${Object.entries(a.quality_review||{}).map(([key,value])=>`<div><dt>${esc(qualityNames[key]||key)}</dt><dd>${esc(textOf(value))}</dd></div>`).join('')}</dl></details>`);
  }
  function renderReference(){
    const d=ref.detail;if(!d)return;const item=d.item||{},snapshot=d.snapshot||{},source=snapshot.source||item.source||{},a=d.analysis;
    const original=typeof d.original==='string'?d.original:'';const lines=original.split('\n').length;const long=lines>14||original.length>1600;
    const excerpt=snapshot.is_excerpt||source.is_excerpt||source.retention==='excerpt'||source.extraction?.kind==='notebook_cells'||['lines','notebook_cells'].includes(source.extraction?.type);
    const originalTitle=excerpt?ui("原文节选","Original excerpt"):item.material_type==='method'?ui("设计方法原文","Original design method"):item.material_type==='workflow'?ui("工作流原文","Original workflow"):ui("原文","Original");
    const preserved=original.length>0;const old=snapshot.id&&snapshot.id!==item.current_snapshot_id;
    const snapshots=d.snapshots||[];const diff=d.diff||{};
    $('reference-detail').innerHTML=`<header class="reference-detail-header"><div class="reference-detail-controls"><button class="icon-button reference-back" data-ref-action="back" aria-label="${ui("返回参考列表","Back to references")}">${icon('back')}</button><span class="reference-badge">${esc(nameOf(item.category_id))}</span><span class="reference-badge">${esc(materialNames()[item.material_type]||ui("参考","Reference"))}</span><div class="reference-actions">${button('favorite',icon('star'),`aria-label="${item.favorite?ui("取消收藏参考","Remove from favorites"):ui("收藏参考","Add to favorites")}" aria-pressed="${!!item.favorite}"`,'icon-button '+(item.favorite?'saved':''))}${button('follow',item.followed?ui("已关注","Following"):ui("关注来源","Follow source"),`aria-pressed="${!!item.followed}"`)}${button('adopt',ui("采用","Add to my items"),old?ui("disabled title=\"请切换到最新快照后采用\"","disabled title=\"Switch to the latest snapshot first\""):'','reference-button primary')}</div></div><h2>${esc(item.title)}</h2><div class="reference-source-line">${link(snapshot.source_url||source.url,source.repository||ui("查看来源","View source"))}<code title="${ui("固定 commit","Pinned commit")}">${esc((snapshot.commit||source.commit||ui("版本待核对","Unknown")).slice(0,12))}</code><span>${esc(source.license||ui("许可待核对","License needs review"))}</span>${old?ui("<span class=\"reference-badge\">历史快照</span>","<span class=\"reference-badge\">Historical snapshot</span>"):''}</div></header>
      <div class="reference-reading" id="reference-reading"><section class="reference-section reference-original-section" aria-labelledby="reference-original-title"><div class="reference-section-top"><h3 id="reference-original-title">${originalTitle}</h3>${button('copy-original',`${icon('copy')}${ui("复制原文","Copy original")}`,preserved?'':'disabled')}</div>${preserved?`<p class="reference-original-range">${source.source_span?esc(textOf(source.source_span)):excerpt?esc(textOf(source.excerpt_scope||snapshot.excerpt_scope||ui("节选范围见来源记录","See the source record for excerpt scope"))):ui("完整已收录原文","Full original as archived")} · ${lines}${ui(" 行"," lines")}${long?ui(" · 区内可滚动"," · scroll to read more"):''}</p><pre id="reference-original" class="reference-original ${long?'scrollable':''}" tabindex="0" aria-label="${originalTitle}${ui('，',', ')}${lines}${ui(" 行"," lines")}">${esc(original)}</pre>${long?button('expand-original',ui("展开全文","Expand full text"),'aria-expanded="false" aria-controls="reference-original"','reference-inline'):''}`:`<div class="reference-pending">${ui("原文未收录","Original unavailable")}</div>${block(snapshot.original_unavailable_reason||source.retention_reason||snapshot.retention_reason||ui("复制许可尚未确认，仅保留来源信息。","This record contains source details only. Permission to copy the text still needs review."))}${link(source.url,ui("查看来源","View source"))}`}${source.license_status!=='allowed'?`<p class="reference-license-note">${source.license_status==='restricted'?ui("使用受限，请核对来源许可。","Use is restricted. Check the source license."):ui("复制与采用条件待核对。","Copying and reuse terms need review.")}</p>`:''}</section>
      ${a?.translation?section(ui("中文译文","Chinese translation"),ui(pre(a.translation),`<details class="reference-subdetails"><summary>Show Chinese</summary>${pre(a.translation)}</details>`)):''}${renderAnalysis(a)}
      ${section(ui("版本变化","Version changes"),`<label class="reference-version-picker" for="reference-snapshot">${ui("来源快照","Source snapshot")}<select id="reference-snapshot">${snapshots.map(s=>`<option value="${esc(s.id)}" ${s.id===snapshot.id?'selected':''}>${esc(s.id)} · ${esc((s.commit||'').slice(0,8))} · ${dateLabel(s.created_at)}</option>`).join('')}</select></label>${diff.text?`<p class="reference-prose">${esc(diff.from_snapshot||ui("前版","Previous version"))} → ${esc(diff.to_snapshot||snapshot.id)}</p>${pre(diff.text,'reference-diff')}${diff.impact?`<h4>${ui("影响说明","Impact")}</h4>${block(diff.impact)}`:''}${diff.analysis_status==='pending'?ui("<p class=\"reference-prose\">变更影响待分析。</p>","<p class=\"reference-prose\">Impact analysis pending.</p>"):''}`:block(ui("当前快照没有可展示的内容差异。","No content differences to display for this snapshot."))}`)}
      ${section(ui("来源与关联","Source and related items"),`<dl class="reference-quality"><div><dt>${ui("来源文件","Source file")}</dt><dd>${esc(source.path||ui("未说明","Unspecified"))}</dd></div><div><dt>${ui("固定版本","Pinned version")}</dt><dd>${esc(snapshot.commit||source.commit||ui("未说明","Unspecified"))}</dd></div><div><dt>${ui("内容校验","Content checksum")}</dt><dd>${esc(snapshot.sha256||ui("未说明","Unspecified"))}</dd></div><div><dt>${ui("最近成功检查","Last successful check")}</dt><dd>${timeOf(item.last_success)}</dd></div><div><dt>${ui("收录时间","Archived")}</dt><dd>${timeOf(snapshot.created_at||source.retrieved_at||item.created_at)}</dd></div><div><dt>${ui("拆解版本","Analysis version")}</dt><dd>${esc(a?.version||ui("待分析","Analysis pending"))}</dd></div></dl>${(item.related_ids||[]).length?`<div class="reference-related-links">${item.related_ids.map(id=>button('open-personal',esc(id),`data-personal-id="${esc(id)}"`)).join('')}</div>`:''}`)}
      </div><footer class="reference-detail-footer"><a class="reference-button" href="/download/reference/${encodeURIComponent(item.id)}/card?snapshot=${encodeURIComponent(snapshot.id||item.current_snapshot_id)}" download>${icon('download')}${ui("导出完整卡片","Export full card")}</a><span>${ui("实测状态：","Test status: ")}${item.evaluation_status==='untested'?ui("待实测","Untested"):ui("查看记录","See records")}</span></footer>`;
  }
  async function copyReference(kind){
    const d=ref.detail;if(!d)return;const value=kind==='original'?d.original:kind==='loop'?(d.analysis?.loop?.text||d.loop?.text):(d.analysis?.template||d.template);
    if(!value)return toast(ui("当前内容尚不可复制","This content is unavailable to copy"));
    try{await navigator.clipboard.writeText(value);toast(ui("已复制","Copied ")+({original:ui("原文","the original"),template:ui("模板","the template"),loop:'Loop'}[kind]));}
    catch{const area=document.createElement('textarea');area.value=value;area.setAttribute('aria-label',ui("待复制参考","Reference text to copy"));document.body.append(area);area.select();const success=document.execCommand('copy');area.remove();toast(success?ui("已复制","Copied"):ui("复制未成功，请选中文本后按 Ctrl+C","Copy failed. Select the text and use your system’s copy shortcut."));}
  }
  async function flag(kind,node){
    if(!ref.detail)return;const id=ref.detail.item.id;node.disabled=true;const scroll=$('reference-reading')?.scrollTop||0;
    try{const data=await post('flags',{id,[kind]:!ref.detail.item[kind]});const updated=data.item;const index=ref.items.findIndex(item=>item.id===id);if(index>=0)ref.items[index]={...ref.items[index],...updated};if(ref.detail?.item.id===id)ref.detail.item=updated;renderList();if(ref.detail?.item.id===id){renderReference();$('reference-reading').scrollTop=scroll;}toast(kind==='favorite'?(updated.favorite?ui("已收藏","Added to favorites"):ui("已取消收藏","Removed from favorites")):(updated.followed?ui("已关注来源","Following source"):ui("已取消关注","Unfollowed source")));}
    catch(error){failure(error,ui("未保存：","Could not save. "));node.disabled=false;}
  }
  function renderScheduledCandidates(){
    if(ref.candidateOrigin==='manual'||!ref.status?.discovery?.candidates?.length)return;
    ref.candidates=ref.status.discovery.candidates;ref.candidateOrigin='scheduled';renderCandidates();
  }
  function renderCandidates(partial=false){
    ref.partialCandidates=partial;
    $('reference-candidates').hidden=false;
    $('reference-candidates').innerHTML=`<div class="reference-candidate-heading"><strong>${ref.candidateOrigin==='scheduled'?ui("定期发现","Scheduled discovery"):ui("GitHub 候选","GitHub candidates")} <span>${ref.candidates.length}</span></strong>${button('close-candidates',ui("关闭结果","Close results"),'','reference-inline')}</div>${partial?ui("<p class=\"reference-prose\">搜索部分完成，可稍后重试。</p>","<p class=\"reference-prose\">Search returned partial results. Try again later.</p>"):''}${ref.candidates.length?`<div class="reference-candidate-list">${ref.candidates.map((item,index)=>`<article><div><h3>${link(item.url,item.repository||item.title)}</h3>${block(item.description||item.reason||ui("请查看来源文件","See the source file"))}<span class="reference-candidate-meta">${esc(item.license||ui("许可待核对","License needs review"))} · ${item.updated_at?dateLabel(item.updated_at):ui("维护时间待核对","Maintenance date needs review")}</span></div>${button('candidate-files',ui("查看文件","View files"),`data-candidate-index="${index}"`)}</article>`).join('')}</div>`:empty(ui("没有找到可靠匹配","No reliable matches found"),ui("换一个更具体的任务词再试。","Try a more specific search term."))}`;
  }
  async function discover(event){
    event?.preventDefault();const query=$('reference-search').value.trim();if(!query){$('reference-search').focus();return toast(ui("先输入任务或关键词","Enter a task or keywords first"));}
    const node=$('reference-github-search');node.disabled=true;node.textContent=ui("搜索中…","Searching…");message('');$('reference-candidates').hidden=false;$('reference-candidates').innerHTML=empty(ui("正在搜索 GitHub…","Searching GitHub…"));
    try{const data=await post('discover',{query,category_id:ref.category==='all'?undefined:ref.category,entry_id:ref.relatedEntry||undefined});ref.candidates=data.candidates||[];ref.candidateOrigin='manual';renderCandidates(data.partial);
    }catch(error){$('reference-candidates').innerHTML=empty(ui("GitHub 搜索失败","GitHub search failed"),errorText(error));failure(error);}
    finally{node.disabled=false;node.textContent=ui("搜索 GitHub","Search GitHub");}
  }
  function openAdd(url=''){$('reference-source-url').value=url;$('reference-file-choices').replaceChildren();$('reference-add-error').hidden=true;$('reference-add-dialog').showModal();$('reference-source-url').focus();}
  async function importSource(url){
    if(ref.importing)return;ref.importing=true;
    const submit=$('reference-add-submit');submit.disabled=true;$('reference-add-error').hidden=true;
    $('reference-file-choices').setAttribute('aria-busy','true');
    try{const result=await post('import',{url,category_id:$('reference-import-category').value});
      if(result.choose_file){const files=result.candidates||[];$('reference-file-choices').innerHTML=`<h3>${ui("选择来源文件","Choose a source file")}</h3><div class="reference-file-list">${files.length?files.map(file=>`<button type="button" data-import-url="${esc(file.url)}" class="reference-file"><strong>${esc(file.title||file.path)}</strong><span>${esc(file.path)}</span></button>`).join(''):empty(ui("未找到可归档文件","No files eligible to archive"),ui("请直接添加具体文件链接。","Try adding a link to a specific file."))}</div>`;}
      else{$('reference-add-dialog').close();toast(result.duplicate?ui("该来源已在参考库中","This source is already in your references"):ui("来源已归档，等待拆解","Source archived. Analysis is pending."));ref.query='';$('reference-search').value='';ref.category='all';ref.favorites=false;setMode('discover');await refresh(false);if(result.id)await select(result.id);}
    }catch(error){$('reference-add-error').textContent=errorText(error);$('reference-add-error').hidden=false;}
    finally{ref.importing=false;submit.disabled=false;$('reference-file-choices').setAttribute('aria-busy','false');}
  }
  async function openAdopt(){
    if(!ref.detail)return;ref.preview=null;$('reference-adopt-target').innerHTML=ui("<option value=\"\">新建素材</option>","<option value=\"\">New item</option>")+state.entries.map(item=>`<option value="${esc(item.id)}">${esc(item.id+' · '+item.title)}${ui("（新增版本）"," (add a version)")}</option>`).join('');$('reference-adopt-dialog').showModal();await previewAdoption();
  }
  async function previewAdoption(){
    if(!ref.detail)return;const request=++ref.previewRequest;ref.preview=null;$('reference-adopt-confirm').disabled=true;$('reference-adopt-preview').innerHTML=empty(ui("正在读取采用预览…","Loading adoption preview…"));$('reference-adopt-error').hidden=true;
    try{const preview=await post('adopt-preview',{id:ref.detail.item.id,target_id:$('reference-adopt-target').value||null});if(request!==ref.previewRequest)return;ref.preview=preview;if(preview.target_id)$('reference-adopt-target').value=preview.target_id;
      const previewSource=preview.source||ref.detail.item.source||{};
      const usageConditions=[[ui("使用限制","Usage restrictions"),previewSource.usage_restrictions],[ui("适用模型","Compatible models"),previewSource.applicable_models],[ui("所需依赖","Required dependencies"),previewSource.dependencies]].filter(([,value])=>value!==null&&value!==undefined&&value!==''&&(!Array.isArray(value)||value.length>0));
      $('reference-adopt-preview').innerHTML=`<h3>${esc(preview.title)}</h3><div class="reference-preview-meta"><span>${esc(nameOf(preview.category_id))}</span><span>${esc(preview.reference_id)} / ${esc(preview.snapshot_id)}</span><span>${esc(preview.license||ui("许可待核对","License needs review"))}</span><span>${ui("待实测","Untested")}</span></div>${preview.can_adopt?'':`<p class="reference-error">${esc(adoptionReason(preview.reason))}</p>`}<h4>${ui("来源","Source")}</h4>${link(previewSource.url,previewSource.repository||ui("查看原始来源","View original source"))}${usageConditions.length?`<dl class="reference-quality reference-usage-conditions">${usageConditions.map(([label,value])=>`<div><dt>${label}</dt><dd>${esc(textOf(value))}</dd></div>`).join('')}</dl>`:''}<h4>${ui("改编内容","Adaptation")}</h4>${preview.template?pre(preview.template):block(ui("尚无可采用的通用模板。","No reusable template is available."))}<p class="reference-prose">${preview.target_id?ui("保留已有原文与历史，追加一个优化版本。","Adds a new adaptation version and keeps the existing original and history."):ui("新条目保留参考原文、改编模板与来源关系。","The new item includes the reference original, adaptation template, and source link.")}</p>`;
      $('reference-adopt-confirm').disabled=!preview.can_adopt;
    }catch(error){if(request!==ref.previewRequest)return;$('reference-adopt-preview').replaceChildren();$('reference-adopt-error').textContent=errorText(error);$('reference-adopt-error').hidden=false;}
  }
  async function adopt(){
    const preview=ref.preview;if(!preview?.can_adopt)return;const node=$('reference-adopt-confirm');node.disabled=true;$('reference-adopt-target').disabled=true;
    try{const result=await post('adopt',{id:preview.reference_id,target_id:preview.target_id||null,expected_snapshot:preview.snapshot_id,expected_analysis_version:preview.analysis_version});$('reference-adopt-dialog').close();toast(result.duplicate?ui("已采用过此版本","This version has already been added"):`${ui("已保存为 ","Saved as ")}${result.entry_id} · ${result.version}`);leave();await loadLibrary();if(result.entry_id)await selectEntry(result.entry_id);ref.loaded=false;}
    catch(error){$('reference-adopt-error').textContent=errorText(error);$('reference-adopt-error').hidden=false;node.disabled=false;}
    finally{$('reference-adopt-target').disabled=false;}
  }
  function renderStatus(){
    const s=ref.status;if(!s)return;
    const stateLabel=s.running?ui("检查中","Checking"):!s.enabled?ui("采集已暂停","Collection paused"):s.registration_status!=='active'?ui("定时执行待就绪","Scheduled checks pending setup"):ui("定时采集已启用","Scheduled collection enabled");
    const runs=s.runs||[],updates=s.updates||[];
    $('reference-updates').innerHTML=`<div class="reference-schedule"><div class="reference-schedule-heading"><h2>${stateLabel}</h2><div>${button('check-now',s.running?ui("检查中…","Checking…"):ui("立即检查","Check now"),s.running?'disabled':'')}${button('schedule-toggle',s.enabled?ui("暂停采集","Pause collection"):ui("恢复采集","Resume collection"))}</div></div><form id="reference-schedule-form" class="reference-schedule-form"><label>${ui("频率","Frequency")}<select id="reference-frequency" name="frequency"><option value="daily" ${s.frequency==='daily'?'selected':''}>${ui("每天","Daily")}</option><option value="weekly" ${s.frequency==='weekly'?'selected':''}>${ui("每周","Weekly")}</option></select></label><label id="reference-weekday-label" ${s.frequency==='weekly'?'':'hidden'}>${ui("日期","Day")}<select id="reference-weekday" name="weekday">${weekdays().map((day,index)=>`<option value="${index}" ${Number(s.weekday??6)===index?'selected':''}>${day}</option>`).join('')}</select></label><span class="reference-fixed-time">09:00 · Asia/Shanghai</span><button class="reference-button" type="submit">${ui("保存频率","Save frequency")}</button></form><dl class="reference-status-grid"><div><dt>${ui("最近尝试","Last attempt")}</dt><dd>${timeOf(s.last_attempt)}</dd></div><div><dt>${ui("最近成功","Last success")}</dt><dd>${timeOf(s.last_success)}</dd></div><div><dt>${ui("下次计划","Next scheduled check")}</dt><dd>${s.enabled?timeOf(s.next_run):ui("已暂停","Paused")}</dd></div><div><dt>${ui("待分析","Analysis pending")}</dt><dd>${typeof s.pending_analysis==='number'?s.pending_analysis:Array.isArray(s.pending_analysis)?s.pending_analysis.length:0}${ui(" 份"," items")}</dd></div></dl>${s.last_error?`<div class="reference-error">${esc(errorText(s.last_error,'The last check failed. See the run history.'))}</div>`:''}<p class="reference-dependency">${esc(ui(s.dependency||"执行依赖本机与 Codex；关闭或离线后恢复时合并补跑。","Scheduled checks require this computer and Codex. After the 09:00 wake-up, checks follow the frequency and pause settings shown here. At most one missed check runs after recovery."))}</p><details class="reference-subdetails"><summary>${ui("执行方式与单次上限","Execution and per-run limits")}</summary><dl class="reference-quality"><div><dt>${ui("调度入口","Scheduler")}</dt><dd>${esc(s.engine||ui("尚未配置","Pending setup"))} · ${s.registration_status==='active'?ui("已注册","Registered"):ui("待注册","Registration pending")}</dd></div>${Object.entries(s.limits||{}).map(([key,value])=>`<div><dt>${esc({repositories:ui("仓库","Repositories"),max_repositories:ui("仓库","Repositories"),files:ui("文件","Files"),max_files:ui("文件","Files"),max_file_bytes:ui("单文件字节","Bytes per file"),max_bytes:ui("单文件字节","Bytes per file"),max_seconds:ui("运行秒数","Run time in seconds"),max_retries:ui("失败重试","Retries"),max_analyses:ui("深度分析","In-depth analyses"),max_analysis:ui("深度分析","In-depth analyses")}[key]||key)}</dt><dd>${esc(textOf(value))}</dd></div>`).join('')}</dl></details></div>
      <section class="reference-update-section"><h2>${ui("来源动态","Source updates")}</h2>${updates.length?updates.map(update=>`<button class="reference-update-row" data-open-reference="${esc(update.reference_id)}"><span><strong>${esc(update.title||update.reference_id)}</strong><small>${esc(statusNames()[update.status]||update.status)}${update.error?' · '+esc(errorText(update.error,'Source check failed')):''}</small></span><time>${timeOf(update.checked_at)}</time>${icon('external')}</button>`).join(''):empty(ui("还没有来源动态","No source updates yet"))}</section>
      <section class="reference-update-section"><h2>${ui("运行记录","Run history")}</h2>${runs.length?`<div class="reference-table-wrap"><table class="reference-table"><thead><tr><th>${ui("开始时间","Start time")}</th><th>${ui("触发","Trigger")}</th><th>${ui("结果","Result")}</th><th>${ui("检查详情","Check details")}</th></tr></thead><tbody>${runs.map(run=>`<tr><td>${timeOf(run.started_at)}</td><td>${esc({manual:ui("手动","Manual"),scheduled:ui("定时","Scheduled"),heartbeat:ui("定时","Scheduled"),codex_heartbeat:ui("定时","Scheduled"),codex_heartbeat_acceptance:ui("定时验收","Scheduled verification"),catchup:ui("补跑","Catch-up")}[run.trigger]||run.trigger)}</td><td>${esc(statusNames()[run.status]||run.status)}</td><td>${ui("无变化 ","Unchanged ")}${Number(run.unchanged)||0}${ui(" · 变化 "," · Changed ")}${Number(run.changed)||0}${ui(" · 失败 "," · Failed ")}${Number(run.failed)||0}${run.errors?.length?`<details><summary>${ui("失败原因","Failure details")}</summary>${block(run.errors)}</details>`:''}</td></tr>`).join('')}</tbody></table></div>`:empty(ui("还没有执行记录","No runs recorded"))}</section>`;
  }
  async function loadStatus(){
    clearTimeout(ref.poll);
    if(!ref.status)$('reference-updates').innerHTML=empty(ui("正在读取跟踪状态…","Loading tracking status…"));
    try{ref.status=await api('/api/references/status');if(!$('reference-schedule-form')?.contains(document.activeElement))renderStatus();if(ref.active&&ref.mode==='updates'&&ref.status.running)ref.poll=setTimeout(loadStatus,3000);}
    catch(error){failure(error,ui("状态读取失败：","Could not read status. "));if(!ref.status)$('reference-updates').innerHTML=empty(ui("状态暂不可用","Status unavailable"),ui("点击顶部刷新重试。","Use the Refresh button to retry."));}
  }
  async function checkNow(node){node.disabled=true;message('');try{const data=await post('check',{force:true});toast(data.started?ui("已开始检查","Check started"):data.reason==='busy'?ui("已有检查正在运行","A check is already running"):errorText(data.reason||ui('检查未启动','The check did not start'),'The check did not start'));await loadStatus();}catch(error){failure(error);node.disabled=false;}}
  async function saveSchedule(values,node){node.disabled=true;message('');try{const status=await post('schedule',values);ref.status=status.schedule||status;renderStatus();toast(values.enabled===false?ui("采集已暂停","Collection paused"):values.enabled===true?ui("采集已恢复","Collection resumed"):ui("更新频率已保存","Frequency saved"));}catch(error){failure(error);node.disabled=false;}}

  async function renderRelated(entryId){
    const content=$('detail-content');if(!content)return;const target=document.createElement('section');target.className='personal-reference-links';target.id='personal-reference-links';content.append(target);
    try{const data=await api('/api/references/related/'+encodeURIComponent(entryId));if(state.selected!==entryId||!target.isConnected)return;const rows=(data.references||[]).slice(0,3);target.innerHTML=`<h3>${ui("参考写法","Related references")}</h3>${rows.length?rows.map(item=>`<button data-open-reference="${esc(item.id)}"><strong>${esc(item.title)}</strong><span>${esc(relatedReason(item.reason))}</span></button>`).join(''):ui("<p>暂未找到可靠匹配。</p>","<p>No reliable match yet.</p>")}<button class="reference-inline" data-discover-for="${esc(entryId)}">${ui("为这条素材寻找参考 ↗","Find references for this item ↗")}</button>`;}
    catch{if(target.isConnected)target.innerHTML=ui("<p>参考关联暂不可用。</p>","<p>Related references are unavailable.</p>");}
  }
  document.addEventListener('click',async event=>{
    const close=event.target.closest('[data-ref-close]');if(close){$(close.dataset.refClose).close();return;}
    const mode=event.target.closest('[data-ref-mode]');if(mode){setMode(mode.dataset.refMode);return;}
    const row=event.target.closest('[data-ref-id]');if(row){select(row.dataset.refId);return;}
    const open=event.target.closest('[data-open-reference]');if(open){await enter(open.dataset.openReference);return;}
    const related=event.target.closest('[data-discover-for]');if(related){ref.relatedEntry=related.dataset.discoverFor;const entry=state.entries.find(item=>item.id===ref.relatedEntry);await enter();setMode('discover');ref.category=entry?.category_id||'all';$('reference-category').value=ref.category;ref.query=entry?.title||'';$('reference-search').value=ref.query;renderList();discover();return;}
    const file=event.target.closest('[data-import-url]');if(file){file.disabled=true;await importSource(file.dataset.importUrl);file.disabled=false;return;}
    const quote=event.target.closest('[data-ref-quote]');if(quote){const q=ref.detail?.analysis?.key_sentences?.[Number(quote.dataset.refQuote)]?.quote||'';const original=$('reference-original');if(original){const raw=ref.detail.original;const pos=raw.indexOf(q);if(pos>=0&&q){const mark=document.createElement('mark');mark.className='reference-quote-mark';mark.textContent=q;original.replaceChildren(document.createTextNode(raw.slice(0,pos)),mark,document.createTextNode(raw.slice(pos+q.length)));mark.scrollIntoView({block:'center'});}else{$('reference-reading').scrollTop=0;toast(ui("原文中未匹配到完整句子，请按标注位置核对。","The full sentence was not found in the original. Check the indicated location."));}original.focus({preventScroll:true});}return;}
    const action=event.target.closest('[data-ref-action]');if(!action)return;const name=action.dataset.refAction;
    if(name==='back')document.querySelector('.reference-workspace').classList.remove('show-detail');
    if(name==='retry-detail'&&ref.selected)select(ref.selected);
    if(name.startsWith('copy-'))copyReference(name.slice(5));
    if(name==='favorite')flag('favorite',action);
    if(name==='follow')flag('followed',action);
    if(name==='favorites'){ref.favorites=!ref.favorites;action.setAttribute('aria-pressed',String(ref.favorites));renderList();}
    if(name==='expand-original'){const expanded=action.getAttribute('aria-expanded')!=='true';action.setAttribute('aria-expanded',String(expanded));action.textContent=expanded?ui("收起全文","Collapse full text"):ui("展开全文","Expand full text");$('reference-original').classList.toggle('expanded',expanded);}
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
  window.addEventListener('offline',()=>{if(ref.active)message(ui("当前离线。已打开的参考仍可阅读，联网后点击刷新。","You are offline. Open references remain readable. Refresh after reconnecting."));});
  window.ReferenceLibrary={active:()=>ref.active,enter,leave,refresh,decorateNavigation,renderRelated};
  if(state.detail)renderRelated(state.detail.item.id);
})();
