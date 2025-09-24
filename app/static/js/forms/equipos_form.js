(function () {
  function onReady(callback) {
    if (document.readyState === 'loading') {
      document.addEventListener('DOMContentLoaded', callback, { once: true });
      return;
    }
    callback();
  }

  function initSerialToggle() {
    const container = document.querySelector('[data-serial-container]');
    if (!container) {
      return;
    }

    const serialInput = container.querySelector('[data-serial-input]');
    const toggle = document.querySelector('[data-serial-toggle]');
    const message = container.querySelector('[data-serial-message]');

    if (!serialInput || !toggle) {
      return;
    }

    const defaultMessage = message ? message.textContent : '';
    const originalValue = serialInput.value;
    let manualValue = serialInput.value;

    serialInput.addEventListener('input', () => {
      manualValue = serialInput.value;
    });

    function updateSerialState() {
      const disabled = toggle.checked;
      if (disabled) {
        serialInput.setAttribute('disabled', 'disabled');
        manualValue = serialInput.value;
        if (message) {
          message.textContent = originalValue
            ? `Código interno actual: ${originalValue}`
            : defaultMessage;
          message.classList.remove('d-none');
        }
      } else {
        serialInput.removeAttribute('disabled');
        serialInput.value = manualValue;
        if (message) {
          message.textContent = defaultMessage;
          message.classList.add('d-none');
        }
      }
    }

    toggle.addEventListener('change', updateSerialState);
    updateSerialState();
  }

  function initLookupHierarchy() {
    const hospitalHidden = document.getElementById('hospital_id');
    const servicioHidden = document.getElementById('servicio_id');
    const oficinaHidden = document.getElementById('oficina_id');

    const servicioInput = document.getElementById('servicio_busqueda');
    const oficinaInput = document.getElementById('oficina_busqueda');

    if (
      !hospitalHidden ||
      !servicioHidden ||
      !oficinaHidden ||
      !servicioInput ||
      !oficinaInput
    ) {
      return;
    }

    let previousHospital = hospitalHidden.value;

    function clearLookup(input) {
      if (!input) {
        return;
      }
      const hidden = document.getElementById(input.dataset.lookupHidden || '');
      if (hidden) {
        hidden.value = '';
        hidden.dispatchEvent(new Event('change', { bubbles: true }));
      }
      input.dataset.lookupSkipNext = 'true';
      input.value = '';
      input.dispatchEvent(new Event('input', { bubbles: true }));
    }

    function toggleLookupAvailability(input, enabled) {
      if (!input) {
        return;
      }

      if (enabled) {
        input.removeAttribute('disabled');
      } else {
        input.setAttribute('disabled', 'disabled');
      }

      const control = input.closest('.lookup-control');
      if (!control) {
        return;
      }

      const showAll = control.querySelector('[data-lookup-show-all]');
      if (showAll) {
        showAll.toggleAttribute('disabled', !enabled);
      }

      if (!enabled) {
        const results = control.querySelector('[data-lookup-results]');
        if (results) {
          results.classList.add('d-none');
        }
      }
    }

    function updateServiceAvailability() {
      toggleLookupAvailability(servicioInput, Boolean(hospitalHidden.value));
    }

    function updateOfficeAvailability() {
      toggleLookupAvailability(oficinaInput, Boolean(servicioHidden.value));
    }

    hospitalHidden.addEventListener('change', () => {
      if (hospitalHidden.value !== previousHospital) {
        clearLookup(servicioInput);
        clearLookup(oficinaInput);
        previousHospital = hospitalHidden.value;
      }
      updateServiceAvailability();
      updateOfficeAvailability();
    });

    servicioHidden.addEventListener('change', () => {
      if (!servicioHidden.value) {
        clearLookup(oficinaInput);
      }
      updateOfficeAvailability();
    });

    // Initialise according to the current persisted values.
    updateServiceAvailability();
    updateOfficeAvailability();
  }

  onReady(() => {
    initSerialToggle();
    initLookupHierarchy();
  });
})();
