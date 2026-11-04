'use strict';
(function(){
  const selector=document.getElementById('language-select');
  const menu=document.getElementById('settings-menu');
  const toggle=menu.querySelector('summary');
  document.addEventListener('click',event=>{if(menu.open&&!menu.contains(event.target))menu.open=false;});
  menu.addEventListener('keydown',event=>{if(event.key==='Escape'&&menu.open){event.preventDefault();menu.open=false;toggle.focus();}});
  const notice=document.getElementById('language-save-status');
  let storage;try{storage=window.localStorage;}catch(_){storage=null;}
  const readLocal=path=>fetch(path,{signal:AbortSignal.timeout(1500)});
  const controller=window.LiubaiLanguageChoice.createController({
    storage,browser:navigator.languages?.length?navigator.languages:[navigator.language],
    system:async()=>{const response=await readLocal('/api/system-language');return response.ok?(await response.json()).language:'';},
    apply:language=>{
      window.LiubaiI18n.localize(document,language);
      document.title=language==='en'?'Liubai · Prompt Library':'留白 · 提示词素材库';
      document.getElementById('search').placeholder=window.LiubaiI18n.translate(language,'search');
      document.documentElement.lang=language==='zh'?'zh-CN':'en';
      window.LiubaiLanguage=language;
      window.dispatchEvent(new CustomEvent('liubai-language-change',{detail:{language}}));
    }
  });
  let revision=0, saves=Promise.resolve();
  function save(value){
    saves=saves.catch(()=>{}).then(async()=>{
      const response=await fetch('/api/language-preference',{method:'POST',headers:{'Content-Type':'application/json','X-Prompt-Library':'1'},body:JSON.stringify({language:value}),signal:AbortSignal.timeout(3000)});
      if(!response.ok)throw Error('save failed');
      notice.textContent='';
    }).catch(()=>{notice.textContent=window.LiubaiI18n.translate(window.LiubaiLanguage,'languageSaveFailed');});
  }
  selector.addEventListener('change',()=>{
    revision++;const value=selector.value;
    const toggle=document.querySelector('.settings-toggle');toggle.classList.remove('ripple');void toggle.offsetWidth;toggle.classList.add('ripple');
    if(value==='auto')controller.auto();else controller.choose(value);
    save(value);
  });
  (async()=>{
    const initialRevision=revision;
    try {
      const response=await readLocal('/api/language-preference');if(!response.ok)throw Error('read failed');
      const value=(await response.json()).language;
      if(initialRevision!==revision)return;
      if(!['auto','zh','en'].includes(value))throw Error('bad preference');
      selector.value=value;
      if(value==='auto')await controller.auto();else controller.choose(value);
    } catch(_){
      if(initialRevision!==revision)return;
      let preference;try{preference=storage?.getItem('liubai.language');}catch(_){preference=null;}
      selector.value=['zh','en'].includes(preference)?preference:'auto';
      await controller.start();
      if(initialRevision===revision)notice.textContent=window.LiubaiI18n.translate(window.LiubaiLanguage,'languageReadFailed');
    }
  })();
})();
