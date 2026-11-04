'use strict';
(function (root) {
  function supported(value) {
    if (typeof value !== 'string') return null;
    const match = /^(zh|en)(?:[-_][a-z0-9]{1,8})*$/i.exec(value.trim());
    return match ? match[1].toLowerCase() : null;
  }
  async function resolveLanguage({manual, browser = [], system} = {}) {
    const chosen = supported(manual);
    if (chosen) return chosen;
    for (const value of browser) { const match = supported(value); if (match) return match; }
    try { return supported(typeof system === 'function' ? await system() : system) || 'en'; }
    catch (_) { return 'en'; }
  }
  function createController({storage, browser = [], system, apply}) {
    let generation = 0;
    const key = 'liubai.language';
    return {
      async start() {
        let stored;
        try { stored = storage?.getItem(key); } catch (_) { stored = null; }
        if (supported(stored)) return this.choose(stored);
        return this.auto();
      },
      async auto() {
        const current = ++generation;
        try { storage?.removeItem(key); } catch (_) { /* 本次会话仍可自动选择。 */ }
        const value = await resolveLanguage({browser, system});
        if (current === generation) apply(value);
      },
      choose(value) {
        const selected = supported(value);
        if (!selected) throw new TypeError('unsupported language');
        generation++;
        try { storage?.setItem(key, selected); } catch (_) { /* 当前页面仍可切换。 */ }
        apply(selected);
      }
    };
  }
  const api = {resolveLanguage, createController};
  if (typeof module !== 'undefined' && module.exports) module.exports = api;
  else root.LiubaiLanguageChoice = api;
})(globalThis);
