(function () {
  const POLL_INTERVAL = 60000;
  let refreshTimer = null;
  let eventSource = null;
  const charts = {};
  let latestMetrics = {};

  function getContext(id) {
    const canvas = document.getElementById(id);
    return canvas ? canvas.getContext('2d') : null;
  }

  function formatNumber(value) {
    return new Intl.NumberFormat('es-AR').format(value || 0);
  }

  function getThemeContext() {
    const styles = getComputedStyle(document.documentElement);
    const textColor = styles.getPropertyValue('--bs-body-color').trim() || '#212529';
    const gridColor = styles.getPropertyValue('--bs-border-color-translucent').trim() || 'rgba(0, 0, 0, 0.1)';
    const paletteVars = ['--bs-primary', '--bs-success', '--bs-warning', '--bs-danger', '--bs-info', '--bs-indigo', '--bs-pink'];
    const fallback = ['#0d6efd', '#198754', '#ffc107', '#dc3545', '#20c997', '#6610f2', '#d63384'];
    const baseColors = paletteVars.map((variable, index) => styles.getPropertyValue(variable).trim() || fallback[index]);
    return { styles, textColor, gridColor, baseColors };
  }

  function colorWithAlpha(color, alpha) {
    if (!color || alpha >= 1) {
      return color;
    }
    if (color.startsWith('#')) {
      let hex = color.slice(1);
      if (hex.length === 3) {
        hex = hex.split('').map((char) => char + char).join('');
      }
      if (hex.length >= 6) {
        const r = parseInt(hex.slice(0, 2), 16);
        const g = parseInt(hex.slice(2, 4), 16);
        const b = parseInt(hex.slice(4, 6), 16);
        return `rgba(${r}, ${g}, ${b}, ${alpha})`;
      }
    }
    if (color.startsWith('rgb')) {
      const parts = color.replace(/rgba?\(|\)/g, '').split(',');
      const [r = 0, g = 0, b = 0] = parts.map((value) => parseInt(value, 10));
      return `rgba(${r}, ${g}, ${b}, ${alpha})`;
    }
    return color;
  }

  function paletteWithAlpha(colors, alpha) {
    return colors.map((color) => colorWithAlpha(color, alpha));
  }

  function mergeOptions(base, overrides) {
    const output = { ...base };
    Object.keys(overrides || {}).forEach((key) => {
      const baseValue = base[key];
      const overrideValue = overrides[key];
      if (
        baseValue &&
        overrideValue &&
        typeof baseValue === 'object' &&
        typeof overrideValue === 'object' &&
        !Array.isArray(baseValue) &&
        !Array.isArray(overrideValue)
      ) {
        output[key] = mergeOptions(baseValue, overrideValue);
      } else {
        output[key] = overrideValue;
      }
    });
    return output;
  }

  function buildChartOptions(theme, overrides = {}) {
    const base = {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: {
          position: 'bottom',
          labels: { color: theme.textColor },
        },
      },
      scales: {
        x: {
          grid: { color: theme.gridColor },
          ticks: { color: theme.textColor },
        },
        y: {
          beginAtZero: true,
          grid: { color: theme.gridColor },
          ticks: { color: theme.textColor },
        },
      },
    };
    if (!overrides || typeof overrides !== 'object') {
      return base;
    }
    return mergeOptions(base, overrides);
  }

  function updateUpdatedAt(text) {
    const label = document.getElementById('last-updated');
    if (label) {
      label.textContent = `Actualizado: ${text}`;
    }
  }

  function renderKpis(kpis) {
    const cards = document.querySelectorAll('[data-kpi-card]');
    cards.forEach((card) => {
      const key = card.getAttribute('data-kpi-card');
      const kpi = kpis.find((item) => item.key === key);
      const valueEl = card.querySelector('[data-kpi-value]');
      const variationEl = card.querySelector('[data-kpi-variation]');
      if (!kpi || !valueEl || !variationEl) {
        return;
      }
      valueEl.textContent = formatNumber(kpi.value);
      const delta = kpi.delta || 0;
      variationEl.classList.remove('kpi-variation--up', 'kpi-variation--steady', 'kpi-variation--down');
      const icon = variationEl.querySelector('.kpi-trend-icon');
      const deltaValue = variationEl.querySelector('.kpi-trend-value');
      if (delta > 0) {
        variationEl.classList.add('kpi-variation--up');
        if (icon) icon.textContent = '▲';
        if (deltaValue) deltaValue.textContent = `+${formatNumber(delta)}`;
      } else if (delta < 0) {
        variationEl.classList.add('kpi-variation--down');
        if (icon) icon.textContent = '▼';
        if (deltaValue) deltaValue.textContent = `-${formatNumber(Math.abs(delta))}`;
      } else {
        variationEl.classList.add('kpi-variation--steady');
        if (icon) icon.textContent = '→';
        if (deltaValue) deltaValue.textContent = '0';
      }
    });
  }

  function renderCritical(list, total) {
    const container = document.querySelector('[data-critical-list]');
    const totalBadge = document.querySelector('[data-critical-total]');
    if (totalBadge) {
      const totalValue = typeof total === 'number' ? total : list.length;
      totalBadge.textContent = formatNumber(totalValue);
    }
    if (!container) {
      return;
    }
    if (!list.length) {
      container.innerHTML = '<li class="list-group-item text-muted">Sin insumos en alerta.</li>';
      return;
    }
    container.innerHTML = list
      .map((item) => {
        const minimo = item.stock_minimo || 0;
        const stock = item.stock || 0;
        const faltante = item.faltante || Math.max(minimo - stock, 0);
        const coverageRaw = typeof item.coverage_percent === 'number' ? item.coverage_percent : minimo > 0 ? (stock / minimo) * 100 : 0;
        const coverage = Math.max(0, Math.min(100, Math.round(coverageRaw)));
        return `
          <li class="list-group-item">
            <div class="d-flex justify-content-between align-items-start gap-3">
              <div>
                <div class="fw-semibold">${item.nombre}</div>
                <div class="text-body-secondary small">Stock actual ${formatNumber(stock)} · Mínimo ${formatNumber(minimo)}</div>
              </div>
              <span class="badge rounded-pill text-bg-danger-subtle text-danger-emphasis">Faltan ${formatNumber(faltante)}</span>
            </div>
            <div class="progress mt-3" style="height: 0.45rem;" role="progressbar" aria-valuenow="${coverage}" aria-valuemin="0" aria-valuemax="100">
              <div class="progress-bar bg-danger" style="width: ${coverage}%"></div>
            </div>
            <div class="d-flex justify-content-between small text-body-secondary mt-2">
              <span>Cobertura ${coverage}%</span>
              <span>Disponible ${formatNumber(stock)}</span>
            </div>
          </li>
        `;
      })
      .join('');
  }

  function renderLicensesToday(payload) {
    const totalBadge = document.querySelector('[data-licenses-total]');
    const listContainer = document.querySelector('[data-licenses-list]');
    if (totalBadge) {
      totalBadge.textContent = formatNumber((payload && payload.total) || 0);
    }
    if (!listContainer) {
      return;
    }
    const items = (payload && payload.items) || [];
    if (!items.length) {
      listContainer.innerHTML = '<li class="list-group-item text-muted">Sin licencias registradas para hoy.</li>';
      return;
    }
    listContainer.innerHTML = items
      .map((item) => {
        const hasta = item.hasta || '—';
        const hospital = item.hospital || 'Sin hospital';
        const tipo = item.tipo || '';
        return `
          <li class="list-group-item">
            <div class="fw-semibold">${item.nombre || '—'}</div>
            <div class="text-body-secondary small">${hospital} · hasta ${hasta}${tipo ? ` · ${tipo}` : ''}</div>
          </li>
        `;
      })
      .join('');
  }

  function createChart(key, config) {
    const ctx = getContext(config.elementId);
    if (!ctx || typeof Chart === 'undefined') {
      return null;
    }
    if (charts[key]) {
      charts[key].destroy();
    }
    const dataset = {
      label: config.label,
      data: config.data,
      borderWidth: 1,
      ...(config.dataset || {}),
    };
    charts[key] = new window.Chart(ctx, {
      type: config.type,
      data: {
        labels: config.labels,
        datasets: [dataset],
      },
      options: config.options || {},
    });
    return charts[key];
  }

  function updateChart(key, config) {
    const chart = charts[key];
    if (!chart) {
      createChart(key, config);
      return;
    }
    chart.data.labels = config.labels;
    chart.data.datasets[0].data = config.data;
    if (config.dataset) {
      Object.assign(chart.data.datasets[0], config.dataset);
    }
    if (config.options) {
      chart.options = mergeOptions(chart.options || {}, config.options);
    }
    chart.update();
  }

  function renderCharts(metrics) {
    const theme = getThemeContext();
    const stateData = metrics.charts.equipment_state || { labels: [], values: [] };
    const typeData = metrics.charts.equipment_type || { labels: [], values: [] };
    const stockData = metrics.charts.insumo_stock || { labels: [], values: [] };
    const doughnutOptions = buildChartOptions(theme);
    delete doughnutOptions.scales;

    createChart('equipment_state', {
      elementId: 'chartEquipmentState',
      type: 'doughnut',
      label: 'Equipos',
      labels: stateData.labels,
      data: stateData.values,
      dataset: {
        backgroundColor: theme.baseColors,
        borderColor: paletteWithAlpha(theme.baseColors, 0.85),
      },
      options: doughnutOptions,
    });

    createChart('equipment_type', {
      elementId: 'chartEquipmentType',
      type: 'bar',
      label: 'Equipos',
      labels: typeData.labels,
      data: typeData.values,
      dataset: {
        backgroundColor: paletteWithAlpha(theme.baseColors, 0.7),
        borderColor: theme.baseColors,
      },
      options: buildChartOptions(theme, {
        scales: {
          x: { ticks: { autoSkip: false, maxRotation: 0 } },
        },
      }),
    });

    createChart('insumo_stock', {
      elementId: 'chartInsumoStock',
      type: 'bar',
      label: 'Stock',
      labels: stockData.labels,
      data: stockData.values,
      dataset: {
        backgroundColor: paletteWithAlpha(theme.baseColors, 0.7),
        borderColor: theme.baseColors,
      },
      options: buildChartOptions(theme, {
        scales: {
          x: { ticks: { autoSkip: false } },
        },
      }),
    });
  }

  function refreshCharts(metrics) {
    const chartsData = metrics.charts || {};
    const stateData = chartsData.equipment_state || { labels: [], values: [] };
    const typeData = chartsData.equipment_type || { labels: [], values: [] };
    const stockData = chartsData.insumo_stock || { labels: [], values: [] };
    const theme = getThemeContext();
    updateChart('equipment_state', {
      elementId: 'chartEquipmentState',
      labels: stateData.labels,
      data: stateData.values,
      dataset: {
        backgroundColor: theme.baseColors,
        borderColor: paletteWithAlpha(theme.baseColors, 0.85),
      },
    });

    updateChart('equipment_type', {
      elementId: 'chartEquipmentType',
      labels: typeData.labels,
      data: typeData.values,
      dataset: {
        backgroundColor: paletteWithAlpha(theme.baseColors, 0.7),
        borderColor: theme.baseColors,
      },
    });

    updateChart('insumo_stock', {
      elementId: 'chartInsumoStock',
      labels: stockData.labels,
      data: stockData.values,
      dataset: {
        backgroundColor: paletteWithAlpha(theme.baseColors, 0.7),
        borderColor: theme.baseColors,
      },
    });
  }

  async function fetchMetrics() {
    try {
      const response = await fetch('/api/dashboard/metrics', { credentials: 'include' });
      if (!response.ok) {
        throw new Error('No se pudieron obtener los datos');
      }
      const payload = await response.json();
      updateDashboard(payload);
    } catch (error) {
      console.error('Actualización de dashboard fallida', error);
    }
  }

  function startPolling() {
    stopPolling();
    refreshTimer = window.setInterval(fetchMetrics, POLL_INTERVAL);
  }

  function stopPolling() {
    if (refreshTimer) {
      window.clearInterval(refreshTimer);
      refreshTimer = null;
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
      eventSource = new window.EventSource('/api/dashboard/stream', { withCredentials: true });
    } catch (error) {
      console.warn('No fue posible iniciar el stream SSE, usando polling.', error);
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
        updateDashboard(payload);
      } catch (error) {
        console.error('No se pudo interpretar el evento SSE de dashboard', error);
      }
    });

    eventSource.addEventListener('error', () => {
      if (!eventSource || eventSource.readyState === window.EventSource.CLOSED) {
        disconnectStream();
        startPolling();
      }
    });
  }

  function updateDashboard(metrics) {
    if (!metrics) {
      return;
    }
    latestMetrics = metrics;
    renderKpis(metrics.kpis || []);
    renderCritical(metrics.critical_supplies || [], metrics.critical_supplies_total);
    renderLicensesToday(metrics.licenses_today || {});
    updateUpdatedAt(metrics.generated_at_display || '—');
    if (!charts.equipment_state) {
      renderCharts(metrics);
    } else {
      refreshCharts(metrics);
    }
  }

  function init() {
    const initial = window.dashboardMetrics || {};
    latestMetrics = initial;
    if (Object.keys(initial).length) {
      renderKpis(initial.kpis || []);
      renderCritical(initial.critical_supplies || [], initial.critical_supplies_total);
      renderLicensesToday(initial.licenses_today || {});
      renderCharts(initial);
      updateUpdatedAt(initial.generated_at_display || '—');
    }
    fetchMetrics();
    connectStream();
    if (!eventSource) {
      startPolling();
    }
  }

  document.addEventListener('DOMContentLoaded', init);

  document.addEventListener('theme:changed', () => {
    if (!Object.keys(charts).length || !Object.keys(latestMetrics || {}).length) {
      return;
    }
    renderCharts(latestMetrics);
  });

  window.addEventListener('beforeunload', () => {
    stopPolling();
    disconnectStream();
  });
})();
