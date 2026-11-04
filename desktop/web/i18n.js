'use strict';
(function(root){
  const messages={
    brandHome:["留白，返回全部素材","Liubai, back to all items"],
    helpData:["使用与数据","Help and data"],
    settings:["语言和反馈","Language and feedback"],
    spaces:["素材与参考","Items and references"],
    browse:["浏览素材与分类","Browse items and categories"],
    quickCategories:["快捷分类","Quick categories"],
    sort:["排序","Sort"],
    collection:["素材列表","Item list"],
    detail:["素材详情","Item details"],
    reading:["读取中","Loading"],
    opening:["正在打开你的素材库…","Opening your library…"],
    readingLibrary:["正在读取素材…","Loading your items…"],
    feedbackTitle:["反馈与建议","Feedback"],
    feedbackNote:["请选择反馈方式。请勿发送密码或敏感素材。","Choose a channel. Keep passwords and sensitive material out of your feedback."],
    emailFeedback:["发送邮件","Email feedback"],
    emailApp:["（使用你的邮件应用）"," (opens your email app)"],
    issueNote:["（公开可见，可能需要登录）"," (public; sign-in may be required)"],
    languageReadFailed:["语言设置暂不可读取。","Language settings are unavailable."],
    languageSaveFailed:["语言选择未能保存；重启后请检查设置。","Could not save your language choice. Check Settings after restarting."],
    all:['全部素材','All items'], count:['{count} 条素材','{count} items'],
    favorite:['我的收藏','Favorites'], recent:['最近收录','Recently added'], categories:['按用途分类','Categories'],
    home:['我的空间','My library'], personal:['我的素材','My items'], references:['参考库','References'],
    guide:['使用说明','User guide'], import:['导入','Import'], create:['新建素材','New item'],
    feedback:['反馈','Feedback'], refresh:['刷新素材库','Refresh library'], search:['搜索标题、标签或正文','Search titles, tags or text'],
    sortUpdated:['最近更新','Recently updated'], sortRecent:['最近收录','Recently added'], sortTitle:['标题排序','Title'],
    local:['本机素材库','Local library'], language:['语言','Language'], auto:['自动','Automatic'],
    original:['原文与译文','Original & translation'], analysis:['拆解分析','Analysis'], optimized:['复用改写','Adaptation'],
    source:['来源','Source'], originalPrompt:['原文提示词','Original prompt'], copyOriginal:['复制原提示词','Copy original'],
    copyTranslation:['复制译文','Copy translation'], showChinese:['展开中文','Show Chinese'], hideChinese:['收起中文','Hide Chinese'],
    missingEnglish:['英文译文尚未提供','English translation unavailable'],
    title:['标题','Title'], category:['分类','Category'], newCategory:['新增分类','Add category'],
    categoryName:['分类名称','Category name'], newCategoryName:['新分类名称','New category name'],
    tags:['标签（可选）','Tags (optional)'], originalText:['原文','Original'], optionalAdaptation:['添加优化版（可选）','Add an adaptation (optional)'],
    adaptation:['优化版','Adaptation'], cancel:['取消','Cancel'], saveItem:['保存素材','Save item'],
    addCategory:['添加分类','Add category'], changeCategory:['修改分类','Change category'], saveCategory:['保存分类','Save category'],
    sourceNote:['来源与说明（可选）','Source and notes (optional)'], sourceLink:['来源链接','Source link'], sourceDescription:['来源说明','Source notes'],
    addSource:['添加来源','Add source'], discover:['发现','Discover'], following:['已关注','Following'], updates:['更新','Updates'], searchGithub:['搜索 GitHub','Search GitHub'], searchReferences:['搜索参考或 GitHub','Search references or GitHub'], allCategories:['全部分类','All categories'], favoriteAction:['收藏','Favorites'], addGithub:['添加 GitHub 来源','Add GitHub source'], repoLink:['仓库或文件链接','Repository or file URL'], assignCategory:['归入分类','Category'], readSource:['读取来源','Read source'], adopt:['采用到我的素材','Add to my items'], saveLocation:['保存位置','Save location'], confirmAdopt:['确认采用','Confirm'],
    importFile:['导入文件','Import file'], close:['关闭窗口','Close dialog'], commaTags:['用逗号分隔','Separate with commas'], sourcePlaceholder:['作者、出处或你记录的使用背景','Author, source or context'], newCategoryOption:['新分类…','New category…'], importNote:['文件导入支持 UTF-8 的 .md / .txt，最大 256 KiB；确认后才会保存。','Import UTF-8 .md or .txt files up to 256 KiB. The item is saved only after confirmation.'],
  };
  function translate(language,key,variables={}){
    const row=messages[key];if(!row)return key;
    return row[language==='en'?1:0].replace(/\{(\w+)\}/g,(match,name)=>Object.hasOwn(variables,name)?String(variables[name]):match);
  }
  function readingView(language,pair,originalIsEnglish=false){
    const original=pair.original||'';
    const translated=pair.translation_status==='ready'?(pair.translation||''):'';
    if(language==='en' && translated){
      return originalIsEnglish
        ? {primary:original,original:translated,kind:'original',foldOriginal:true}
        : {primary:translated,original,kind:'translation',foldOriginal:true};
    }
    return {primary:original,original:'',kind:'original',foldOriginal:false};
  }
  const originalMarkup = new WeakMap();
  function localizeMarkup(root,language,key,attribute){
    root.querySelectorAll('[data-'+key+']').forEach(el=>{
      if(!originalMarkup.has(el))originalMarkup.set(el,{});
      const originals=originalMarkup.get(el);
      if(!Object.hasOwn(originals,key))originals[key]=attribute?el.getAttribute(attribute):el.textContent;
      const text=language==='en'?el.getAttribute('data-'+key):originals[key];
      if(attribute)el.setAttribute(attribute,text);
      else el.textContent=text;
    });
  }
  function localize(root,language){
    root.querySelectorAll('[data-i18n]').forEach(el=>{el.textContent=translate(language,el.dataset.i18n);});
    root.querySelectorAll('[data-i18n-aria]').forEach(el=>el.setAttribute('aria-label',translate(language,el.dataset.i18nAria)));
    root.querySelectorAll('[data-i18n-title]').forEach(el=>el.title=translate(language,el.dataset.i18nTitle));
    root.querySelectorAll('[data-i18n-placeholder]').forEach(el=>el.placeholder=translate(language,el.dataset.i18nPlaceholder));
    localizeMarkup(root,language,'en');
    localizeMarkup(root,language,'en-aria-label','aria-label');
    localizeMarkup(root,language,'en-placeholder','placeholder');
  }
  const apiErrors=Object.freeze({
  "仅允许本机入口": "Access is limited to this device.",
  "请从本机素材库下载备份": "Download the backup from your local library.",
  "请从本机素材库操作，或为本机API提供有效的Bearer令牌": "Open your local library or supply a valid bearer token for the local API.",
  "本机操作未完成，请检查目录权限或稍后重试；已有资料仍保留": "The operation could not finish. Check folder permissions or try again. Your existing material is still available.",
  "找不到这条素材，请刷新列表": "Item not found. Refresh the list.",
  "找不到这条素材": "Item not found.",
  "找不到这个优化版本": "Adaptation version not found.",
  "分类不存在，请选择已有分类或填写新分类名称": "Choose an existing category or enter a new category name.",
  "已有分类编号与新分类名称只能选择一种": "Choose an existing category or enter a new name.",
  "请选择库内分类": "Choose a category from this library.",
  "来源链接需为不含账号凭据的 http 或 https 网址": "Enter an HTTP or HTTPS source URL without account credentials.",
  "标签必须是最多 30 个元素的文本列表": "Enter up to 30 tags.",
  "原文不能为空": "Enter the original text.",
  "标题不能为空": "Enter a title.",
  "原文校验不一致，请先核对资料文件": "The original checksum did not match. Verify your library files.",
  "版本正文校验不一致，请先核对资料文件": "The version checksum did not match. Verify your library files.",
  "请先预览，并提交快照及拆解版本后再采用": "Preview the reference again before adding it to your items.",
  "参考已更新，请重新预览后采用": "The reference was updated. Preview it again before adding it.",
  "找不到这份参考": "Reference not found.",
  "找不到该快照": "Snapshot not found.",
  "GitHub 仓库格式无效": "Enter a valid GitHub repository.",
  "来源文件路径无效": "The source file path is invalid.",
  "备份超过 256 MiB 或 10000 个文件，请停止服务后复制整个资料目录": "The backup exceeds 256 MiB or 10,000 files. Stop Liubai and copy the entire data folder.",
  "资料包含符号链接或目录联接，请先核对后再备份": "Check the symbolic links or junctions in the library before exporting a backup."
});
  function error(language,raw,fallback){
    if(typeof raw!=='string'||!raw.trim())return fallback;
    if(language!=='en')return raw;
    return Object.hasOwn(apiErrors,raw)?apiErrors[raw]:(/\p{Script=Han}/u.test(raw)?fallback:raw);
  }
  const api={translate,readingView,localize,error};
  if(typeof module!=='undefined'&&module.exports)module.exports=api;else root.LiubaiI18n=api;
})(globalThis);
