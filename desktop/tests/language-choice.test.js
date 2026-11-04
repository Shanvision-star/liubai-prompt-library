const test = require('node:test');
const assert = require('node:assert/strict');
const { resolveLanguage, createController } = require('../web/language-choice.js');
test('manual choice and browser language take priority', async () => {
  assert.equal(await resolveLanguage({manual:'en',browser:['zh-CN'],system:'zh'}),'en');
  assert.equal(await resolveLanguage({browser:['ja','zh-Hant'],system:'en'}),'zh');
});
test('system locale is used only when browser has no supported language', async () => {
  let calls=0;const system=async()=>{calls++;return 'zh-CN';};
  assert.equal(await resolveLanguage({browser:['fr'],system}),'zh');
  assert.equal(await resolveLanguage({browser:['en'],system}),'en');
  assert.equal(calls,1);
  assert.equal(await resolveLanguage({browser:[],system:async()=>{throw Error();}}),'en');
});
test('malformed preferences are skipped', async () => {
  assert.equal(await resolveLanguage({manual:'en-invalid!',browser:['zh-Hant-TW'],system:'en'}),'zh');
  assert.equal(await resolveLanguage({browser:['zh-','en-US'],system:'zh'}),'en');
  assert.equal(await resolveLanguage({browser:['fr'],system:'zh__CN'}),'en');
});
test('late automatic result cannot override manual choice', async () => {
  let finish;const pending=new Promise(resolve=>{finish=resolve;});const shown=[];
  const controller=createController({browser:['ja'],system:()=>pending,apply:v=>shown.push(v)});
  const start=controller.auto();controller.choose('en');finish('zh');await start;
  assert.deepEqual(shown,['en']);
});
test('storage failures do not block selection', () => {
  const shown=[];const controller=createController({storage:{setItem(){throw Error();}},apply:v=>shown.push(v)});
  controller.choose('zh');assert.deepEqual(shown,['zh']);
});
test('saved manual choice persists until automatic mode', async () => {
  const values=new Map([['liubai.language','en']]);
  const storage={getItem:k=>values.get(k),setItem:(k,v)=>values.set(k,v),removeItem:k=>values.delete(k)};
  const shown=[];const controller=createController({storage,browser:['zh-CN'],apply:v=>shown.push(v)});
  await controller.start();await controller.auto();
  assert.deepEqual(shown,['en','zh']);assert.equal(values.has('liubai.language'),false);
});
