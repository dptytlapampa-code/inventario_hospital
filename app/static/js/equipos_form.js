(function () {
  function handleSerialToggle() {
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
  }

  function handleNuevoEquipoToggle() {
    const nuevoSwitch = document.getElementById('esNuevoSwitch');
    if (!nuevoSwitch) {
      return;
    }
    const container = document.querySelector('[data-nuevo-fields]');
    if (!container) {
      return;
    }
    const toggleFields = () => {
      if (nuevoSwitch.checked) {
        container.removeAttribute('hidden');
      } else {
        container.setAttribute('hidden', '');
        container.querySelectorAll('input, select').forEach((input) => {
          if (input.type === 'checkbox' || input.type === 'radio') {
            input.checked = false;
          } else {
            input.value = '';
          }
        });
      }
    };
    nuevoSwitch.addEventListener('change', toggleFields);
    toggleFields();
  }

  document.addEventListener('DOMContentLoaded', () => {
    handleSerialToggle();
    handleNuevoEquipoToggle();
  });
})();
