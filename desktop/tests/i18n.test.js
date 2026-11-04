const test = require('node:test');
const assert = require('node:assert/strict');
const {translate} = require('../web/i18n.js');
test('message keys have explicit language fallback and interpolation', () => {
  assert.equal(translate('en','all'), 'All items');
  assert.equal(translate('zh','all'), '全部素材');
  assert.equal(translate('en','count',{count:2}), '2 items');
  assert.equal(translate('en','unknown.key'), 'unknown.key');
});

test('English reading preserves original and only prefers a verified translation', () => {
  const { readingView } = require('../web/i18n.js');
  assert.deepEqual(readingView('en',{original:'中文',translation:'English',translation_status:'ready'},false),{primary:'English',original:'中文',kind:'translation',foldOriginal:true});
  assert.deepEqual(readingView('en',{original:'中文',translation:'',translation_status:'missing'},false),{primary:'中文',original:'',kind:'original',foldOriginal:false});
  assert.deepEqual(readingView('en',{original:'Original',translation:'中文',translation_status:'ready'},true),{primary:'Original',original:'中文',kind:'original',foldOriginal:true});
});

test('declared UI translation keys resolve in both languages', () => {
  const fs = require('node:fs'), path = require('node:path');
  const root = path.join(__dirname, '../web');
  const files=['index.html','prompts.js','references.js'];
  const keys=new Set();
  for (const file of files) {
    const source=fs.readFileSync(path.join(root,file),'utf8');
    for (const match of source.matchAll(/data-i18n(?:-aria|-title|-placeholder)?="([\w]+)"/g)) keys.add(match[1]);
  }
  for(const key of keys) for(const lang of ['en','zh']) assert.notEqual(translate(lang,key),key,`${lang}: ${key}`);
});
