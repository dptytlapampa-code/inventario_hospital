(function () {
  /**
   * Sistema de tematización global
   * --------------------------------
   * - Lee y escribe `data-bs-theme` en <html> para que Bootstrap y nuestro CSS
   *   reaccionen correctamente.
   * - Guarda la preferencia en localStorage y respeta el `prefers-color-scheme`
   *   cuando no exista una selección manual.
   * - Emite el evento personalizado `theme:changed` cada vez que el tema cambia
   *   para que otros módulos puedan reaccionar.
   * - Para añadir nuevos temas o matices, expón el tema en CSS bajo
   *   `[data-bs-theme='<nombre>']` y en JS agrégalo a los botones con
   *   `data-theme-option`.
   */

  const STORAGE_KEY = 'theme-preference';
  const doc = document.documentElement;
  const themeButtons = document.querySelectorAll('[data-theme-option]');
  const systemQuery = window.matchMedia ? window.matchMedia('(prefers-color-scheme: dark)') : null;

  function sanitizeTheme(theme) {
    return theme === 'dark' ? 'dark' : 'light';
  }

  function getStoredTheme() {
    try {
      const stored = localStorage.getItem(STORAGE_KEY);
      return stored ? sanitizeTheme(stored) : null;
    } catch (error) {
      return null;
    }
  }

  function setStoredTheme(theme) {
    try {
      localStorage.setItem(STORAGE_KEY, sanitizeTheme(theme));
    } catch (error) {
      // Sin almacenamiento disponible, simplemente ignoramos.
    }
  }

  function setActiveButton(theme) {
    themeButtons.forEach((btn) => {
      btn.classList.toggle('active', sanitizeTheme(btn.getAttribute('data-theme-option')) === theme);
    });
  }

  function applyTheme(theme, { silent = false } = {}) {
    const effective = sanitizeTheme(theme);
    doc.setAttribute('data-bs-theme', effective);
    setActiveButton(effective);
    if (!silent) {
      document.dispatchEvent(new CustomEvent('theme:changed', { detail: { theme: effective } }));
    }
  }

  function resolvePreferredTheme() {
    const stored = getStoredTheme();
    if (stored) {
      return stored;
    }
    if (systemQuery) {
      return systemQuery.matches ? 'dark' : 'light';
    }
    return 'light';
  }

  function handleSystemChange(event) {
    if (!getStoredTheme()) {
      applyTheme(event.matches ? 'dark' : 'light');
    }
  }

  applyTheme(resolvePreferredTheme(), { silent: true });

  if (systemQuery) {
    if (typeof systemQuery.addEventListener === 'function') {
      systemQuery.addEventListener('change', handleSystemChange);
    } else if (typeof systemQuery.addListener === 'function') {
      systemQuery.addListener(handleSystemChange);
    }
  }

  themeButtons.forEach((btn) => {
    btn.addEventListener('click', (event) => {
      event.preventDefault();
      const theme = sanitizeTheme(btn.getAttribute('data-theme-option'));
      setStoredTheme(theme);
      applyTheme(theme);
    });
  });

  window.addEventListener('storage', (event) => {
    if (event.key === STORAGE_KEY) {
      const storedTheme = event.newValue ? sanitizeTheme(event.newValue) : null;
      applyTheme(storedTheme || resolvePreferredTheme());
    }
  });
})();
