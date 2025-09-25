(function () {
  const list = document.querySelector('[data-license-list]');
  if (!list) {
    return;
  }

  const scope = list.dataset.licenseScope || 'mine';
  const POLL_INTERVAL = 60000;
  const POLL_ENDPOINTS = {
    admin: '/api/licencias/admin',
    mine: '/api/licencias/mias',
  };
  const badgeMap = {
    solicitada: 'bg-secondary',
    aprobada: 'bg-success',
    rechazada: 'bg-danger',
    cancelada: 'bg-warning',
  };

  let eventSource = null;
  let pollTimer = null;

  function escapeHtml(value) {
    return String(value ?? '')
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;')
      .replace(/'/g, '&#39;');
  }

  function formatLabel(value) {
    if (!value) {
      return '';
    }
    return value
      .toString()
      .replace(/_/g, ' ')
      .replace(/\b\w/g, (letter) => letter.toUpperCase());
  }

  function formatDateTime(value) {
    if (!value) {
      return '';
    }
    const date = new Date(value);
    if (Number.isNaN(date.getTime())) {
      return '';
    }
    return new Intl.DateTimeFormat('es-AR', {
      dateStyle: 'short',
      timeStyle: 'short',
    }).format(date);
  }

  function toggle(element, hidden) {
    if (!element) {
      return;
    }
    element.classList.toggle('d-none', Boolean(hidden));
    if (hidden) {
      const collapse = element.querySelector('.collapse.show');
      if (collapse && typeof bootstrap !== 'undefined') {
        const instance = bootstrap.Collapse.getInstance(collapse);
        if (instance) {
          instance.hide();
        } else {
          collapse.classList.remove('show');
        }
      }
    }
  }

  function updateStatusCell(row, licencia) {
    const cell = row.querySelector('[data-license-status]');
    if (!cell) {
      return;
    }
    const estado = licencia.estado || '';
    const badgeClass = badgeMap[estado] || 'bg-secondary';
    const label = formatLabel(estado);
    const badge = `<span class="badge ${badgeClass}">${escapeHtml(label)}</span>`;
    let extra = '';
    if (licencia.decidido_por) {
      const decided = licencia.decidido_en ? formatDateTime(licencia.decidido_en) : '';
      const meta = decided
        ? `${escapeHtml(licencia.decidido_por)}, ${escapeHtml(decided)}`
        : escapeHtml(licencia.decidido_por);
      extra = `<div class="small text-muted mt-1">${meta}</div>`;
    }
    cell.innerHTML = `${badge}${extra}`;
  }

  function updateDetailCell(row, licencia) {
    const cell = row.querySelector('[data-license-detail]');
    if (!cell) {
      return;
    }
    let html = `<div class="small text-muted">Motivo</div><div>${escapeHtml(licencia.motivo || '—')}</div>`;
    if (licencia.motivo_rechazo) {
      html += `<div class="small text-muted mt-2">Motivo de rechazo</div><div class="text-danger">${escapeHtml(licencia.motivo_rechazo)}</div>`;
    }
    if (scope === 'mine' && licencia.decidido_por) {
      const decided = licencia.decidido_en ? formatDateTime(licencia.decidido_en) : '';
      const decidedText = decided ? ` el ${escapeHtml(decided)}` : '';
      html += `<div class="small text-muted mt-2">Decidido por ${escapeHtml(licencia.decidido_por)}${decidedText}</div>`;
    }
    cell.innerHTML = html;
  }

  function updateActions(row, estado) {
    const actionsCell = row.querySelector('[data-license-actions]');
    if (!actionsCell) {
      return;
    }
    const approveForm = actionsCell.querySelector('[data-license-approve]');
    const rejectWrapper = actionsCell.querySelector('[data-license-reject]');
    const cancelForm = actionsCell.querySelector('[data-license-cancel]');
    const noActions = actionsCell.querySelector('[data-license-no-actions]');

    if (scope === 'admin') {
      if (estado === 'solicitada') {
        toggle(approveForm, false);
        toggle(rejectWrapper, false);
        toggle(cancelForm, false);
        toggle(noActions, true);
      } else if (estado === 'aprobada') {
        toggle(approveForm, true);
        toggle(rejectWrapper, true);
        toggle(cancelForm, false);
        toggle(noActions, true);
      } else {
        toggle(approveForm, true);
        toggle(rejectWrapper, true);
        toggle(cancelForm, true);
        toggle(noActions, false);
      }
    } else {
      toggle(cancelForm, estado !== 'solicitada');
      toggle(noActions, estado === 'solicitada');
    }
  }

  function updateRow(licencia) {
    const row = list.querySelector(`[data-license-row="${licencia.id}"]`);
    if (!row) {
      return;
    }
    const estado = (licencia.estado || '').toLowerCase();
    updateStatusCell(row, licencia);
    updateDetailCell(row, licencia);
    updateActions(row, estado);
  }

  function updateList(licencias) {
    if (!Array.isArray(licencias)) {
      return;
    }
    licencias.forEach((licencia) => updateRow(licencia));
  }

  async function fetchLicencias() {
    const endpoint = POLL_ENDPOINTS[scope] || POLL_ENDPOINTS.mine;
    try {
      const response = await fetch(endpoint, { credentials: 'include' });
      if (!response.ok) {
        throw new Error('No se pudieron obtener las licencias');
      }
      const data = await response.json();
      updateList(data.licencias || []);
    } catch (error) {
      console.error('Fallo al actualizar licencias por polling', error);
    }
  }

  function startPolling() {
    stopPolling();
    pollTimer = window.setInterval(fetchLicencias, POLL_INTERVAL);
  }

  function stopPolling() {
    if (pollTimer) {
      window.clearInterval(pollTimer);
      pollTimer = null;
    }
  }

  function disconnectStream() {
    if (eventSource) {
      eventSource.close();
      eventSource = null;
    }
  }

  function connectStream() {
    if (typeof window.EventSource === 'undefined') {
      startPolling();
      return;
    }

    disconnectStream();

    try {
      eventSource = new window.EventSource('/api/licencias/stream', { withCredentials: true });
    } catch (error) {
      console.warn('No fue posible iniciar el stream de licencias, usando polling.', error);
      startPolling();
      return;
    }

    eventSource.addEventListener('open', () => {
      stopPolling();
    });

    eventSource.addEventListener('message', (event) => {
      if (!event.data) {
        return;
      }
      try {
        const payload = JSON.parse(event.data);
        if (payload.scope && payload.scope !== scope) {
          return;
        }
        updateList(payload.licencias || []);
      } catch (error) {
        console.error('No se pudo interpretar el stream de licencias', error);
      }
    });

    eventSource.addEventListener('error', () => {
      if (!eventSource || eventSource.readyState === window.EventSource.CLOSED) {
        disconnectStream();
        startPolling();
      }
    });
  }

  function init() {
    fetchLicencias();
    connectStream();
    if (!eventSource) {
      startPolling();
    }
  }

  document.addEventListener('DOMContentLoaded', init);
  window.addEventListener('beforeunload', () => {
    stopPolling();
    disconnectStream();
  });
})();
