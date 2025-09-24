(function () {
  const body = document.body;
  const toggleButtons = document.querySelectorAll('[data-sidebar-toggle]');
  const backdrop = document.querySelector('.app-sidebar-backdrop');

  function toggleSidebar(force) {
    const shouldOpen = force !== undefined ? force : !body.classList.contains('sidebar-open');
    body.classList.toggle('sidebar-open', shouldOpen);
  }

  toggleButtons.forEach((btn) => {
    btn.addEventListener('click', () => toggleSidebar());
  });

  if (backdrop) {
    backdrop.addEventListener('click', () => toggleSidebar(false));
  }

  document.querySelectorAll('.app-sidebar .nav-link').forEach((link) => {
    link.addEventListener('click', () => {
      if (window.innerWidth < 992) {
        toggleSidebar(false);
      }
    });
  });
})();
