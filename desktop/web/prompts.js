'use strict';

// 手动收录只保存用户填写的内容；不把原文当作 HTML 或可执行指令。
(() => {
  const editor={saving:false,importing:false,imported:null,categorySaving:false,classifying:false,classifyId:null,classifyVersion:null,opener:null};
  const NEW_CATEGORY='__new__';
  const send=(path,body)=>api(path,{method:'POST',headers:{'Content-Type':'application/json','X-Prompt-Library':'1'},body:JSON.stringify(body)});
  const closeButton=id=>`<button type="button" class="icon-button" data-prompt-close="${id}" aria-label="关闭窗口" data-i18n-aria="close">×</button>`;
  const categoryFields=prefix=>`<label for="${prefix}-category" data-i18n="category">分类</label><select id="${prefix}-category" name="category" required></select><div id="${prefix}-new-category-field" hidden><label for="${prefix}-new-category" data-i18n="newCategoryName">新分类名称</label><input id="${prefix}-new-category" name="category_name" maxlength="80" autocomplete="off" disabled></div>`;
  const dialogs=document.createElement('div');
  dialogs.innerHTML=`<dialog id="prompt-create-dialog" class="prompt-dialog" aria-labelledby="prompt-create-heading"><div class="dialog-top"><h2 id="prompt-create-heading" data-i18n="create">新建素材</h2>${closeButton('prompt-create-dialog')}</div><form id="prompt-create-form"><fieldset id="prompt-create-fields"><label for="prompt-title" data-i18n="title">标题</label><input id="prompt-title" name="title" maxlength="200" required autocomplete="off"><div class="prompt-form-columns"><div>${categoryFields('prompt')}</div><div><label for="prompt-tags" data-i18n="tags">标签（可选）</label><input id="prompt-tags" name="tags" placeholder="用逗号分隔" data-i18n-placeholder="commaTags" autocomplete="off"></div></div><label for="prompt-original" data-i18n="originalText">原文</label><textarea id="prompt-original" name="original" rows="9" required spellcheck="false"></textarea><details id="prompt-optional-optimized" class="prompt-optional"><summary data-i18n="optionalAdaptation">添加优化版（可选）</summary><label for="prompt-optimized" data-i18n="adaptation">优化版</label><textarea id="prompt-optimized" name="optimized" rows="6" spellcheck="false"></textarea></details></fieldset><div id="prompt-create-error" class="prompt-error" role="alert" hidden></div><div class="prompt-form-actions"><button type="button" class="reference-button" data-prompt-close="prompt-create-dialog" data-i18n="cancel">取消</button><button id="prompt-save-button" type="submit" class="reference-button primary" data-i18n="saveItem">保存素材</button></div></form></dialog>
    <dialog id="category-create-dialog" class="prompt-dialog compact" aria-labelledby="category-create-heading"><div class="dialog-top"><h2 id="category-create-heading" data-i18n="newCategory">新增分类</h2>${closeButton('category-create-dialog')}</div><form id="category-create-form"><fieldset id="category-create-fields"><label for="category-name" data-i18n="categoryName">分类名称</label><input id="category-name" name="name" maxlength="80" required autocomplete="off"></fieldset><div id="category-create-error" class="prompt-error" role="alert" hidden></div><div class="prompt-form-actions"><button type="button" class="reference-button" data-prompt-close="category-create-dialog" data-i18n="cancel">取消</button><button id="category-save-button" type="submit" class="reference-button primary" data-i18n="addCategory">添加分类</button></div></form></dialog>
    <dialog id="prompt-classify-dialog" class="prompt-dialog compact" aria-labelledby="prompt-classify-heading"><div class="dialog-top"><h2 id="prompt-classify-heading" data-i18n="changeCategory">修改分类</h2>${closeButton('prompt-classify-dialog')}</div><p id="prompt-classify-title" class="prompt-context-title"></p><form id="prompt-classify-form"><fieldset id="prompt-classify-fields">${categoryFields('classify')}</fieldset><div id="prompt-classify-error" class="prompt-error" role="alert" hidden></div><div class="prompt-form-actions"><button type="button" class="reference-button" data-prompt-close="prompt-classify-dialog" data-i18n="cancel">取消</button><button id="prompt-classify-save-button" type="submit" class="reference-button primary" data-i18n="saveCategory">保存分类</button></div></form></dialog>`;
  document.body.append(dialogs);
  const sourceFields=document.createElement('details');sourceFields.className='prompt-optional';sourceFields.id='prompt-source-fields';
  sourceFields.innerHTML='<summary data-i18n="sourceNote">来源与说明（可选）</summary><label for="prompt-source-url" data-i18n="sourceLink">来源链接</label><input id="prompt-source-url" type="url" maxlength="2048" placeholder="https://…"><label for="prompt-source-note" data-i18n="sourceDescription">来源说明</label><textarea id="prompt-source-note" rows="3" maxlength="4000" placeholder="作者、出处或你记录的使用背景" data-i18n-placeholder="sourcePlaceholder"></textarea>';
  $('prompt-optional-optimized').before(sourceFields);
  const duplicateOpen=document.createElement('button');duplicateOpen.id='prompt-open-existing';duplicateOpen.type='button';duplicateOpen.className='reference-button';duplicateOpen.hidden=true;duplicateOpen.textContent=ui('打开已有素材，保留草稿','Open existing item and keep draft');$('prompt-create-error').after(duplicateOpen);
  const duplicateMessage=()=>ui("原文已存在。本次填写的改编、来源和其他补充尚未保存，草稿仍保留。请打开已有素材，用“新版本”或“补充来源”分别保存。","This original is already saved. Your adaptation, source and other changes are still in the draft. Open the existing item to save them as a new version or source note.");
  $('prompt-original').addEventListener('input',()=>{editor.duplicate=null;duplicateOpen.hidden=true;showError('prompt-create-error','');});
  const fileInput=document.createElement('input');fileInput.type='file';fileInput.id='prompt-import-file';fileInput.accept='.md,.txt,text/plain,text/markdown';fileInput.hidden=true;fileInput.setAttribute('aria-label',ui("选择提示词文本文件","Choose a prompt file"));document.body.append(fileInput);
  const importButton=document.createElement('button');importButton.type='button';importButton.className='reference-button prompt-import-button';importButton.dataset.promptAction='import';importButton.dataset.i18n='importFile';importButton.textContent='导入文件';$('prompt-create-dialog').querySelector('.dialog-top').insertBefore(importButton,$('prompt-create-dialog').querySelector('[data-prompt-close]'));
  const importNote=document.createElement('p');importNote.id='prompt-import-note';importNote.dataset.i18n='importNote';importNote.className='prompt-import-note';importNote.textContent='文件导入支持 UTF-8 的 .md / .txt，最大 256 KiB；确认后才会保存。';$('prompt-original').after(importNote);$('prompt-original').setAttribute('aria-describedby','prompt-import-note');

  const localizeEditor=()=>{window.LiubaiI18n.localize(dialogs,window.LiubaiLanguage||'zh');['prompt-category','classify-category'].forEach(id=>Array.from($(id).options).forEach(option=>{option.textContent=option.value===NEW_CATEGORY?t('newCategoryOption'):categoryName(option.value);}));};
  window.addEventListener('liubai-language-change',localizeEditor);localizeEditor();

  function showError(id,message){$(id).textContent=message;$(id).hidden=!message;}
  function hasDraft(){return ['prompt-title','prompt-original','prompt-optimized','prompt-tags','prompt-new-category','prompt-source-url','prompt-source-note'].some(id=>$(id).value.length>0);}
  function categoryOptions(prefix,preferred){
    const select=$(prefix+'-category');const previous=select.value;
    select.innerHTML=state.categories.map(category=>`<option value="${escapeHTML(category.id)}">${escapeHTML(categoryName(category.id))}</option>`).join('')+`<option value="${NEW_CATEGORY}">${t('newCategoryOption')}</option>`;
    select.value=[preferred,previous,'uncategorized',state.categories[0]?.id].find(id=>id===NEW_CATEGORY||state.categories.some(category=>category.id===id))||NEW_CATEGORY;
    toggleNewCategory(prefix);
  }
  function toggleNewCategory(prefix){
    const expanded=$(prefix+'-category').value===NEW_CATEGORY;$(prefix+'-new-category-field').hidden=!expanded;$(prefix+'-new-category').disabled=!expanded;$(prefix+'-new-category').required=expanded;
  }
  function categoryPayload(prefix){return $(prefix+'-category').value===NEW_CATEGORY?{category_name:$(prefix+'-new-category').value.trim()}:{category_id:$(prefix+'-category').value};}
  function showDialog(id,focusId){if(!$(id).open){editor.opener=document.activeElement;$(id).showModal();}$(focusId)?.focus();}
  function clearFilters(category='all'){
    window.ReferenceLibrary?.leave();state.query='';$('search').value='';state.view='all';state.category=category;state.expanded=state.expanded||category!=='all';
  }
  async function refreshCategories(){
    const data=await api('/api/categories');state.categories=data.categories;renderNavigation();window.ReferenceLibrary?.decorateNavigation();
  }
  async function openCreate(){
    categoryOptions('prompt',hasDraft()?$('prompt-category').value:state.category==='all'?'uncategorized':state.category);
    showError('prompt-create-error',editor.duplicate?duplicateMessage():'');showDialog('prompt-create-dialog','prompt-title');
    try{await refreshCategories();categoryOptions('prompt');}catch(error){showError('prompt-create-error',ui("分类读取失败：","Could not load categories: ")+error.message);}
  }
  async function importPromptFile(){
    const file=fileInput.files?.[0];fileInput.value='';if(!file||editor.saving||editor.importing)return;
    showError('prompt-create-error','');editor.importing=true;importButton.disabled=true;$('prompt-save-button').disabled=true;
    try{
      if(!/\.(md|txt)$/i.test(file.name))throw new Error(ui("请选择 .md 或 .txt 文件。","Choose a .md or .txt file."));
      if(file.size>256*1024)throw new Error(ui("文件超过 256 KiB，请拆分后导入。","This file exceeds 256 KiB. Split it before importing."));
      let original;try{original=new TextDecoder('utf-8',{fatal:true,ignoreBOM:true}).decode(await file.arrayBuffer());}catch{throw new Error(ui("文件不是有效的 UTF-8 文本，请转换编码后重试。","Convert this file to UTF-8 and try again."));}
      if(!original.trim())throw new Error(ui("文件内容为空，请选择包含提示词的文件。","Choose a file that contains a prompt."));
      if(hasDraft()&&!window.confirm(ui("导入文件会替换当前未保存的草稿，是否继续？","Importing this file will replace your unsaved draft. Continue?")))return;
      const category=$('prompt-category').value;$('prompt-create-form').reset();categoryOptions('prompt',category===NEW_CATEGORY?'uncategorized':category);$('prompt-optional-optimized').open=false;
      editor.duplicate=null;duplicateOpen.hidden=true;
      $('prompt-title').value=Array.from(file.name.replace(/\.(md|txt)$/i,'')).slice(0,200).join('');$('prompt-original').value=original;
      // textarea 会统一换行；未改正文时保留导入文件的原始 CRLF / LF 与 BOM。
      editor.imported={original,displayed:$('prompt-original').value};
      importNote.textContent=importedNote(file.name);$('prompt-original').focus();
    }catch(error){showError('prompt-create-error',error.message);}
    finally{editor.importing=false;importButton.disabled=false;$('prompt-save-button').disabled=editor.saving;}
  }
  function decorateDetail(){
    if(!state.detail||document.querySelector('#detail-pane [data-prompt-action="classify"]'))return;
    const controls=document.querySelector('#detail-pane .detail-topline > .detail-controls:last-child');if(!controls)return;
    const button=document.createElement('button');button.type='button';button.className='reference-button subtle prompt-classify-button';button.dataset.promptAction='classify';button.textContent=t('changeCategory');controls.prepend(button);
  }
  async function openClassification(){
    if(!state.detail)return;editor.classifyId=state.detail.item.id;editor.classifyVersion=state.detail.selected_version||state.detail.item.latest_version;
    $('prompt-classify-title').textContent=state.detail.item.title;$('classify-new-category').value='';categoryOptions('classify',state.detail.item.category_id);showError('prompt-classify-error','');showDialog('prompt-classify-dialog','classify-category');
    try{await refreshCategories();categoryOptions('classify');}catch(error){showError('prompt-classify-error',ui("分类读取失败：","Could not load categories: ")+error.message);}
  }
  async function savePrompt(event){
    event.preventDefault();if(editor.saving||editor.importing)return;
    const displayed=$('prompt-original').value;
    const original=editor.imported&&displayed===editor.imported.displayed?editor.imported.original:displayed,optimized=$('prompt-optimized').value;
    if(new TextEncoder().encode(original).byteLength>256*1024){showError('prompt-create-error',ui("原文超过 256 KiB，请拆分后保存。","Split the original before saving it. It exceeds 256 KiB."));return;}
    const body={title:$('prompt-title').value.trim(),original,...categoryPayload('prompt'),tags:[...new Set($('prompt-tags').value.split(/[,，、]/).map(tag=>tag.trim()).filter(Boolean))]};
    if(optimized.length)body.optimized=optimized;
    if($('prompt-source-url').value.trim())body.source_url=$('prompt-source-url').value.trim();
    if($('prompt-source-note').value.trim())body.source_note=$('prompt-source-note').value.trim();
    editor.saving=true;$('prompt-create-fields').disabled=true;$('prompt-save-button').disabled=true;$('prompt-save-button').textContent=ui("保存中…","Saving…");showError('prompt-create-error','');
    try{
      const result=await send('/api/prompts',body);
      if(result.duplicate){editor.duplicate=result;duplicateOpen.hidden=false;showError('prompt-create-error',duplicateMessage());return;}
      editor.duplicate=null;duplicateOpen.hidden=true;$('prompt-create-dialog').close();$('prompt-create-form').reset();editor.imported=null;importNote.textContent=t('importNote');$('prompt-optional-optimized').open=false;toggleNewCategory('prompt');
      clearFilters();await loadLibrary();const item=state.entries.find(entry=>entry.id===result.id);if(item){state.category=item.category_id;updateView();await selectEntry(result.id,true,result.version||null);$('tab-optimized')?.focus({preventScroll:true});}toast(result.duplicate?ui("已存在相同原文，已打开已有素材","This original already exists. Opened the existing item."):ui("素材已保存","Item saved"));
    }catch(error){showError('prompt-create-error',error.message);if(!$('prompt-create-dialog').open)$('prompt-create-dialog').showModal();}
    finally{editor.saving=false;$('prompt-create-fields').disabled=false;toggleNewCategory('prompt');$('prompt-save-button').disabled=false;$('prompt-save-button').textContent=t('saveItem');}
  }
  async function createCategory(event){
    event.preventDefault();if(editor.categorySaving)return;editor.categorySaving=true;$('category-create-fields').disabled=true;$('category-save-button').disabled=true;showError('category-create-error','');
    try{const result=await send('/api/categories',{name:$('category-name').value.trim()});await refreshCategories();$('category-create-dialog').close();$('category-create-form').reset();clearFilters(result.category.id);updateView();Array.from(document.querySelectorAll('#category-nav [data-category]')).find(node=>node.dataset.category===result.category.id)?.focus({preventScroll:true});toast(result.created?ui("分类已添加","Category added"):ui("已打开已有分类","Opened the existing category"));}
    catch(error){showError('category-create-error',error.message);if(!$('category-create-dialog').open)$('category-create-dialog').showModal();}
    finally{editor.categorySaving=false;$('category-create-fields').disabled=false;$('category-save-button').disabled=false;}
  }
  async function updateClassification(event){
    event.preventDefault();if(editor.classifying||!editor.classifyId)return;editor.classifying=true;$('prompt-classify-fields').disabled=true;$('prompt-classify-save-button').disabled=true;showError('prompt-classify-error','');
    const id=editor.classifyId,version=editor.classifyVersion,body=categoryPayload('classify');
    try{await send('/api/entries/'+encodeURIComponent(id)+'/metadata',body);$('prompt-classify-dialog').close();clearFilters();await loadLibrary();const item=state.entries.find(entry=>entry.id===id);if(item){state.category=item.category_id;updateView();await selectEntry(id,true,version);$('tab-optimized')?.focus({preventScroll:true});}toast(ui("分类已更新","Category updated"));}
    catch(error){showError('prompt-classify-error',error.message);if(!$('prompt-classify-dialog').open)$('prompt-classify-dialog').showModal();}
    finally{editor.classifying=false;$('prompt-classify-fields').disabled=false;toggleNewCategory('classify');$('prompt-classify-save-button').disabled=false;}
  }
  document.addEventListener('click',event=>{
    const closer=event.target.closest('[data-prompt-close]');if(closer){$(closer.dataset.promptClose).close();return;}
    const action=event.target.closest('[data-prompt-action]');if(!action)return;
    if(editor.saving){toast(ui("正在保存，请稍候。","Saving. Please wait."));return;}
    if($('help-dialog').open)$('help-dialog').close();
    if(action.dataset.promptAction==='new')openCreate();
    if(action.dataset.promptAction==='import'&&!editor.saving&&!editor.importing){if(!$('prompt-create-dialog').open)openCreate();fileInput.click();}
    if(action.dataset.promptAction==='new-category'){showError('category-create-error','');showDialog('category-create-dialog','category-name');}
    if(action.dataset.promptAction==='classify')openClassification();
  });
  fileInput.addEventListener('change',importPromptFile);
  window.addEventListener('beforeunload',event=>{if(hasDraft()){event.preventDefault();event.returnValue='';}});
  ['prompt','classify'].forEach(prefix=>$(prefix+'-category').addEventListener('change',()=>{toggleNewCategory(prefix);if($(prefix+'-category').value===NEW_CATEGORY)$(prefix+'-new-category').focus();}));
  ['prompt-create-dialog','category-create-dialog','prompt-classify-dialog'].forEach(id=>$(id).addEventListener('close',()=>{if(editor.opener?.isConnected)editor.opener.focus({preventScroll:true});}));
  $('prompt-create-form').addEventListener('submit',savePrompt);$('category-create-form').addEventListener('submit',createCategory);$('prompt-classify-form').addEventListener('submit',updateClassification);
  duplicateOpen.addEventListener('click',async()=>{
    if(editor.saving||!editor.duplicate)return;
    const result=editor.duplicate;$('prompt-create-dialog').close();clearFilters();
    try{await loadLibrary();await selectEntry(result.id,true,result.version||null);toast(ui("已打开已有素材。未保存的补充仍在“新建素材”草稿中。","Opened the existing item. Your unsaved changes remain in the new-item draft."));}
    catch(error){showError('prompt-create-error',error.message);showDialog('prompt-create-dialog','prompt-title');}
  });
  function importedNote(filename){
    return ui(`已读取 ${filename}；请确认标题、原文和分类后保存。`,`Loaded ${filename}. Check the title, original and category before saving.`);
  }
  window.PromptEditor={decorateDetail};decorateDetail();
})();
