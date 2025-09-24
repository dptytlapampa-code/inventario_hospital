(function () {
  document.addEventListener('DOMContentLoaded', () => {
    const container = document.querySelector('[data-serial-container]');
    if (!container) {
      initLookups();
      return;
    }
    const serialInput = container.querySelector('[data-serial-input]');
    const toggle = document.querySelector('[data-serial-toggle]');
    const message = container.querySelector('[data-serial-message]');
    if (!serialInput || !toggle) {
      initLookups();
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
          message.textContent = originalValue ? `Código interno actual: ${originalValue}` : defaultMessage;
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
    initLookups();
  });

  function initLookups() {
    const hospitalHidden = document.querySelector('#hospital_id');
    const servicioHidden = document.querySelector('#servicio_id');
    const oficinaHidden = document.querySelector('#oficina_id');
    const servicioInput = document.querySelector('#servicio_busqueda');
    const oficinaInput = document.querySelector('#oficina_busqueda');

    if (!hospitalHidden || !servicioHidden || !oficinaHidden || !servicioInput || !oficinaInput) {
      return;
    }

    let previousHospital = hospitalHidden.value;

    function clearLookup(input) {
      if (!input) {
        return;
      }
      if (!input.value) {
        const hidden = document.getElementById(input.dataset.lookupHidden || '');
        if (hidden) {
          hidden.value = '';
          hidden.dispatchEvent(new Event('change', { bubbles: true }));
        }
        return;
      }
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
        if (enabled) {
          showAll.removeAttribute('disabled');
        } else {
          showAll.setAttribute('disabled', 'disabled');
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

    updateServiceAvailability();
    updateOfficeAvailability();
  }
})();
