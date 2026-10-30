'use strict';
(() => {
  const stateful={version:null,source:null,saving:false,opener:null};
  const host=document.createElement('div');
  host.innerHTML=`<dialog id="version-dialog" class="prompt-dialog lifecycle-dialog" aria-labelledby="version-heading"><div class="dialog-top"><h2 id="version-heading">保存新版本</h2><button class="icon-button" data-lifecycle-close="version-dialog" aria-label="关闭新版本">×</button></div><p id="version-context" class="lifecycle-context"></p><form id="version-form"><fieldset id="version-fields"><label for="version-body">改编正文</label><textarea id="version-body" rows="12" required spellcheck="false"></textarea><label for="version-reason">改动理由</label><textarea id="version-reason" rows="2" maxlength="2000" required placeholder="说明这次改编适合什么任务，改了哪里。"></textarea></fieldset><p class="lifecycle-note">原文与旧版本保留。新版本的设计拆解需要重新生成，效果仍为待实测。</p><p id="version-error" class="prompt-error" role="alert" hidden></p><button type="button" id="version-reload" class="reference-button" hidden>读取最新版本，保留草稿</button><div class="prompt-form-actions"><button type="button" class="reference-button" data-lifecycle-close="version-dialog">取消</button><button id="version-save" class="reference-button primary" type="submit">保存新版本</button></div></form></dialog>
<dialog id="source-note-dialog" class="prompt-dialog lifecycle-dialog" aria-labelledby="source-note-heading"><div class="dialog-top"><h2 id="source-note-heading">补充来源</h2><button class="icon-button" data-lifecycle-close="source-note-dialog" aria-label="关闭补充来源">×</button></div><p id="source-note-context" class="lifecycle-context"></p><form id="source-note-form"><fieldset id="source-note-fields"><label for="source-note-url">来源链接 <span>可选</span></label><input id="source-note-url" type="url" maxlength="2048" placeholder="https://…"><label for="source-note-text">来源说明</label><textarea id="source-note-text" rows="5" maxlength="4000" required placeholder="作者、出处或你补充的使用背景"></textarea></fieldset><p class="lifecycle-note">补充记录单独留存，不覆盖已有固定来源、许可和原文。</p><p id="source-note-error" class="prompt-error" role="alert" hidden></p><div class="prompt-form-actions"><button type="button" class="reference-button" data-lifecycle-close="source-note-dialog">取消</button><button id="source-note-save" class="reference-button primary" type="submit">保存来源说明</button></div></form></dialog>`;
  document.body.append(host);
  const q=id=>document.getElementById(id);
  const send=(url,body)=>api(url,{method:'POST',headers:{'Content-Type':'application/json','X-Prompt-Library':'1'},body:JSON.stringify(body)});
  function error(id,message){q(id).textContent=message;q(id).hidden=!message;}
  function dirtyVersion(){return stateful.version&&(q('version-body').value!==stateful.version.initial||q('version-reason').value.trim());}
  function openVersion(){
    const d=state.detail;if(!d)return;
    if(dirtyVersion()&&stateful.version.id!==d.item.id&&!window.confirm('另一条素材还有未保存的改编。要放弃草稿并打开这条吗？'))return;
    const keep=dirtyVersion()&&stateful.version.id===d.item.id;
    if(!keep){q('version-body').value=d.optimized;stateful.version={id:d.item.id,expected:d.item.latest_version,based:d.selected_version,initial:q('version-body').value};q('version-reason').value='';}
    q('version-context').textContent=d.item.title+' · 基于 '+stateful.version.based+'，当前最新 '+stateful.version.expected;
    stateful.opener=document.activeElement;error('version-error','');q('version-reload').hidden=true;q('version-dialog').showModal();q('version-body').focus();
  }
  function openSource(){
    const d=state.detail;if(!d)return;
    if(stateful.source&&stateful.source!==d.item.id&&(q('source-note-url').value.trim()||q('source-note-text').value.trim())&&!window.confirm('另一条素材还有未保存的来源说明。要放弃草稿并打开这条吗？'))return;
    if(stateful.source!==d.item.id){q('source-note-form').reset();stateful.source=d.item.id;}
    q('source-note-context').textContent=d.item.id+' · '+d.item.title;
    stateful.opener=document.activeElement;error('source-note-error','');q('source-note-dialog').showModal();q('source-note-text').focus();
  }
  async function saveVersion(e){
    e.preventDefault();if(stateful.saving||!stateful.version)return;
    const draft=stateful.version,body=q('version-body').value;
    if(new TextEncoder().encode(body).length>256*1024){error('version-error','正文超过256 KiB，请缩短后保存。');return;}
    stateful.saving=true;q('version-fields').disabled=true;q('version-save').disabled=true;error('version-error','');
    try{
      const result=await send('/api/entries/'+draft.id+'/versions',{optimized:body,reason:q('version-reason').value,expected_version:draft.expected,based_on_version:draft.based});
      stateful.version=null;q('version-form').reset();q('version-dialog').close();await loadLibrary();await selectEntry(result.id,true,result.version,'optimized');toast(result.duplicate?'相同正文已经保存，已打开对应版本':'新版本已保存，原文与旧版本保留');
    }catch(e){error('version-error','保存未完成：'+e.message);q('version-reload').hidden=false;}
    finally{stateful.saving=false;q('version-fields').disabled=false;q('version-save').disabled=false;}
  }
  async function saveSource(e){
    e.preventDefault();if(stateful.saving||!stateful.source)return;
    stateful.saving=true;q('source-note-fields').disabled=true;q('source-note-save').disabled=true;error('source-note-error','');
    try{
      const id=stateful.source;const result=await send('/api/entries/'+id+'/source-notes',{source_url:q('source-note-url').value.trim(),source_note:q('source-note-text').value});
      q('source-note-form').reset();stateful.source=null;q('source-note-dialog').close();await selectEntry(id,false,state.detail.selected_version,'source');toast(result.duplicate?'相同来源说明已经保存':'来源说明已追加');
    }catch(e){error('source-note-error','保存未完成：'+e.message);}
    finally{stateful.saving=false;q('source-note-fields').disabled=false;q('source-note-save').disabled=false;}
  }
  function decorate(){
    if(!state.detail)return;
    const controls=document.querySelector('#detail-pane .detail-topline > .detail-controls:last-child');
    if(controls&&!controls.querySelector('[data-lifecycle=version]')){
      const b=document.createElement('button');b.type='button';b.className='reference-button subtle prompt-classify-button';b.dataset.lifecycle='version';b.textContent='新版本';controls.prepend(b);
    }
    const content=q('detail-content');
    if(state.tab==='analysis'&&!content.querySelector('.analysis-delegate')){
      const box=document.createElement('div');box.className='analysis-delegate';
      const text=document.createElement('p');text.textContent='使用你自己的 AI 客户端拆解这份素材，完成后回写到对应版本。';
      const b=document.createElement('button');b.type='button';b.className='reference-button';b.dataset.guideOpen='workflow';b.textContent=state.detail.analysis?'用我的 AI 重新拆解':'让我的 AI 生成拆解';box.append(text,b);content.prepend(box);
    }
    if(state.tab==='source'&&!content.querySelector('.source-supplements')){
      const section=document.createElement('section');section.className='source-supplements';
      const title=document.createElement('h3');title.textContent='我的来源补充';section.append(title);
      (state.detail.record.source_notes||[]).forEach(note=>{
        const item=document.createElement('div');item.className='source-supplement';
        const time=document.createElement('small');time.textContent=dateLabel(note.created_at);
        const p=document.createElement('p');p.textContent=note.source_note;
        item.append(time,p);const url=safeURL(note.source_url);if(url){const a=document.createElement('a');a.href=url;a.target='_blank';a.rel='noopener noreferrer';a.textContent='查看补充来源 ↗';item.append(a);}section.append(item);
      });
      const b=document.createElement('button');b.type='button';b.className='reference-button';b.dataset.lifecycle='source';b.textContent='补充来源';section.append(b);content.append(section);
    }
  }
  const original=window.PromptEditor.decorateDetail;
  window.PromptEditor.decorateDetail=()=>{original();decorate();};
  document.addEventListener('click',e=>{
    const close=e.target.closest('[data-lifecycle-close]');if(close){if(!stateful.saving)q(close.dataset.lifecycleClose).close();return;}
    const action=e.target.closest('[data-lifecycle]');if(action){if(action.dataset.lifecycle==='version')openVersion();else openSource();}
  });
  ['version-dialog','source-note-dialog'].forEach(id=>{
    q(id).addEventListener('cancel',e=>{if(stateful.saving)e.preventDefault();});
    q(id).addEventListener('close',()=>{if(stateful.opener?.isConnected)stateful.opener.focus({preventScroll:true});});
  });
  q('version-reload').addEventListener('click',async()=>{
    if(!stateful.version)return;
    try{const d=await api('/api/entries/'+stateful.version.id);stateful.version.expected=d.item.latest_version;q('version-context').textContent=d.item.title+' · 草稿基于 '+stateful.version.based+'，最新版本 '+stateful.version.expected;error('version-error','');q('version-reload').hidden=true;toast('已读取最新版本，你的草稿已保留');}catch(e){error('version-error','读取失败：'+e.message);}
  });
  q('version-form').addEventListener('submit',saveVersion);q('source-note-form').addEventListener('submit',saveSource);
  window.addEventListener('beforeunload',e=>{if(dirtyVersion()||q('source-note-text').value.trim()||q('source-note-url').value.trim()){e.preventDefault();e.returnValue='';}});
  decorate();
})();
