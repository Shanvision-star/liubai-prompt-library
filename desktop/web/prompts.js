'use strict';

// 手动收录只保存用户填写的内容；不把原文当作 HTML 或可执行指令。
(() => {
  const editor={saving:false,categorySaving:false,classifying:false,classifyId:null,classifyVersion:null,opener:null};
  const NEW_CATEGORY='__new__';
  const send=(path,body)=>api(path,{method:'POST',headers:{'Content-Type':'application/json','X-Prompt-Library':'1'},body:JSON.stringify(body)});
  const closeButton=id=>`<button type="button" class="icon-button" data-prompt-close="${id}" aria-label="关闭窗口">×</button>`;
  const categoryFields=prefix=>`<label for="${prefix}-category">分类</label><select id="${prefix}-category" name="category" required></select><div id="${prefix}-new-category-field" hidden><label for="${prefix}-new-category">新分类名称</label><input id="${prefix}-new-category" name="category_name" maxlength="80" autocomplete="off" disabled></div>`;
  const dialogs=document.createElement('div');
  dialogs.innerHTML=`<dialog id="prompt-create-dialog" class="prompt-dialog" aria-labelledby="prompt-create-heading"><div class="dialog-top"><h2 id="prompt-create-heading">新建素材</h2>${closeButton('prompt-create-dialog')}</div><form id="prompt-create-form"><fieldset id="prompt-create-fields"><label for="prompt-title">标题</label><input id="prompt-title" name="title" maxlength="200" required autocomplete="off"><div class="prompt-form-columns"><div>${categoryFields('prompt')}</div><div><label for="prompt-tags">标签 <span>可选</span></label><input id="prompt-tags" name="tags" placeholder="用逗号分隔" autocomplete="off"></div></div><label for="prompt-original">原文</label><textarea id="prompt-original" name="original" rows="9" required spellcheck="false"></textarea><details id="prompt-optional-optimized" class="prompt-optional"><summary>添加优化版 <span>可选</span></summary><label for="prompt-optimized">优化版</label><textarea id="prompt-optimized" name="optimized" rows="6" spellcheck="false"></textarea></details></fieldset><div id="prompt-create-error" class="prompt-error" role="alert" hidden></div><div class="prompt-form-actions"><button type="button" class="reference-button" data-prompt-close="prompt-create-dialog">取消</button><button id="prompt-save-button" type="submit" class="reference-button primary">保存素材</button></div></form></dialog>
    <dialog id="category-create-dialog" class="prompt-dialog compact" aria-labelledby="category-create-heading"><div class="dialog-top"><h2 id="category-create-heading">新增分类</h2>${closeButton('category-create-dialog')}</div><form id="category-create-form"><fieldset id="category-create-fields"><label for="category-name">分类名称</label><input id="category-name" name="name" maxlength="80" required autocomplete="off"></fieldset><div id="category-create-error" class="prompt-error" role="alert" hidden></div><div class="prompt-form-actions"><button type="button" class="reference-button" data-prompt-close="category-create-dialog">取消</button><button id="category-save-button" type="submit" class="reference-button primary">添加分类</button></div></form></dialog>
    <dialog id="prompt-classify-dialog" class="prompt-dialog compact" aria-labelledby="prompt-classify-heading"><div class="dialog-top"><h2 id="prompt-classify-heading">修改分类</h2>${closeButton('prompt-classify-dialog')}</div><p id="prompt-classify-title" class="prompt-context-title"></p><form id="prompt-classify-form"><fieldset id="prompt-classify-fields">${categoryFields('classify')}</fieldset><div id="prompt-classify-error" class="prompt-error" role="alert" hidden></div><div class="prompt-form-actions"><button type="button" class="reference-button" data-prompt-close="prompt-classify-dialog">取消</button><button id="prompt-classify-save-button" type="submit" class="reference-button primary">保存分类</button></div></form></dialog>`;
  document.body.append(dialogs);

  function showError(id,message){$(id).textContent=message;$(id).hidden=!message;}
  function categoryOptions(prefix,preferred){
    const select=$(prefix+'-category');const previous=select.value;
    select.innerHTML=state.categories.map(category=>`<option value="${escapeHTML(category.id)}">${escapeHTML(category.name)}</option>`).join('')+`<option value="${NEW_CATEGORY}">新分类…</option>`;
    select.value=[preferred,previous,'uncategorized',state.categories[0]?.id].find(id=>id===NEW_CATEGORY||state.categories.some(category=>category.id===id))||NEW_CATEGORY;
    toggleNewCategory(prefix);
  }
  function toggleNewCategory(prefix){
    const expanded=$(prefix+'-category').value===NEW_CATEGORY;$(prefix+'-new-category-field').hidden=!expanded;$(prefix+'-new-category').disabled=!expanded;$(prefix+'-new-category').required=expanded;
  }
  function categoryPayload(prefix){return $(prefix+'-category').value===NEW_CATEGORY?{category_name:$(prefix+'-new-category').value.trim()}:{category_id:$(prefix+'-category').value};}
  function showDialog(id,focusId){editor.opener=document.activeElement;$(id).showModal();$(focusId)?.focus();}
  function clearFilters(category='all'){
    window.ReferenceLibrary?.leave();state.query='';$('search').value='';state.view='all';state.category=category;state.expanded=state.expanded||category!=='all';
  }
  async function refreshCategories(){
    const data=await api('/api/categories');state.categories=data.categories;renderNavigation();window.ReferenceLibrary?.decorateNavigation();
  }
  async function openCreate(){
    const hasDraft=!!($('prompt-title').value||$('prompt-original').value||$('prompt-optimized').value);
    categoryOptions('prompt',hasDraft?$('prompt-category').value:state.category==='all'?'uncategorized':state.category);
    showError('prompt-create-error','');showDialog('prompt-create-dialog','prompt-title');
    try{await refreshCategories();categoryOptions('prompt');}catch(error){showError('prompt-create-error','分类读取失败：'+error.message);}
  }
  function decorateDetail(){
    if(!state.detail||document.querySelector('#detail-pane [data-prompt-action="classify"]'))return;
    const controls=document.querySelector('#detail-pane .detail-topline > .detail-controls:last-child');if(!controls)return;
    const button=document.createElement('button');button.type='button';button.className='reference-button subtle prompt-classify-button';button.dataset.promptAction='classify';button.textContent='修改分类';controls.prepend(button);
  }
  async function openClassification(){
    if(!state.detail)return;editor.classifyId=state.detail.item.id;editor.classifyVersion=state.detail.selected_version||state.detail.item.latest_version;
    $('prompt-classify-title').textContent=state.detail.item.title;$('classify-new-category').value='';categoryOptions('classify',state.detail.item.category_id);showError('prompt-classify-error','');showDialog('prompt-classify-dialog','classify-category');
    try{await refreshCategories();categoryOptions('classify');}catch(error){showError('prompt-classify-error','分类读取失败：'+error.message);}
  }
  async function savePrompt(event){
    event.preventDefault();if(editor.saving)return;
    const original=$('prompt-original').value,optimized=$('prompt-optimized').value;
    if(new TextEncoder().encode(original).byteLength>256*1024){showError('prompt-create-error','原文超过 256 KiB，请拆分后保存。');return;}
    const body={title:$('prompt-title').value.trim(),original,...categoryPayload('prompt'),tags:[...new Set($('prompt-tags').value.split(/[,，、]/).map(tag=>tag.trim()).filter(Boolean))]};
    if(optimized.length)body.optimized=optimized;
    editor.saving=true;$('prompt-create-fields').disabled=true;$('prompt-save-button').disabled=true;$('prompt-save-button').textContent='保存中…';showError('prompt-create-error','');
    try{
      const result=await send('/api/prompts',body);$('prompt-create-dialog').close();$('prompt-create-form').reset();$('prompt-optional-optimized').open=false;toggleNewCategory('prompt');
      clearFilters();await loadLibrary();const item=state.entries.find(entry=>entry.id===result.id);if(item){state.category=item.category_id;updateView();await selectEntry(result.id,true,result.version||null);$('tab-optimized')?.focus({preventScroll:true});}toast(result.duplicate?'已存在相同原文，已打开已有素材':'素材已保存');
    }catch(error){showError('prompt-create-error',error.message);if(!$('prompt-create-dialog').open)$('prompt-create-dialog').showModal();}
    finally{editor.saving=false;$('prompt-create-fields').disabled=false;toggleNewCategory('prompt');$('prompt-save-button').disabled=false;$('prompt-save-button').textContent='保存素材';}
  }
  async function createCategory(event){
    event.preventDefault();if(editor.categorySaving)return;editor.categorySaving=true;$('category-create-fields').disabled=true;$('category-save-button').disabled=true;showError('category-create-error','');
    try{const result=await send('/api/categories',{name:$('category-name').value.trim()});await refreshCategories();$('category-create-dialog').close();$('category-create-form').reset();clearFilters(result.category.id);updateView();Array.from(document.querySelectorAll('#category-nav [data-category]')).find(node=>node.dataset.category===result.category.id)?.focus({preventScroll:true});toast(result.created?'分类已添加':'已打开已有分类');}
    catch(error){showError('category-create-error',error.message);if(!$('category-create-dialog').open)$('category-create-dialog').showModal();}
    finally{editor.categorySaving=false;$('category-create-fields').disabled=false;$('category-save-button').disabled=false;}
  }
  async function updateClassification(event){
    event.preventDefault();if(editor.classifying||!editor.classifyId)return;editor.classifying=true;$('prompt-classify-fields').disabled=true;$('prompt-classify-save-button').disabled=true;showError('prompt-classify-error','');
    const id=editor.classifyId,version=editor.classifyVersion,body=categoryPayload('classify');
    try{await send('/api/entries/'+encodeURIComponent(id)+'/metadata',body);$('prompt-classify-dialog').close();clearFilters();await loadLibrary();const item=state.entries.find(entry=>entry.id===id);if(item){state.category=item.category_id;updateView();await selectEntry(id,true,version);$('tab-optimized')?.focus({preventScroll:true});}toast('分类已更新');}
    catch(error){showError('prompt-classify-error',error.message);if(!$('prompt-classify-dialog').open)$('prompt-classify-dialog').showModal();}
    finally{editor.classifying=false;$('prompt-classify-fields').disabled=false;toggleNewCategory('classify');$('prompt-classify-save-button').disabled=false;}
  }
  document.addEventListener('click',event=>{
    const closer=event.target.closest('[data-prompt-close]');if(closer){$(closer.dataset.promptClose).close();return;}
    const action=event.target.closest('[data-prompt-action]');if(!action)return;
    if(action.dataset.promptAction==='new')openCreate();
    if(action.dataset.promptAction==='new-category'){showError('category-create-error','');showDialog('category-create-dialog','category-name');}
    if(action.dataset.promptAction==='classify')openClassification();
  });
  ['prompt','classify'].forEach(prefix=>$(prefix+'-category').addEventListener('change',()=>{toggleNewCategory(prefix);if($(prefix+'-category').value===NEW_CATEGORY)$(prefix+'-new-category').focus();}));
  ['prompt-create-dialog','category-create-dialog','prompt-classify-dialog'].forEach(id=>$(id).addEventListener('close',()=>{if(editor.opener?.isConnected)editor.opener.focus({preventScroll:true});}));
  $('prompt-create-form').addEventListener('submit',savePrompt);$('category-create-form').addEventListener('submit',createCategory);$('prompt-classify-form').addEventListener('submit',updateClassification);
  window.PromptEditor={decorateDetail};decorateDetail();
})();
