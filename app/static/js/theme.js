(function () {
  const doc = document.documentElement;

  function sanitizeTheme(theme) {
    return theme === 'dark' ? 'dark' : 'light';
  }

  function setActiveButton(theme) {
    document
      .querySelectorAll('[data-theme-option]')
      .forEach((btn) => btn.classList.toggle('active', btn.getAttribute('data-theme-option') === theme));
  }

  function applyTheme(theme, { silent = false } = {}) {
    const effective = sanitizeTheme(theme);
    doc.dataset.themePref = effective;
    doc.setAttribute('data-bs-theme', effective);
    setActiveButton(effective);
    if (!silent) {
      document.dispatchEvent(new CustomEvent('theme:changed', { detail: { theme: effective } }));
    }
  }

  function persistTheme(theme) {
    const csrfToken = document.querySelector('meta[name="csrf-token"]').getAttribute('content');
    fetch('/preferencias/tema', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'X-CSRFToken': csrfToken,
      },
      body: JSON.stringify({ theme: sanitizeTheme(theme) }),
    }).catch(() => {
      // Network failures shouldn't break the UI; the preference will be retried on next change.
    });
  }

  const initialTheme = sanitizeTheme(doc.dataset.themePref || 'light');
  applyTheme(initialTheme, { silent: true });

  document.querySelectorAll('[data-theme-option]').forEach((btn) => {
    btn.addEventListener('click', (event) => {
      event.preventDefault();
      const theme = sanitizeTheme(btn.getAttribute('data-theme-option'));
      applyTheme(theme);
      persistTheme(theme);
    });
  });
})();
