(function () {
  if (typeof window.jQuery === 'undefined' || typeof window.jQuery.fn.select2 === 'undefined') {
    return;
  }

  const $ = window.jQuery;

  function getCsrfToken() {
    const meta = document.querySelector('meta[name="csrf-token"]');
    return meta ? meta.getAttribute('content') : null;
  }

  function normaliseOption(option) {
    if (!option) {
      return { id: '', text: '' };
    }
    const id = option.id ?? option.value ?? '';
    const text = option.text ?? option.label ?? option.nombre ?? `${id}`;
    return { id: String(id), text: String(text) };
  }

  function parseInitialOptions(element) {
    const raw = element.dataset.initialOptions;
    if (!raw) {
      return [];
    }
    try {
      const parsed = JSON.parse(raw);
      if (Array.isArray(parsed)) {
        return parsed.map((item) => normaliseOption(item));
      }
    } catch (error) {
      console.warn('No se pudo parsear opciones iniciales de equipo', error);
    }
    return [];
  }

  function updateHiddenValue(selectElement, hidden, multiple) {
    const value = $(selectElement).val();
    if (multiple) {
      if (Array.isArray(value)) {
        hidden.value = value.join(',');
      } else {
        hidden.value = '';
      }
    } else {
      hidden.value = value ? String(value) : '';
    }
  }

  $(function initialiseEquipoSelects() {
    const csrfToken = getCsrfToken();
    document.querySelectorAll('[data-equipo-select]').forEach((element) => {
      const hiddenSelector = element.dataset.target || '';
      const hidden = hiddenSelector ? document.querySelector(hiddenSelector) : null;
      if (!hidden) {
        console.warn('Campo oculto no encontrado para selector de equipos', element);
        return;
      }

      const multiple = element.dataset.multiple === 'true';
      const allowClear = element.dataset.allowClear === 'true';
      const placeholder = element.dataset.placeholder || 'Buscar equipo…';
      const minChars = Number.parseInt(element.dataset.minChars || '1', 10) || 1;
      const endpoint = element.dataset.endpoint || '/api/equipos/search';
      const initialOptions = parseInitialOptions(element);

      const ajaxConfig = {
        url: endpoint,
        dataType: 'json',
        delay: 250,
        headers: csrfToken ? { 'X-CSRFToken': csrfToken } : {},
        data(params) {
          return {
            q: params.term || '',
            page: params.page || 1,
            per_page: element.dataset.pageSize || undefined,
          };
        },
        processResults(data) {
          const payload = data && typeof data === 'object' ? data : {};
          const results = Array.isArray(payload)
            ? payload
            : payload.results || payload.items || [];
          const mapped = results.map((item) => normaliseOption(item));
          const pagination = payload.pagination || {};
          return {
            results: mapped,
            pagination: { more: Boolean(pagination.more) },
          };
        },
      };

      $(element).select2({
        theme: 'bootstrap-5',
        placeholder,
        allowClear,
        multiple,
        minimumInputLength: minChars,
        width: '100%',
        ajax: ajaxConfig,
      });

      if (initialOptions.length) {
        const values = [];
        initialOptions.forEach((option) => {
          const opt = new Option(option.text, option.id, true, true);
          element.add(opt);
          values.push(option.id);
        });
        $(element).val(multiple ? values : values[0] || null).trigger('change');
      } else if (hidden.value) {
        const currentValues = multiple ? hidden.value.split(',') : [hidden.value];
        currentValues
          .filter((value) => value)
          .forEach((value) => {
            const opt = new Option(value, value, true, true);
            element.add(opt);
          });
        $(element).val(multiple ? currentValues : currentValues[0] || null).trigger('change');
      }

      updateHiddenValue(element, hidden, multiple);

      $(element).on('change', () => updateHiddenValue(element, hidden, multiple));

      const form = element.closest('form');
      if (form) {
        form.addEventListener('reset', () => {
          $(element).val(null).trigger('change');
          hidden.value = '';
        });
      }
    });
  });
})();
