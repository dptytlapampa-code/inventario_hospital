(function () {
  if (typeof TomSelect === 'undefined') {
    return;
  }

  const registry = new Map();

  function debounce(fn, delay = 250) {
    let timeoutId;
    return function debounced(...args) {
      window.clearTimeout(timeoutId);
      timeoutId = window.setTimeout(() => fn.apply(this, args), delay);
    };
  }

  function parseJsonAttribute(value, fallback) {
    if (!value) {
      return fallback;
    }
    try {
      return JSON.parse(value);
    } catch (error) {
      console.warn('No se pudo parsear el atributo de lookup', error);
      return fallback;
    }
  }

  function normaliseOption(option) {
    if (!option) {
      return { id: '', label: '' };
    }
    const id = option.id ?? option.value ?? '';
    const label = option.label ?? option.text ?? option.name ?? `${id}`;
    return { id: String(id), label: String(label) };
  }

  class LookupModal {
    constructor() {
      this.element = document.getElementById('lookupModal');
      this.modal = this.element ? new bootstrap.Modal(this.element) : null;
      this.title = this.element ? this.element.querySelector('[data-lookup-modal-title]') : null;
      this.searchInput = this.element ? this.element.querySelector('[data-lookup-modal-search]') : null;
      this.results = this.element ? this.element.querySelector('[data-lookup-modal-results]') : null;
      this.summary = this.element ? this.element.querySelector('[data-lookup-modal-summary]') : null;
      this.prevButton = this.element ? this.element.querySelector('[data-lookup-modal-prev]') : null;
      this.nextButton = this.element ? this.element.querySelector('[data-lookup-modal-next]') : null;
      this.control = null;
      this.loading = false;
      this.params = {};
      this.currentPage = 1;
      this.total = 0;
      this.pages = 0;
      this.currentQuery = '';

      if (!this.element) {
        return;
      }

      const debouncedSearch = debounce(() => {
        const query = this.searchInput ? this.searchInput.value.trim() : '';
        this.load(1, query);
      }, 300);

      this.searchInput && this.searchInput.addEventListener('input', debouncedSearch);
      this.prevButton &&
        this.prevButton.addEventListener('click', () => {
          if (this.currentPage > 1) {
            this.load(this.currentPage - 1, this.currentQuery);
          }
        });
      this.nextButton &&
        this.nextButton.addEventListener('click', () => {
          if (this.currentPage < this.pages) {
            this.load(this.currentPage + 1, this.currentQuery);
          }
        });

      this.results &&
        this.results.addEventListener('click', (event) => {
          const button = event.target.closest('[data-value]');
          if (!button || !this.control) {
            return;
          }
          const option = normaliseOption({ id: button.dataset.value ?? '', label: button.dataset.text ?? button.textContent });
          this.control.applySelection(option);
          this.hide();
        });
    }

    open(control, params) {
      if (!this.modal || !control) {
        return;
      }
      this.control = control;
      this.params = params || {};
      this.currentPage = 1;
      this.currentQuery = '';
      this.total = 0;
      this.pages = 0;
      if (this.title) {
        this.title.textContent = control.label;
      }
      if (this.searchInput) {
        this.searchInput.value = '';
        this.searchInput.placeholder = `Buscar ${control.label.toLowerCase()}…`;
      }
      this.renderItems([]);
      this.modal.show();
      this.load(1, '');
    }

    hide() {
      if (this.modal) {
        this.modal.hide();
      }
    }

    async load(page, query) {
      if (!this.control || this.loading) {
        return;
      }
      this.loading = true;
      this.currentQuery = query;
      if (this.summary) {
        this.summary.textContent = 'Cargando…';
      }
      if (this.results) {
        this.results.innerHTML = '';
      }
      try {
        const data = await this.control.request(query, page, this.params);
        this.currentPage = data.page || page;
        this.pages = data.pages || 0;
        this.total = data.total || 0;
        this.renderItems(data.items || []);
      } catch (error) {
        console.error(error);
        this.renderItems([]);
        if (this.summary) {
          this.summary.textContent = 'No se pudieron cargar los datos.';
        }
      } finally {
        this.loading = false;
      }
    }

    renderItems(items) {
      if (!this.results) {
        return;
      }
      this.results.innerHTML = '';
      if (this.control && this.control.allowEmpty) {
        const emptyButton = document.createElement('button');
        emptyButton.type = 'button';
        emptyButton.className = 'list-group-item list-group-item-action';
        emptyButton.dataset.value = '';
        emptyButton.dataset.text = this.control.emptyLabel;
        emptyButton.textContent = this.control.emptyLabel;
        this.results.appendChild(emptyButton);
      }
      if (!items.length) {
        const empty = document.createElement('div');
        empty.className = 'list-group-item text-muted small';
        empty.textContent = 'Sin resultados disponibles.';
        this.results.appendChild(empty);
      } else {
        items.forEach((item) => {
          const option = normaliseOption(item);
          const button = document.createElement('button');
          button.type = 'button';
          button.className = 'list-group-item list-group-item-action';
          button.dataset.value = option.id;
          button.dataset.text = option.label;
          button.textContent = option.label;
          this.results.appendChild(button);
        });
      }
      if (this.summary) {
        if (this.total) {
          const totalPages = this.pages || 1;
          this.summary.textContent = `Mostrando página ${this.currentPage} de ${totalPages}. Total: ${this.total}`;
        } else {
          this.summary.textContent = 'Sin registros disponibles.';
        }
      }
      if (this.prevButton) {
        this.prevButton.disabled = !this.control || this.currentPage <= 1;
      }
      if (this.nextButton) {
        this.nextButton.disabled = !this.control || (this.pages && this.currentPage >= this.pages);
      }
    }
  }

  const lookupModal = new LookupModal();

  class LookupControl {
    constructor(input) {
      this.input = input;
      this.hidden = document.getElementById(input.dataset.lookupHidden || '');
      this.container = input.closest('.lookup-control');
      this.showAllButton = this.container ? this.container.querySelector('[data-lookup-show-all]') : null;
      this.clearButton = this.container ? this.container.querySelector('[data-lookup-clear]') : null;
      this.paramsMapping = parseJsonAttribute(input.dataset.lookupParams, {});
      this.requiredParams = new Set(parseJsonAttribute(input.dataset.lookupRequired, []));
      this.resetTargets = parseJsonAttribute(input.dataset.lookupReset, []);
      this.requiresMessage = input.dataset.lookupRequiredMessage || 'Complete los datos previos.';
      this.allowEmpty = input.dataset.lookupAllowEmpty === 'true';
      this.emptyLabel = input.dataset.lookupEmptyLabel || 'Sin definir';
      this.minChars = parseInt(input.dataset.lookupMinChars || '2', 10);
      this.label = input.dataset.lookupLabel || input.placeholder || input.name || 'Seleccionar opción';
      this.endpoint = input.dataset.lookupUrl;
      this.optionCache = new Map();
      this.selectedOption = null;
      this.paramElements = new Map();

      this.setupTomSelect();
      this.registerDependencies();
      this.bindButtons();
      this.updateDisabledState();
      registry.set(this.input.id, this);
    }

    setupTomSelect() {
      const placeholder = this.input.getAttribute('placeholder') || this.label;
      const initialId = this.hidden ? this.hidden.value : '';
      const initialLabel = this.input.value || '';
      const self = this;

      this.tomselect = new TomSelect(this.input, {
        valueField: 'id',
        labelField: 'label',
        searchField: ['label'],
        maxItems: 1,
        create: false,
        persist: false,
        preload: false,
        placeholder,
        allowEmptyOption: this.allowEmpty,
        plugins: { clear_button: { title: 'Limpiar selección' } },
        loadThrottle: 250,
        shouldLoad(query) {
          return query.length >= self.minChars;
        },
        load(query, callback) {
          const state = self.collectParams();
          if (!state.ok) {
            callback();
            return;
          }
          self.request(query, 1, state.params)
            .then((data) => {
              const items = data.items || [];
              self.registerOptions(items);
              callback(items);
            })
            .catch((error) => {
              console.error(error);
              callback();
            });
        },
      });

      this.tomselect.on('item_add', (value) => {
        const option = this.optionCache.get(value) || normaliseOption(this.tomselect.options[value]);
        this.applySelection(option, { fromTomSelect: true });
      });

      this.tomselect.on('item_remove', () => {
        this.reset({ notify: true, fromTomSelect: true });
      });

      this.tomselect.on('type', (query) => {
        if (!query) {
          this.clearHidden();
        }
      });

      if (this.allowEmpty) {
        const emptyOption = { id: '', label: this.emptyLabel };
        this.registerOptions([emptyOption]);
        this.tomselect.addOption(emptyOption);
      }

      if (initialId && initialLabel) {
        const option = { id: String(initialId), label: initialLabel };
        this.registerOptions([option]);
        this.tomselect.addOption(option);
        this.tomselect.addItem(option.id, true);
        this.selectedOption = option;
      } else if (!initialId && initialLabel) {
        // Ensure plain text is preserved when there is no identifier yet
        this.tomselect.setTextboxValue(initialLabel);
      }
    }

    registerDependencies() {
      Object.entries(this.paramsMapping || {}).forEach(([param, elementId]) => {
        if (!param || !elementId) {
          return;
        }
        const element = document.getElementById(elementId);
        if (!element) {
          return;
        }
        this.paramElements.set(param, element);
        element.addEventListener('change', () => {
          this.updateDisabledState();
          this.reset();
        });
      });
    }

    bindButtons() {
      this.showAllButton &&
        this.showAllButton.addEventListener('click', () => {
          const state = this.collectParams();
          if (!state.ok) {
            this.showAllButton?.setAttribute('aria-live', 'polite');
            this.showAllButton?.setAttribute('data-lookup-error', state.message || this.requiresMessage);
            this.showMessage(state.message || this.requiresMessage);
            return;
          }
          lookupModal.open(this, state.params);
        });

      this.clearButton &&
        this.clearButton.addEventListener('click', () => {
          this.reset();
        });
    }

    registerOptions(items) {
      (items || []).forEach((item) => {
        const option = normaliseOption(item);
        this.optionCache.set(option.id, option);
      });
    }

    updateDisabledState() {
      const missing = Array.from(this.requiredParams).some((param) => {
        const value = this.getParamValue(param);
        return value === undefined || value === null || value === '';
      });
      if (missing) {
        this.tomselect.disable();
        this.showAllButton && this.showAllButton.setAttribute('disabled', 'disabled');
      } else {
        this.tomselect.enable();
        this.showAllButton && this.showAllButton.removeAttribute('disabled');
      }
    }

    getParamValue(param) {
      const element = this.paramElements.get(param);
      if (!element) {
        return '';
      }
      if (element.tomselect) {
        const value = element.tomselect.getValue();
        return Array.isArray(value) ? value[0] || '' : value;
      }
      return element.value;
    }

    collectParams() {
      const params = {};
      for (const [param, element] of this.paramElements.entries()) {
        const value = this.getParamValue(param);
        if (!value) {
          if (this.requiredParams.has(param)) {
            return { ok: false, message: this.requiresMessage };
          }
          continue;
        }
        params[param] = value;
      }
      return { ok: true, params };
    }

    async request(query, page = 1, params = {}) {
      if (!this.endpoint) {
        throw new Error('No se configuró el endpoint de búsqueda.');
      }
      const url = new URL(this.endpoint, window.location.origin);
      url.searchParams.set('q', query || '');
      url.searchParams.set('page', page);
      Object.entries(params || {}).forEach(([key, value]) => {
        if (value !== undefined && value !== null && value !== '') {
          url.searchParams.set(key, value);
        }
      });
      const response = await fetch(url, { credentials: 'include' });
      const data = await response.json();
      if (!response.ok) {
        const message = data && data.message ? data.message : 'No se pudo obtener la información.';
        throw new Error(message);
      }
      return data;
    }

    applySelection(option, { fromTomSelect = false } = {}) {
      const value = option ? option.id : '';
      const label = option ? option.label : '';
      this.selectedOption = option && value !== undefined ? option : null;

      if (this.allowEmpty && value === '') {
        this.clearHidden();
        this.tomselect.clear(true);
        if (!fromTomSelect) {
          this.tomselect.addItem('', true);
        }
        if (this.selectedOption) {
          this.tomselect.setTextboxValue(this.emptyLabel);
        }
        this.resetDependents();
        return;
      }

      if (!fromTomSelect) {
        this.tomselect.addOption(option);
        this.tomselect.setValue(value, true);
      }

      if (this.hidden) {
        this.hidden.value = value;
        this.hidden.dispatchEvent(new Event('change', { bubbles: true }));
      }

      if (label) {
        this.tomselect.setTextboxValue(label);
      }

      this.resetDependents();
    }

    clearHidden() {
      if (this.hidden) {
        this.hidden.value = '';
        this.hidden.dispatchEvent(new Event('change', { bubbles: true }));
      }
    }

    reset({ notify = true, fromTomSelect = false } = {}) {
      this.selectedOption = null;
      if (!fromTomSelect) {
        this.tomselect.clear(true);
        if (this.allowEmpty) {
          this.tomselect.setTextboxValue(this.emptyLabel);
        } else {
          this.tomselect.setTextboxValue('');
        }
      }
      this.clearHidden();
      if (notify) {
        this.resetDependents();
      }
    }

    resetDependents() {
      this.resetTargets.forEach((targetId) => {
        const lookup = registry.get(targetId);
        if (lookup) {
          lookup.reset();
          lookup.updateDisabledState();
        } else {
          const element = document.getElementById(targetId);
          if (element) {
            element.value = '';
            element.dispatchEvent(new Event('change', { bubbles: true }));
          }
        }
      });
    }

    showMessage(message) {
      if (!message) {
        return;
      }
      this.tomselect.clearOptions();
      this.tomselect.dropdown_content.innerHTML = `<div class="px-3 py-2 text-muted">${message}</div>`;
      this.tomselect.open();
    }

    syncToForm() {
      if (this.selectedOption && this.selectedOption.label) {
        this.input.value = this.selectedOption.label;
      } else if (!this.allowEmpty) {
        this.input.value = '';
      }
    }
  }

  document.addEventListener('DOMContentLoaded', () => {
    document.querySelectorAll('[data-lookup="true"]').forEach((input) => {
      if (!input.id) {
        console.warn('El campo de lookup requiere un id único', input);
        return;
      }
      if (!input.dataset.lookupUrl) {
        console.warn('Falta data-lookup-url para el campo', input);
        return;
      }
      new LookupControl(input);
    });
  });

  document.addEventListener('submit', (event) => {
    const form = event.target;
    if (!(form instanceof HTMLFormElement)) {
      return;
    }
    registry.forEach((control) => {
      if (form.contains(control.input)) {
        control.syncToForm();
      }
    });
  });
})();
