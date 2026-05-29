// Lightweight client-side i18n loader.
// Exposes window.i18n = { locale, t(key, vars?), applyToDom(root?), onChange(cb), setLocale(locale), available, ready }

(function () {
  const AVAILABLE = ['ko', 'en'];
  const FALLBACK = 'ko';
  const STORAGE_KEY = 'demoLocale';

  const tables = {};        // { ko: {...}, en: {...} }
  const listeners = [];
  let current = FALLBACK;
  let readyResolve;
  const ready = new Promise(r => { readyResolve = r; });

  function normalize(loc) {
    if (!loc) return null;
    const v = String(loc).trim().toLowerCase().split('-')[0];
    return AVAILABLE.includes(v) ? v : null;
  }

  function pickInitialLocale() {
    const params = new URLSearchParams(window.location.search);
    const fromQuery = normalize(params.get('lang') || params.get('locale'));
    if (fromQuery) return fromQuery;
    try {
      const stored = normalize(localStorage.getItem(STORAGE_KEY));
      if (stored) return stored;
    } catch (_) { /* localStorage may be blocked */ }
    const nav = normalize(navigator.language);
    return nav || FALLBACK;
  }

  async function loadTable(loc) {
    if (tables[loc]) return tables[loc];
    const resp = await fetch(`i18n/${loc}.json`, { cache: 'no-cache' });
    if (!resp.ok) throw new Error(`Failed to load locale ${loc}`);
    tables[loc] = await resp.json();
    return tables[loc];
  }

  function format(value, vars) {
    if (!vars || typeof value !== 'string') return value;
    return value.replace(/\{(\w+)\}/g, (_, k) => (k in vars ? String(vars[k]) : `{${k}}`));
  }

  function t(key, vars) {
    const cur = tables[current] || {};
    const fb = tables[FALLBACK] || {};
    const value = (key in cur) ? cur[key] : (key in fb ? fb[key] : key);
    return format(value, vars);
  }

  function applyToDom(root) {
    const scope = root || document;
    scope.querySelectorAll('[data-i18n]').forEach(el => {
      const key = el.getAttribute('data-i18n');
      if (!key) return;
      el.textContent = t(key);
    });
    scope.querySelectorAll('[data-i18n-placeholder]').forEach(el => {
      const key = el.getAttribute('data-i18n-placeholder');
      if (!key) return;
      el.setAttribute('placeholder', t(key));
    });
    scope.querySelectorAll('[data-i18n-title]').forEach(el => {
      const key = el.getAttribute('data-i18n-title');
      if (!key) return;
      el.setAttribute('title', t(key));
    });
    if (scope === document) {
      document.documentElement.setAttribute('lang', current);
    }
  }

  async function setLocale(loc, opts) {
    const normalized = normalize(loc) || FALLBACK;
    if (normalized === current && tables[normalized]) return current;
    await loadTable(normalized);
    current = normalized;
    try { localStorage.setItem(STORAGE_KEY, normalized); } catch (_) {}
    applyToDom();
    if (!opts || !opts.silent) {
      listeners.forEach(cb => {
        try { cb(current); } catch (e) { console.error(e); }
      });
    }
    return current;
  }

  function onChange(cb) {
    if (typeof cb === 'function') listeners.push(cb);
  }

  async function init() {
    const initial = pickInitialLocale();
    try {
      await loadTable(initial);
      current = initial;
    } catch (e) {
      console.warn('i18n init failed for', initial, e);
      await loadTable(FALLBACK);
      current = FALLBACK;
    }
    try { localStorage.setItem(STORAGE_KEY, current); } catch (_) {}
    applyToDom();
    readyResolve(current);
  }

  window.i18n = {
    get locale() { return current; },
    available: AVAILABLE.slice(),
    t,
    applyToDom,
    setLocale,
    onChange,
    ready,
  };

  // Kick off as soon as parsed.
  init();
})();
