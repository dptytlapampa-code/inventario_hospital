(function () {
  function buildUrl(endpoint, params) {
    const url = new URL(endpoint, window.location.origin);
    Object.entries(params || {}).forEach(([key, value]) => {
      if (value !== undefined && value !== null && value !== "") {
        url.searchParams.set(key, value);
      }
    });
    return url;
  }

  function createElement(tag, className, text) {
    const element = document.createElement(tag);
    if (className) {
      element.className = className;
    }
    if (text !== undefined && text !== null) {
      element.textContent = text;
    }
    return element;
  }

  function getCsrfToken() {
    const meta = document.querySelector('meta[name="csrf-token"]');
    return meta ? meta.getAttribute('content') : '';
  }

  function showToast(message, variant = 'success') {
    const container = document.querySelector('[data-toast-container]');
    if (!container || typeof bootstrap === 'undefined' || !message) {
      return;
    }
    const toast = document.createElement('div');
    toast.className = `toast align-items-center text-bg-${variant} border-0`;
    toast.setAttribute('role', 'status');
    toast.setAttribute('aria-live', 'polite');
    toast.setAttribute('aria-atomic', 'true');
    toast.innerHTML = `
      <div class="d-flex">
        <div class="toast-body">${message}</div>
        <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast" aria-label="Cerrar"></button>
      </div>
    `;
    container.appendChild(toast);
    const instance = bootstrap.Toast.getOrCreateInstance(toast, { delay: 4000 });
    toast.addEventListener('hidden.bs.toast', () => {
      toast.remove();
    });
    instance.show();
  }

  function formatDateTime(value) {
    if (!value) {
      return '—';
    }
    const date = new Date(value);
    if (Number.isNaN(date.getTime())) {
      return value;
    }
    return date.toLocaleString('es-AR', {
      day: '2-digit',
      month: '2-digit',
      year: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    });
  }

  function ensureEmptyRow(table) {
    if (!table) {
      return;
    }
    const hasRows = table.querySelector('[data-insumo-row]');
    let emptyRow = table.querySelector('[data-empty-row]');
    if (hasRows) {
      if (emptyRow) {
        emptyRow.remove();
      }
      return;
    }
    const colSpan = parseInt(table.dataset.emptyColspan || '1', 10) || 1;
    if (emptyRow) {
      const cell = emptyRow.querySelector('td');
      if (cell) {
        cell.colSpan = colSpan;
      }
      emptyRow.classList.remove('d-none');
      return;
    }
    const tbody = table.tBodies[0] || table.querySelector('tbody');
    if (!tbody) {
      return;
    }
    emptyRow = document.createElement('tr');
    emptyRow.setAttribute('data-empty-row', '');
    const cell = document.createElement('td');
    cell.className = 'text-muted text-center py-3';
    cell.colSpan = colSpan;
    cell.textContent = 'Sin insumos vinculados.';
    emptyRow.appendChild(cell);
    tbody.appendChild(emptyRow);
  }

  function appendAssociationRow(table, data, canRemove) {
    if (!table || !data || !data.serie) {
      return;
    }
    const tbody = table.tBodies[0] || table.querySelector('tbody');
    if (!tbody) {
      return;
    }
    const row = document.createElement('tr');
    row.setAttribute('data-insumo-row', '');
    row.dataset.serieId = data.serie.id;

    const insumoCell = document.createElement('td');
    insumoCell.textContent = data.insumo && data.insumo.nombre ? data.insumo.nombre : 'Insumo';
    row.appendChild(insumoCell);

    const serieCell = document.createElement('td');
    serieCell.className = 'font-monospace';
    serieCell.textContent = data.serie.nro_serie || '';
    row.appendChild(serieCell);

    const fechaCell = document.createElement('td');
    fechaCell.textContent = formatDateTime(data.fecha_asociacion);
    row.appendChild(fechaCell);

    const usuarioCell = document.createElement('td');
    usuarioCell.textContent = data.asociado_por || '—';
    row.appendChild(usuarioCell);

    if (canRemove) {
      const accionesCell = document.createElement('td');
      accionesCell.className = 'text-end';
      const button = document.createElement('button');
      button.type = 'button';
      button.className = 'btn btn-sm btn-outline-danger';
      button.textContent = 'Quitar';
      button.setAttribute('data-remove-insumo', '');
      accionesCell.appendChild(button);
      row.appendChild(accionesCell);
    }

    const emptyRow = table.querySelector('[data-empty-row]');
    if (emptyRow) {
      emptyRow.remove();
    }
    tbody.prepend(row);
    ensureEmptyRow(table);
  }

  class RemotePanel {
    constructor(root) {
      this.root = root;
      this.endpoint = root.dataset.endpoint;
      this.type = root.dataset.remotePanel || "";
      this.limit = parseInt(root.dataset.limit || "10", 10);
      this.form = root.querySelector("[data-panel-form]") || null;
      this.results = root.querySelector("[data-panel-results]") || null;
      this.summary = root.querySelector("[data-panel-summary]") || null;
      this.prevButton = root.querySelector("[data-panel-prev]") || null;
      this.nextButton = root.querySelector("[data-panel-next]") || null;
      this.resetButtons = Array.from(root.querySelectorAll("[data-panel-reset]"));
      this.filters = Array.from(root.querySelectorAll("[data-filter]"));
      this.paginationContainer = root.querySelector("[data-panel-pagination]") || null;

      this.offset = 0;
      this.total = 0;
      this.loaded = false;
      this.loading = false;

      this.handleShown = this.handleShown.bind(this);
      this.handleSubmit = this.handleSubmit.bind(this);
      this.handlePrev = this.handlePrev.bind(this);
      this.handleNext = this.handleNext.bind(this);
      this.handleReset = this.handleReset.bind(this);

      this.registerEvents();
    }

    registerEvents() {
      if (typeof bootstrap !== "undefined" && this.root.id) {
        this.root.addEventListener("shown.bs.collapse", this.handleShown);
      } else {
        // Fallback if Bootstrap events are not available (non-collapsible scenario)
        this.root.addEventListener("transitionend", this.handleShown, { once: true });
      }

      if (this.form) {
        this.form.addEventListener("submit", this.handleSubmit);
      }

      this.resetButtons.forEach((button) => {
        button.addEventListener("click", this.handleReset);
      });

      this.prevButton && this.prevButton.addEventListener("click", this.handlePrev);
      this.nextButton && this.nextButton.addEventListener("click", this.handleNext);
    }

    handleShown() {
      if (!this.loaded) {
        this.fetchData(0);
      }
    }

    handleSubmit(event) {
      event.preventDefault();
      this.fetchData(0);
    }

    handlePrev() {
      if (this.loading || this.offset <= 0) {
        return;
      }
      const newOffset = Math.max(this.offset - this.limit, 0);
      this.fetchData(newOffset);
    }

    handleNext() {
      if (this.loading || this.offset + this.limit >= this.total) {
        return;
      }
      const newOffset = this.offset + this.limit;
      this.fetchData(newOffset);
    }

    handleReset() {
      this.filters.forEach((field) => {
        if (field.matches("select")) {
          field.selectedIndex = 0;
        } else {
          field.value = "";
        }
      });
      this.fetchData(0);
    }

    collectParams(offset) {
      const params = { limit: this.limit, offset };
      this.filters.forEach((field) => {
        const key = field.dataset.filter;
        if (!key) {
          return;
        }
        if (field.matches("select")) {
          params[key] = field.value;
        } else {
          params[key] = field.value.trim();
        }
      });
      return params;
    }

    showLoadingState() {
      if (!this.results) {
        return;
      }
      this.results.innerHTML = "";
      const message = createElement("div", "text-muted small", "Cargando…");
      this.results.appendChild(message);
      if (this.summary) {
        this.summary.textContent = "Cargando…";
      }
      if (this.prevButton) {
        this.prevButton.disabled = true;
      }
      if (this.nextButton) {
        this.nextButton.disabled = true;
      }
    }

    async fetchData(offset) {
      if (!this.endpoint) {
        return;
      }
      this.loading = true;
      this.showLoadingState();
      try {
        const url = buildUrl(this.endpoint, this.collectParams(offset));
        const response = await fetch(url, { credentials: "include" });
        const data = await response.json();
        if (!response.ok) {
          throw new Error((data && data.message) || "No se pudo obtener la información");
        }
        this.limit = data.limit || this.limit;
        this.offset = data.offset || 0;
        this.total = data.total || 0;
        const items = Array.isArray(data.items) ? data.items : [];
        this.renderItems(items);
        this.updateSummary(items);
        this.updatePagination();
        this.loaded = true;
      } catch (error) {
        this.renderError(error && error.message ? error.message : "No se pudieron obtener los datos");
      } finally {
        this.loading = false;
      }
    }

    renderError(message) {
      if (!this.results) {
        return;
      }
      this.results.innerHTML = "";
      this.results.appendChild(createElement("div", "text-danger small", message));
      if (this.summary) {
        this.summary.textContent = message;
      }
    }

    renderItems(items) {
      if (!this.results) {
        return;
      }
      this.results.innerHTML = "";
      if (!items.length) {
        this.results.appendChild(createElement("div", "text-muted small", "Sin resultados para el período seleccionado."));
        return;
      }
      const list = createElement("div", "list-group");
      items.forEach((item) => {
        if (this.type === "actas") {
          list.appendChild(this.renderActaItem(item));
        } else {
          list.appendChild(this.renderHistorialItem(item));
        }
      });
      this.results.appendChild(list);
    }

    renderHistorialItem(item) {
      const container = createElement("div", "list-group-item");
      const title = createElement("div", "fw-semibold", item.accion || "Registro");
      container.appendChild(title);
      if (item.descripcion) {
        container.appendChild(createElement("div", "", item.descripcion));
      }
      const metaParts = [];
      if (item.fecha_display) {
        metaParts.push(item.fecha_display);
      }
      if (item.usuario) {
        metaParts.push(item.usuario);
      }
      container.appendChild(createElement("div", "text-muted small", metaParts.join(" · ")));
      return container;
    }

    renderActaItem(item) {
      const container = createElement("div", "list-group-item d-flex justify-content-between align-items-center gap-2");
      const info = createElement("div", "fw-semibold");
      const labelParts = [];
      if (item.tipo_label) {
        labelParts.push(item.tipo_label);
      }
      if (item.fecha_display) {
        labelParts.push(item.fecha_display);
      }
      info.textContent = labelParts.join(" - ") || "Acta";
      container.appendChild(info);
      if (item.url) {
        const link = createElement("a", "btn btn-sm btn-outline-secondary", "Ver");
        link.href = item.url;
        link.target = "_blank";
        link.rel = "noopener";
        container.appendChild(link);
      }
      return container;
    }

    updateSummary(items) {
      if (!this.summary) {
        return;
      }
      if (!this.total) {
        this.summary.textContent = "Sin resultados.";
        return;
      }
      const start = this.total ? this.offset + 1 : 0;
      const end = Math.min(this.offset + items.length, this.total);
      this.summary.textContent = `Mostrando ${start}–${end} de ${this.total}`;
    }

    updatePagination() {
      const hasPrev = this.offset > 0;
      const hasNext = this.offset + this.limit < this.total;
      if (this.prevButton) {
        this.prevButton.disabled = !hasPrev;
      }
      if (this.nextButton) {
        this.nextButton.disabled = !hasNext;
      }
      if (this.paginationContainer) {
        this.paginationContainer.classList.toggle("d-none", !this.total);
      }
    }
  }

  document.addEventListener("DOMContentLoaded", () => {
    document.querySelectorAll("[data-remote-panel]").forEach((panel) => {
      new RemotePanel(panel);
    });

    const table = document.querySelector('[data-insumos-table]');
    if (table) {
      ensureEmptyRow(table);
      const canRemove = table.dataset.canRemove === '1';
      const removeUrl = table.dataset.removeUrl;
      if (canRemove && removeUrl) {
        table.addEventListener('click', async (event) => {
          const button = event.target.closest('[data-remove-insumo]');
          if (!button) {
            return;
          }
          const row = button.closest('[data-insumo-row]');
          const serieId = row ? row.dataset.serieId : null;
          if (!row || !serieId) {
            return;
          }
          const originalHtml = button.innerHTML;
          button.disabled = true;
          button.innerHTML = 'Quitando…';
          try {
            const response = await fetch(removeUrl, {
              method: 'POST',
              headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCsrfToken(),
              },
              credentials: 'include',
              body: JSON.stringify({ insumo_serie_id: serieId }),
            });
            const data = await response.json().catch(() => ({}));
            if (!response.ok) {
              throw new Error((data && data.message) || 'No se pudo remover el insumo');
            }
            row.remove();
            ensureEmptyRow(table);
            showToast((data && data.message) || 'Insumo removido', 'success');
          } catch (error) {
            showToast(error && error.message ? error.message : 'No se pudo remover el insumo', 'danger');
          } finally {
            button.disabled = false;
            button.innerHTML = originalHtml;
          }
        });
      }

      const form = document.querySelector('[data-associate-form]');
      if (form) {
        const select = form.querySelector('select[name="nro_serie"]');
        const submitButton = form.querySelector('[data-associate-submit]');
        const errorBox = form.querySelector('[data-associate-error]');
        const modalElement = form.closest('.modal');
        const modalInstance =
          modalElement && typeof bootstrap !== 'undefined'
            ? bootstrap.Modal.getOrCreateInstance(modalElement)
            : null;

        form.addEventListener('submit', async (event) => {
          event.preventDefault();
          if (!select) {
            return;
          }
          const rawValue = select.tomselect ? select.tomselect.getValue() : select.value;
          const nroSerie = Array.isArray(rawValue) ? rawValue[0] : rawValue;
          if (!nroSerie) {
            if (errorBox) {
              errorBox.textContent = 'Seleccione un número de serie disponible.';
              errorBox.classList.remove('d-none');
            }
            return;
          }
          if (errorBox) {
            errorBox.classList.add('d-none');
            errorBox.textContent = '';
          }
          const url = form.dataset.associateUrl;
          if (!url) {
            return;
          }
          const originalLabel = submitButton ? submitButton.textContent : '';
          if (submitButton) {
            submitButton.disabled = true;
            submitButton.textContent = 'Asociando…';
          }
          try {
            const response = await fetch(url, {
              method: 'POST',
              headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCsrfToken(),
              },
              credentials: 'include',
              body: JSON.stringify({ nro_serie: nroSerie }),
            });
            const data = await response.json().catch(() => ({}));
            if (!response.ok) {
              throw new Error((data && data.message) || 'No se pudo asociar el insumo');
            }
            appendAssociationRow(table, data.asociacion || {}, table.dataset.canRemove === '1');
            showToast((data && data.message) || 'Insumo asociado', 'success');
            if (select.tomselect) {
              select.tomselect.clear();
              select.tomselect.focus();
            } else {
              select.value = '';
            }
            if (modalInstance) {
              modalInstance.hide();
            }
          } catch (error) {
            if (errorBox) {
              errorBox.textContent = error && error.message ? error.message : 'No se pudo asociar el insumo';
              errorBox.classList.remove('d-none');
            } else {
              showToast(error && error.message ? error.message : 'No se pudo asociar el insumo', 'danger');
            }
          } finally {
            if (submitButton) {
              submitButton.disabled = false;
              submitButton.textContent = originalLabel || 'Asociar';
            }
          }
        });

        if (modalElement && modalInstance) {
          modalElement.addEventListener('hidden.bs.modal', () => {
            if (errorBox) {
              errorBox.classList.add('d-none');
              errorBox.textContent = '';
            }
            if (select && select.tomselect) {
              select.tomselect.clear();
            } else if (select) {
              select.value = '';
            }
          });
        }
      }
    }
  });
})();
