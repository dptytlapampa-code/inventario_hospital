(function () {
  function setOptions(select, items, placeholder, options) {
    const settings = Object.assign({ disabled: false, retainSelection: false }, options);
    const previousValue = settings.retainSelection ? select.value : '';
    select.innerHTML = '';
    if (placeholder !== undefined && placeholder !== null) {
      const placeholderOption = document.createElement('option');
      placeholderOption.value = '';
      placeholderOption.textContent = placeholder;
      select.appendChild(placeholderOption);
    }
    let selectionRestored = false;
    items.forEach((item) => {
      const option = document.createElement('option');
      option.value = String(item.value);
      option.textContent = item.label;
      if (settings.retainSelection && previousValue && String(item.value) === previousValue) {
        option.selected = true;
        selectionRestored = true;
      }
      select.appendChild(option);
    });
    if (settings.retainSelection && previousValue && !selectionRestored && !settings.disabled) {
      select.value = previousValue;
    } else if (!settings.retainSelection) {
      select.value = '';
    }
    select.disabled = settings.disabled;
  }

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

  function handleUbicacionSelects() {
    const form = document.querySelector('form[data-servicios-url][data-oficinas-url]');
    const hospitalSelect = document.getElementById('hospital_id');
    const servicioSelect = document.getElementById('servicio_id');
    const oficinaSelect = document.getElementById('oficina_id');
    if (!form || !hospitalSelect || !servicioSelect || !oficinaSelect) {
      return;
    }

    const serviciosUrl = form.getAttribute('data-servicios-url');
    const oficinasUrl = form.getAttribute('data-oficinas-url');
    let serviciosRequestId = 0;
    let oficinasRequestId = 0;

    function resetServicios(defaultLabel) {
      setOptions(
        servicioSelect,
        [],
        defaultLabel || servicioSelect.dataset.defaultLabel || 'Seleccione un hospital para ver servicios',
        { disabled: true }
      );
      servicioSelect.dataset.hasInitial = '0';
      resetOficinas();
    }

    function resetOficinas(defaultLabel) {
      setOptions(
        oficinaSelect,
        [],
        defaultLabel || oficinaSelect.dataset.defaultLabel || 'Seleccione un servicio para ver oficinas',
        { disabled: true }
      );
      oficinaSelect.dataset.hasInitial = '0';
    }

    function fetchServicios(hospitalId) {
      serviciosRequestId += 1;
      const currentRequest = serviciosRequestId;
      setOptions(
        servicioSelect,
        [],
        servicioSelect.dataset.loadingLabel || 'Cargando servicios...',
        { disabled: true }
      );
      resetOficinas();
      const url = `${serviciosUrl}?${new URLSearchParams({ hospital_id: hospitalId })}`;
      fetch(url, { credentials: 'same-origin' })
        .then((response) => {
          if (!response.ok) {
            throw new Error('Error de red');
          }
          return response.json();
        })
        .then((data) => {
          if (currentRequest !== serviciosRequestId) {
            return;
          }
          if (!Array.isArray(data) || data.length === 0) {
            setOptions(
              servicioSelect,
              [],
              servicioSelect.dataset.emptyLabel || 'No hay servicios disponibles',
              { disabled: true }
            );
            servicioSelect.dataset.hasInitial = '0';
            return;
          }
          const items = data.map((servicio) => ({ value: servicio.id, label: servicio.nombre }));
          setOptions(
            servicioSelect,
            items,
            servicioSelect.dataset.placeholder || 'Seleccione un servicio',
            { disabled: false }
          );
          servicioSelect.dataset.hasInitial = '1';
        })
        .catch(() => {
          if (currentRequest !== serviciosRequestId) {
            return;
          }
          setOptions(
            servicioSelect,
            [],
            servicioSelect.dataset.errorLabel || 'Error al cargar servicios',
            { disabled: true }
          );
          servicioSelect.dataset.hasInitial = '0';
        });
    }

    function fetchOficinas(servicioId) {
      oficinasRequestId += 1;
      const currentRequest = oficinasRequestId;
      setOptions(
        oficinaSelect,
        [],
        oficinaSelect.dataset.loadingLabel || 'Cargando oficinas...',
        { disabled: true }
      );
      const url = `${oficinasUrl}?${new URLSearchParams({ servicio_id: servicioId })}`;
      fetch(url, { credentials: 'same-origin' })
        .then((response) => {
          if (!response.ok) {
            throw new Error('Error de red');
          }
          return response.json();
        })
        .then((data) => {
          if (currentRequest !== oficinasRequestId) {
            return;
          }
          if (!Array.isArray(data) || data.length === 0) {
            setOptions(
              oficinaSelect,
              [],
              oficinaSelect.dataset.emptyLabel || 'No hay oficinas disponibles',
              { disabled: true }
            );
            oficinaSelect.dataset.hasInitial = '0';
            return;
          }
          const items = data.map((oficina) => ({ value: oficina.id, label: oficina.nombre }));
          setOptions(
            oficinaSelect,
            items,
            oficinaSelect.dataset.placeholder || 'Seleccione una oficina',
            { disabled: false }
          );
          oficinaSelect.dataset.hasInitial = '1';
        })
        .catch(() => {
          if (currentRequest !== oficinasRequestId) {
            return;
          }
          setOptions(
            oficinaSelect,
            [],
            oficinaSelect.dataset.errorLabel || 'Error al cargar oficinas',
            { disabled: true }
          );
          oficinaSelect.dataset.hasInitial = '0';
        });
    }

    if (!hospitalSelect.value) {
      resetServicios();
    }
    if (hospitalSelect.value && servicioSelect.dataset.hasInitial !== '1') {
      resetOficinas();
    }
    if (servicioSelect.value && oficinaSelect.dataset.hasInitial !== '1') {
      resetOficinas();
    }

    hospitalSelect.addEventListener('change', () => {
      const hospitalId = hospitalSelect.value;
      if (!hospitalId) {
        resetServicios();
        return;
      }
      fetchServicios(hospitalId);
    });

    servicioSelect.addEventListener('change', () => {
      const servicioId = servicioSelect.value;
      if (!servicioId) {
        resetOficinas();
        return;
      }
      fetchOficinas(servicioId);
    });
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
    handleUbicacionSelects();
    handleSerialToggle();
    handleNuevoEquipoToggle();
  });
})();
