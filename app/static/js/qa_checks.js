(function () {
  function logResult(ok, message) {
    const prefix = ok ? '[QA] ✅' : '[QA] ❌';
    console[ok ? 'info' : 'error'](`${prefix} ${message}`);
  }

  function validateArrayOfObjects(data, fields) {
    if (!Array.isArray(data)) {
      return false;
    }
    return data.every((item) => {
      if (typeof item !== 'object' || item === null) {
        return false;
      }
      return fields.every((field) => Object.prototype.hasOwnProperty.call(item, field));
    });
  }

  document.addEventListener('DOMContentLoaded', () => {
    const root = document.documentElement;
    if (root.dataset.qaChecks !== 'true') {
      return;
    }

    const form = document.querySelector('form[data-servicios-url][data-oficinas-url]');
    const hospitalSelect = document.getElementById('hospital_id');
    const servicioSelect = document.getElementById('servicio_id');
    const oficinaSelect = document.getElementById('oficina_id');

    logResult(!!form, 'Formulario con endpoints para servicios y oficinas está presente');
    logResult(!!hospitalSelect, 'Select de hospital presente');
    logResult(!!servicioSelect, 'Select de servicio presente');
    logResult(!!oficinaSelect, 'Select de oficina presente');

    if (!form || !hospitalSelect) {
      return;
    }

    const serviciosUrl = form.getAttribute('data-servicios-url');
    const oficinasUrl = form.getAttribute('data-oficinas-url');
    const firstHospitalOption = hospitalSelect.querySelector('option[value]:not([value=""])');

    if (!firstHospitalOption) {
      logResult(false, 'No hay hospital para validar servicios');
      return;
    }

    const hospitalId = firstHospitalOption.value;

    fetch(`${serviciosUrl}?${new URLSearchParams({ hospital_id: hospitalId })}`, {
      credentials: 'same-origin',
    })
      .then((response) => response.json())
      .then((data) => {
        const serviciosValidos = validateArrayOfObjects(data, ['id', 'nombre']);
        logResult(serviciosValidos, 'Respuesta de servicios cumple el contrato JSON');

        const firstServicio = Array.isArray(data) && data.length > 0 ? data[0] : null;
        if (!firstServicio || !firstServicio.id) {
          logResult(true, 'No hay servicios disponibles para validar oficinas');
          return;
        }

        return fetch(`${oficinasUrl}?${new URLSearchParams({ servicio_id: firstServicio.id })}`, {
          credentials: 'same-origin',
        })
          .then((response) => response.json())
          .then((oficinas) => {
            const oficinasValidas = validateArrayOfObjects(oficinas, ['id', 'nombre']);
            logResult(oficinasValidas, 'Respuesta de oficinas cumple el contrato JSON');
          });
      })
      .catch((error) => {
        logResult(false, `Error al validar servicios/oficinas: ${error}`);
      })
      .finally(() => {
        const initialTheme = root.getAttribute('data-bs-theme');
        const targetTheme = initialTheme === 'dark' ? 'light' : 'dark';
        const toggleButton = document.querySelector(`[data-theme-option="${targetTheme}"]`);

        if (!toggleButton) {
          logResult(false, 'No se encontró botón para alternar el tema');
          return;
        }

        const revertButton = document.querySelector(`[data-theme-option="${initialTheme}"]`);
        const originalFetch = window.fetch;

        if (typeof window.fetch === 'function') {
          window.fetch = function (input, init) {
            if (typeof input === 'string' && input.includes('/preferencias/tema')) {
              return Promise.resolve(
                new Response(JSON.stringify({ ok: true }), {
                  status: 200,
                  headers: { 'Content-Type': 'application/json' },
                }),
              );
            }
            return originalFetch.apply(this, arguments);
          };
        }

        toggleButton.click();
        const afterToggle = root.getAttribute('data-bs-theme');
        const themeChanged = afterToggle !== initialTheme;
        logResult(themeChanged, 'El toggler de tema actualiza data-bs-theme');

        if (revertButton && revertButton !== toggleButton) {
          revertButton.click();
        }

        if (typeof window.fetch === 'function') {
          window.fetch = originalFetch;
        }
      });
  });
})();
