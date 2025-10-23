(function () {
  function buildUrl(endpoint, params) {
    const url = new URL(endpoint, window.location.origin);
    Object.entries(params).forEach(([key, value]) => {
      if (value !== undefined && value !== null && value !== '') {
        url.searchParams.set(key, value);
      }
    });
    return url;
  }

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
    return element.value;
  }

  function showDropdownMessage(instance, message) {
    if (!instance) return;
    instance.clearOptions();
    instance.renderCache = { item: {}, option: {} };
    instance.dropdown_content.innerHTML = `<div class="px-3 py-2 text-muted">${message}</div>`;
  }

  function updateInsumosTable(instance) {
    const card = document.querySelector('[data-insumos-card]');
    if (!card || !instance) {
      return;
    }
    const body = card.querySelector('tbody');
    if (!body) {
      return;
    }
    const values = instance.getValue();
    const selection = Array.isArray(values) ? values : values ? [values] : [];
    const placeholder = card.querySelector('.insumo-table-placeholder');
    if (!selection.length) {
      body.innerHTML = '';
      card.classList.add('d-none');
      if (placeholder) {
        placeholder.classList.remove('d-none');
      }
      return;
    }
    const rows = selection
      .map((value) => {
        const option = instance.options[value] || {};
        const label = option.text || option.label || value;
        return `
          <tr>
            <td>${label}</td>
            <td style="max-width: 120px;">
              <input type="number" name="insumo_cantidad[${value}]" min="1" value="1" class="form-control form-control-sm" />
            </td>
          </tr>
        `;
      })
      .join('');
    body.innerHTML = rows;
    card.classList.remove('d-none');
    if (placeholder) {
      placeholder.classList.add('d-none');
    }
  }

  function parseExtraParams(select) {
    const raw = select.dataset.extraParams;
    if (!raw) {
      return [];
    }
    try {
      const parsed = JSON.parse(raw);
      return Array.isArray(parsed)
        ? parsed
            .map((item) => {
              if (!item || !item.field || !item.param) {
                return null;
              }
              const element = document.getElementById(item.field);
              if (!element) {
                return null;
              }
              return { param: item.param, element };
            })
            .filter(Boolean)
        : [];
    } catch (error) {
      console.warn('No se pudieron interpretar los parámetros extra para Tom Select', error);
      return [];
    }
  }

  function initTomSelect(select) {
    const endpoint = select.dataset.endpoint;
    if (!endpoint || typeof TomSelect === 'undefined') {
      return;
    }
    const minChars = parseInt(select.dataset.minChars || '1', 10);
    const placeholder = select.dataset.placeholder || select.getAttribute('placeholder') || 'Escriba para buscar…';
    const dependsField = select.dataset.dependentField;
    const dependsMessage = select.dataset.dependentMessage || 'Seleccione un valor para continuar';
    const dependencyElement = dependsField ? document.getElementById(dependsField) : null;
    const dependencyParam = select.dataset.dependentParam || 'servicio_id';
    const allowClear = select.dataset.allowClear === 'true';
    const extraParams = parseExtraParams(select);

    const plugins = {};
    if (select.multiple) {
      plugins.remove_button = { title: 'Quitar' };
    } else if (allowClear) {
      plugins.clear_button = { title: 'Limpiar' };
    }

    const tom = new TomSelect(select, {
      valueField: 'id',
      labelField: 'text',
      searchField: 'text',
      maxOptions: 20,
      create: false,
      persist: false,
      preload: false,
      placeholder,
      plugins,
      shouldLoad(query) {
        return query.length >= minChars;
      },
      load(query, callback) {
        if (dependsField) {
          const dependencyValue = getDependencyValue(dependencyElement);
          if (!dependencyValue) {
            showDropdownMessage(this, dependsMessage);
            callback();
            return;
          }
        }
        const params = { q: query, page: 1 };
        if (dependsField) {
          params[dependencyParam] = getDependencyValue(dependencyElement);
        }
        if (extraParams.length) {
          extraParams.forEach(({ param, element }) => {
            const value = getDependencyValue(element);
            if (value) {
              params[param] = value;
            }
          });
        }
        fetch(buildUrl(endpoint, params), { credentials: 'include' })
          .then((response) => {
            return response.json().then((data) => {
              if (!response.ok) {
                const message = data && data.message ? data.message : 'Sin resultados disponibles';
                showDropdownMessage(tom, message);
                return { items: [] };
              }
              return data;
            });
          })
          .then((data) => {
            callback(data.items || data.results || []);
          })
          .catch(() => {
            callback();
          });
      },
      onInitialize() {
        if (select.dataset.role === 'insumos-selector') {
          updateInsumosTable(this);
        }
      },
      onChange() {
        if (select.dataset.role === 'insumos-selector') {
          updateInsumosTable(this);
        }
      },
    });

    if (dependencyElement) {
      dependencyElement.addEventListener('change', () => {
        tom.clear();
        tom.clearOptions();
        if (select.dataset.role === 'insumos-selector') {
          updateInsumosTable(tom);
        }
        if (getDependencyValue(dependencyElement)) {
          tom.enable();
        } else {
          tom.disable();
        }
      });
      if (!getDependencyValue(dependencyElement)) {
        tom.disable();
      }
    }

    if (extraParams.length) {
      extraParams.forEach(({ element }) => {
        element.addEventListener('change', () => {
          if (dependsField && !getDependencyValue(dependencyElement)) {
            return;
          }
          tom.clearOptions();
        });
      });
    }

    return tom;
  }

  document.addEventListener('DOMContentLoaded', () => {
    const selects = document.querySelectorAll('select[data-control="tom-select"]');
    selects.forEach((select) => initTomSelect(select));
  });
})();
