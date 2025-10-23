(function () {
  if (typeof window.jQuery === 'undefined' || typeof window.jQuery.fn.select2 === 'undefined') {
    return;
  }

  const $ = window.jQuery;

  function getDependencyValue(element) {
    if (!element) {
      return '';
    }
    if (element.tomselect) {
      const value = element.tomselect.getValue();
      if (Array.isArray(value)) {
        return value[0] || '';
      }
      return value;
    }
    if (element.type === 'checkbox' || element.type === 'radio') {
      return element.checked ? element.value : '';
    }
    return element.value ?? '';
  }

  function parseExtraParams(element) {
    const raw = element.dataset.extraParams;
    if (!raw) {
      return [];
    }
    try {
      const parsed = JSON.parse(raw);
      if (!Array.isArray(parsed)) {
        return [];
      }
      return parsed
        .map((item) => {
          if (!item || !item.field || !item.param) {
            return null;
          }
          const target = document.getElementById(item.field);
          if (!target) {
            return null;
          }
          return { param: item.param, element: target };
        })
        .filter(Boolean);
    } catch (error) {
      console.warn('No se pudieron interpretar parámetros extra para selector de equipos', error);
      return [];
    }
  }

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
      const dependencyField = element.dataset.dependentField || '';
      const dependencyElement = dependencyField
        ? document.getElementById(dependencyField)
        : null;
      const dependencyParam = element.dataset.dependentParam || 'hospital_id';
      const dependencyMessage = element.dataset.dependentMessage || '';
      const extraParams = parseExtraParams(element);

      const perPage = Number.parseInt(element.dataset.pageSize || '', 10);
      const effectivePlaceholder =
        dependencyElement && !getDependencyValue(dependencyElement) && dependencyMessage
          ? dependencyMessage
          : placeholder;

      const ajaxConfig = {
        url: endpoint,
        dataType: 'json',
        delay: 250,
        headers: csrfToken ? { 'X-CSRFToken': csrfToken } : {},
        data(params) {
          if (dependencyElement && !getDependencyValue(dependencyElement)) {
            return false;
          }
          return {
            q: params.term || '',
            page: params.page || 1,
            per_page: Number.isFinite(perPage) && perPage > 0 ? perPage : undefined,
            ...(dependencyElement
              ? { [dependencyParam]: getDependencyValue(dependencyElement) }
              : {}),
            ...extraParams.reduce((acc, item) => {
              const value = getDependencyValue(item.element);
              if (value) {
                acc[item.param] = value;
              }
              return acc;
            }, {}),
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
        placeholder: effectivePlaceholder,
        allowClear,
        multiple,
        minimumInputLength: minChars,
        width: '100%',
        ajax: ajaxConfig,
      });

      const selectInstance = $(element).data('select2');

      function resetSelection() {
        $(element).val(null).trigger('change');
        hidden.value = '';
      }

      function updateDependencyState() {
        if (!dependencyElement || !selectInstance) {
          return;
        }
        const hasValue = Boolean(getDependencyValue(dependencyElement));
        $(element).prop('disabled', !hasValue);
        if (!hasValue) {
          resetSelection();
        }
        const selection = selectInstance.$selection || selectInstance.$container;
        if (selection && selection.find) {
          const placeholderNode = selection.find('.select2-selection__placeholder');
          if (placeholderNode.length) {
            placeholderNode.text(hasValue ? placeholder : dependencyMessage || placeholder);
          }
        }
      }

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

      if (dependencyElement) {
        dependencyElement.addEventListener('change', () => {
          resetSelection();
          updateDependencyState();
        });
        updateDependencyState();
      }

      if (extraParams.length) {
        extraParams.forEach(({ element: paramElement }) => {
          paramElement.addEventListener('change', () => {
            resetSelection();
          });
        });
      }
    });
  });
})();
