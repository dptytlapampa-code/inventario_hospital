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
      this.page = 1;
      this.currentQuery = '';
      this.loading = false;
      this.nextPage = null;
      this.debouncedSearch = debounce((value) => this.search(value), 300);

      registry.set(this.input.id, this);
      this.bindEvents();
    }

    bindEvents() {
      this.input.addEventListener('input', () => {
        const value = this.input.value.trim();
        if (!value) {
          this.reset();
          return;
        }
        this.hidden && (this.hidden.value = '');
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
          this.input.value = '...';
          this.search('...');
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
          if (!button) {
            if (event.target.matches('[data-load-more]')) {
              this.loadMore();
            }
            return;
          }
          this.selectOption({ id: button.dataset.value, text: button.dataset.text || button.textContent.trim() });
        });
      }
    }

    buildParams() {
      const params = {};
      for (const [param, elementId] of Object.entries(this.params)) {
        if (!elementId) {
          continue;
        }
        const element = document.getElementById(elementId);
        const value = element ? element.value : '';
        if (!value && this.requiredParams.has(param)) {
          return { ok: false, message: this.requiredMessage || 'Complete los datos requeridos.' };
        }
        if (value) {
          params[param] = value;
        }
      }
      return { ok: true, params };
    }

    async search(query, page = 1, append = false) {
      if (this.loading) {
        return;
      }
      const { ok, params, message } = this.buildParams();
      if (!ok) {
        this.showMessage(message || 'Seleccione una opción previa.');
        return;
      }

      const url = new URL(this.input.dataset.lookupUrl, window.location.origin);
      url.searchParams.set('q', query);
      url.searchParams.set('page', page);
      Object.entries(params || {}).forEach(([key, value]) => {
        url.searchParams.set(key, value);
      });

      this.loading = true;
      this.showMessage('Buscando…', append);

      try {
        const response = await fetch(url, { credentials: 'include' });
        const data = await response.json();
        if (!response.ok) {
          const errorMessage = data && data.message ? data.message : 'Sin resultados disponibles.';
          this.showMessage(errorMessage);
          return;
        }
        this.currentQuery = query;
        this.page = page;
        this.nextPage = data.next ? page + 1 : null;
        this.renderResults(data.results || [], append);
      } catch (error) {
        console.error('Error al buscar opciones', error);
        this.showMessage('No se pudo obtener la información.');
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
      } else {
        const loadMoreButton = this.results.querySelector('[data-load-more]');
        loadMoreButton && loadMoreButton.remove();
      }

      if (!items.length && !append) {
        this.showMessage('Sin resultados coincidentes.');
        return;
      }

      items.forEach((item) => {
        const button = document.createElement('button');
        button.type = 'button';
        button.className = 'list-group-item list-group-item-action';
        button.dataset.value = item.id;
        button.dataset.text = item.text;
        button.textContent = item.text;
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
      this.input.value = item.text;
      if (this.hidden) {
        this.hidden.value = item.id;
      }
      this.hideResults(true);
      this.resetDependents();
    }

    reset({ notify = true } = {}) {
      this.input.value = '';
      if (this.hidden) {
        this.hidden.value = '';
      }
      this.currentQuery = '';
      this.page = 1;
      this.nextPage = null;
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
