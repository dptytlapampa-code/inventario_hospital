(function () {
  const doc = document.documentElement;
  const prefersDark = window.matchMedia('(prefers-color-scheme: dark)');

  function systemTheme() {
    return prefersDark.matches ? 'dark' : 'light';
  }

  function applyTheme(theme) {
    const effective = theme === 'system' ? systemTheme() : theme;
    doc.dataset.themePref = theme;
    doc.setAttribute('data-bs-theme', effective);
    document
      .querySelectorAll('[data-theme-option]')
      .forEach((btn) => btn.classList.toggle('active', btn.getAttribute('data-theme-option') === theme));
  }

  function persistTheme(theme) {
    const csrfToken = document.querySelector('meta[name="csrf-token"]').getAttribute('content');
    fetch('/preferencias/tema', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'X-CSRFToken': csrfToken,
      },
      body: JSON.stringify({ theme }),
    }).catch(() => {
      // Network failures shouldn't break the UI; the preference will be retried on next change.
    });
  }

  applyTheme(doc.dataset.themePref || 'system');

  prefersDark.addEventListener('change', () => {
    if (doc.dataset.themePref === 'system') {
      applyTheme('system');
    }
  });

  document.querySelectorAll('[data-theme-option]').forEach((btn) => {
    btn.addEventListener('click', (event) => {
      event.preventDefault();
      const theme = btn.getAttribute('data-theme-option');
      if (!theme) {
        return;
      }
      applyTheme(theme);
      persistTheme(theme);
    });
  });
})();
