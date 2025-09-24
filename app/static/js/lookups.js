(function () {
  const registry = new Map();

  function debounce(fn, delay = 300) {
    let timeoutId;
    return function (...args) {
      clearTimeout(timeoutId);
      timeoutId = setTimeout(() => fn.apply(this, args), delay);
    };
  }

  function parseJsonAttribute(value, fallback) {
    if (!value) {
      return fallback;
    }
    try {
      return JSON.parse(value);
    } catch (error) {
      console.warn('No se pudo parsear el atributo de búsqueda', error);
      return fallback;
    }
  }

  class LookupModal {
    constructor() {
      this.element = document.getElementById('lookupModal');
      if (!this.element || typeof bootstrap === 'undefined') {
        this.modal = null;
        return;
      }
      this.modal = new bootstrap.Modal(this.element);
      this.title = this.element.querySelector('[data-lookup-modal-title]');
      this.searchInput = this.element.querySelector('[data-lookup-modal-search]');
      this.results = this.element.querySelector('[data-lookup-modal-results]');
      this.summary = this.element.querySelector('[data-lookup-modal-summary]');
      this.prevButton = this.element.querySelector('[data-lookup-modal-prev]');
      this.nextButton = this.element.querySelector('[data-lookup-modal-next]');
      this.loading = false;
      this.control = null;
      this.params = {};
      this.currentPage = 1;
      this.currentQuery = '';
      this.total = 0;
      this.pages = 0;

      const debouncedSearch = debounce(() => {
        this.load(1, this.searchInput ? this.searchInput.value.trim() : '');
      }, 300);
      this.searchInput && this.searchInput.addEventListener('input', debouncedSearch);

      this.prevButton && this.prevButton.addEventListener('click', () => {
        if (this.currentPage > 1) {
          this.load(this.currentPage - 1, this.currentQuery);
        }
      });
      this.nextButton && this.nextButton.addEventListener('click', () => {
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
          this.control.selectOption({ id: button.dataset.value, text: button.dataset.text || button.textContent.trim() });
          this.hide();
        });
    }

    open(control, params) {
      if (!this.modal || !control) {
        return;
      }
      this.control = control;
      this.params = params || {};
      this.currentQuery = '';
      this.currentPage = 1;
      this.total = 0;
      this.pages = 0;
      if (this.title) {
        const label = control.input.getAttribute('aria-label') || control.input.placeholder || control.input.name || 'Seleccionar opción';
        this.title.textContent = label;
      }
      if (this.searchInput) {
        this.searchInput.value = '';
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
      if (this.summary) {
        this.summary.textContent = 'Cargando…';
      }
      if (this.results) {
        this.results.innerHTML = '';
      }
      try {
        const data = await this.control.request(query, page, this.params);
        this.currentQuery = query;
        this.currentPage = data.page || page;
        this.pages = data.pages || 0;
        this.total = data.total || 0;
        this.renderItems(data.items || []);
      } catch (error) {
        this.renderItems([]);
        if (this.summary) {
          this.summary.textContent = error && error.message ? error.message : 'No se pudieron obtener los datos.';
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
      const control = this.control;
      if (control && control.allowEmpty) {
        const emptyOption = document.createElement('button');
        emptyOption.type = 'button';
        emptyOption.className = 'list-group-item list-group-item-action';
        emptyOption.dataset.value = '';
        emptyOption.dataset.text = control.emptyLabel;
        emptyOption.textContent = control.emptyLabel;
        this.results.appendChild(emptyOption);
      }
      if (!items.length) {
        const empty = document.createElement('div');
        empty.className = 'list-group-item text-muted small';
        empty.textContent = 'Sin resultados disponibles.';
        this.results.appendChild(empty);
      } else {
        items.forEach((item) => {
          const button = document.createElement('button');
          button.type = 'button';
          button.className = 'list-group-item list-group-item-action';
          button.dataset.value = item.id ?? '';
          button.dataset.text = item.label || item.text || '';
          button.textContent = item.label || item.text || '';
          this.results.appendChild(button);
        });
      }
      if (this.summary) {
        if (this.total) {
          this.summary.textContent = `Mostrando página ${this.currentPage} de ${this.pages || 1}. Total: ${this.total}`;
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
      this.results = this.container ? this.container.querySelector('[data-lookup-results]') : null;
      this.clearButton = this.container ? this.container.querySelector('[data-lookup-clear]') : null;
      this.showAllButton = this.container ? this.container.querySelector('[data-lookup-show-all]') : null;
      this.params = parseJsonAttribute(input.dataset.lookupParams, {});
      this.requiredParams = new Set(parseJsonAttribute(input.dataset.lookupRequired, []));
      this.resetTargets = parseJsonAttribute(input.dataset.lookupReset, []);
      this.requiredMessage = input.dataset.lookupRequiredMessage || null;
      this.allowEmpty = input.dataset.lookupAllowEmpty === 'true';
      this.emptyLabel = input.dataset.lookupEmptyLabel || 'Sin definir';
      this.page = 1;
      this.currentQuery = '';
      this.loading = false;
      this.nextPage = null;
      this.total = 0;
      this.pages = 0;
      this.paramElements = new Map();
      this.debouncedSearch = debounce((value) => this.search(value), 300);

      registry.set(this.input.id, this);
      this.registerDependencies();
      this.bindEvents();
    }

    registerDependencies() {
      Object.entries(this.params || {}).forEach(([param, elementId]) => {
        if (!elementId) {
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
      this.updateDisabledState();
    }

    bindEvents() {
      this.input.addEventListener('input', () => {
        const value = this.input.value.trim();
        if (!value) {
          this.reset();
          return;
        }
        if (this.hidden) {
          this.hidden.value = '';
        }
        this.debouncedSearch(value);
      });

      this.input.addEventListener('focus', () => {
        if (this.results && this.results.children.length) {
          this.results.classList.remove('d-none');
        }
      });

      this.clearButton &&
        this.clearButton.addEventListener('click', () => {
          this.reset();
        });

      this.showAllButton &&
        this.showAllButton.addEventListener('click', () => {
          const state = this.collectParams();
          if (!state.ok) {
            this.showMessage(state.message || 'Complete los datos requeridos.');
            return;
          }
          lookupModal.open(this, state.params);
        });

      document.addEventListener('click', (event) => {
        if (!this.container || this.container.contains(event.target)) {
          return;
        }
        this.hideResults();
      });

      if (this.results) {
        this.results.addEventListener('click', (event) => {
          const button = event.target.closest('[data-value]');
          if (button) {
            this.selectOption({ id: button.dataset.value, text: button.dataset.text || button.textContent.trim() });
            return;
          }
          if (event.target.matches('[data-load-more]')) {
            this.loadMore();
          }
        });
      }
    }

    updateDisabledState() {
      const missing = Array.from(this.requiredParams).some((param) => {
        const value = this.getParamValue(param);
        return value === null || value === undefined || value === '';
      });
      if (missing) {
        this.input.setAttribute('disabled', 'disabled');
        this.showAllButton && this.showAllButton.setAttribute('disabled', 'disabled');
        this.hideResults(true);
      } else {
        this.input.removeAttribute('disabled');
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
            return { ok: false, message: this.requiredMessage || 'Seleccione una opción previa.' };
          }
          continue;
        }
        params[param] = value;
      }
      return { ok: true, params };
    }

    async request(query, page = 1, params = {}) {
      const url = new URL(this.input.dataset.lookupUrl, window.location.origin);
      url.searchParams.set('page', page);
      url.searchParams.set('q', query || '');
      Object.entries(params || {}).forEach(([key, value]) => {
        if (value !== undefined && value !== null && value !== '') {
          url.searchParams.set(key, value);
        }
      });
      const response = await fetch(url, { credentials: 'include' });
      const data = await response.json();
      if (!response.ok) {
        const errorMessage = data && data.message ? data.message : 'No se pudo obtener la información.';
        throw new Error(errorMessage);
      }
      return data;
    }

    async search(query, page = 1, append = false) {
      if (this.loading) {
        return;
      }
      const state = this.collectParams();
      if (!state.ok) {
        this.showMessage(state.message || 'Seleccione una opción válida.');
        return;
      }
      const value = query.trim();
      const effectiveQuery = value || '';
      this.loading = true;
      this.showMessage('Buscando…', append);
      try {
        const data = await this.request(effectiveQuery, page, state.params);
        this.currentQuery = effectiveQuery;
        this.page = data.page || page;
        this.pages = data.pages || 0;
        this.total = data.total || 0;
        this.nextPage = this.pages && this.page < this.pages ? this.page + 1 : null;
        this.renderResults(data.items || [], append);
      } catch (error) {
        this.showMessage(error && error.message ? error.message : 'No se pudo obtener la información.');
      } finally {
        this.loading = false;
      }
    }

    loadMore() {
      if (!this.nextPage) {
        return;
      }
      this.search(this.currentQuery, this.nextPage, true);
    }

    renderResults(items, append) {
      if (!this.results) {
        return;
      }
      if (!append) {
        this.results.innerHTML = '';
        if (this.allowEmpty) {
          const emptyOption = document.createElement('button');
          emptyOption.type = 'button';
          emptyOption.className = 'list-group-item list-group-item-action';
          emptyOption.dataset.value = '';
          emptyOption.dataset.text = this.emptyLabel;
          emptyOption.textContent = this.emptyLabel;
          this.results.appendChild(emptyOption);
        }
      } else {
        const loadMore = this.results.querySelector('[data-load-more]');
        loadMore && loadMore.remove();
      }

      if (!items.length && !append) {
        this.showMessage('Sin resultados coincidentes.');
        return;
      }

      items.forEach((item) => {
        const button = document.createElement('button');
        button.type = 'button';
        button.className = 'list-group-item list-group-item-action';
        button.dataset.value = item.id ?? '';
        button.dataset.text = item.label || item.text || '';
        button.textContent = item.label || item.text || '';
        this.results.appendChild(button);
      });

      if (this.nextPage) {
        const loadMore = document.createElement('button');
        loadMore.type = 'button';
        loadMore.className = 'list-group-item list-group-item-action text-center text-primary fw-semibold';
        loadMore.dataset.loadMore = 'true';
        loadMore.textContent = 'Cargar más';
        this.results.appendChild(loadMore);
      }

      this.results.classList.remove('d-none');
    }

    showMessage(message, append = false) {
      if (!this.results) {
        return;
      }
      if (!append) {
        this.results.innerHTML = '';
      }
      const info = document.createElement('div');
      info.className = 'list-group-item text-muted small';
      info.textContent = message;
      this.results.appendChild(info);
      this.results.classList.remove('d-none');
    }

    hideResults(clear = false) {
      if (!this.results) {
        return;
      }
      if (clear) {
        this.results.innerHTML = '';
      }
      this.results.classList.add('d-none');
    }

    selectOption(item) {
      if (this.allowEmpty && (item.id === '' || item.id === null || item.id === undefined)) {
        this.input.value = this.emptyLabel;
        if (this.hidden) {
          this.hidden.value = '';
          this.hidden.dispatchEvent(new Event('change', { bubbles: true }));
        }
        this.hideResults(true);
        this.resetDependents();
        return;
      }
      this.input.value = item.text;
      if (this.hidden) {
        this.hidden.value = item.id;
        this.hidden.dispatchEvent(new Event('change', { bubbles: true }));
      }
      this.hideResults(true);
      this.resetDependents();
    }

    reset({ notify = true } = {}) {
      this.input.value = '';
      if (this.hidden) {
        this.hidden.value = '';
        this.hidden.dispatchEvent(new Event('change', { bubbles: true }));
      }
      this.currentQuery = '';
      this.page = 1;
      this.nextPage = null;
      this.total = 0;
      this.pages = 0;
      this.hideResults(true);
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
          return;
        }
        const element = document.getElementById(targetId);
        if (element) {
          element.value = '';
        }
      });
    }
  }

  document.addEventListener('DOMContentLoaded', () => {
    document.querySelectorAll('[data-lookup="true"]').forEach((input) => {
      if (!input.id) {
        console.warn('El campo de búsqueda debe tener un id único.');
        return;
      }
      if (!input.dataset.lookupUrl) {
        console.warn('Falta data-lookup-url en el campo', input);
        return;
      }
      new LookupControl(input);
    });
  });
})();
