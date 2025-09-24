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

    const tom = new TomSelect(select, {
      valueField: 'id',
      labelField: 'text',
      searchField: 'text',
      maxOptions: 20,
      create: false,
      persist: false,
      preload: false,
      placeholder,
      plugins: select.multiple
        ? {
            remove_button: { title: 'Quitar' },
          }
        : {},
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
          params.servicio_id = getDependencyValue(dependencyElement);
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
      });
    }

    return tom;
  }

  document.addEventListener('DOMContentLoaded', () => {
    const selects = document.querySelectorAll('select[data-control="tom-select"]');
    selects.forEach((select) => initTomSelect(select));
  });
})();
