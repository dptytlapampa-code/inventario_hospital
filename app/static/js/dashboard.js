(function () {
  const REFRESH_INTERVAL = 30000;
  let refreshTimer = null;
  let charts = {};

  function getContext(id) {
    const canvas = document.getElementById(id);
    return canvas ? canvas.getContext('2d') : null;
  }

  function formatNumber(value) {
    return new Intl.NumberFormat('es-AR').format(value || 0);
  }

  function updateUpdatedAt(text) {
    const container = document.querySelector('[data-dashboard-updated]');
    if (container) {
      container.textContent = `Actualizado: ${text}`;
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
      variationEl.classList.remove('kpi-variation--up', 'kpi-variation--steady');
      const icon = variationEl.querySelector('.kpi-trend-icon');
      const deltaValue = variationEl.querySelector('.kpi-trend-value');
      if (delta > 0) {
        variationEl.classList.add('kpi-variation--up');
        if (icon) icon.textContent = '▲';
        if (deltaValue) deltaValue.textContent = `+${formatNumber(delta)}`;
      } else {
        variationEl.classList.add('kpi-variation--steady');
        if (icon) icon.textContent = '→';
        if (deltaValue) deltaValue.textContent = '0';
      }
    });
  }

  function renderCritical(list) {
    const container = document.querySelector('[data-critical-list]');
    const totalBadge = document.querySelector('[data-critical-total]');
    if (totalBadge) {
      totalBadge.textContent = formatNumber(list.length);
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
        const faltante = item.faltante || Math.max((item.stock_minimo || 0) - (item.stock || 0), 0);
        return `
          <li class="list-group-item d-flex justify-content-between align-items-start">
            <div>
              <div class="fw-semibold">${item.nombre}</div>
              <div class="text-muted small">Mínimo ${formatNumber(item.stock_minimo)} · Faltan ${formatNumber(faltante)}</div>
            </div>
            <span class="status-badge status-badge--danger">${formatNumber(item.stock)}</span>
          </li>
        `;
      })
      .join('');
  }

  function palette() {
    return [
      '#2563eb',
      '#16a34a',
      '#f59f00',
      '#d9480f',
      '#0ca678',
      '#845ef7',
      '#f783ac',
    ];
  }

  function createChart(key, config) {
    const ctx = getContext(config.elementId);
    if (!ctx || typeof Chart === 'undefined') {
      return null;
    }
    if (charts[key]) {
      charts[key].destroy();
    }
    charts[key] = new window.Chart(ctx, {
      type: config.type,
      data: {
        labels: config.labels,
        datasets: [
          {
            label: config.label,
            data: config.data,
            backgroundColor: config.backgroundColor || palette(),
            borderColor: config.borderColor || palette(),
            borderWidth: 1,
          },
        ],
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
    if (config.backgroundColor) {
      chart.data.datasets[0].backgroundColor = config.backgroundColor;
    }
    chart.update();
  }

  function renderCharts(metrics) {
    const stateData = metrics.charts.equipment_state || { labels: [], values: [] };
    const typeData = metrics.charts.equipment_type || { labels: [], values: [] };
    const stockData = metrics.charts.insumo_stock || { labels: [], values: [] };

    const baseOptions = {
      responsive: true,
      maintainAspectRatio: false,
      plugins: { legend: { position: 'bottom' } },
    };

    createChart('equipment_state', {
      elementId: 'chartEquipmentState',
      type: 'doughnut',
      label: 'Equipos',
      labels: stateData.labels,
      data: stateData.values,
      options: baseOptions,
    });

    createChart('equipment_type', {
      elementId: 'chartEquipmentType',
      type: 'bar',
      label: 'Equipos',
      labels: typeData.labels,
      data: typeData.values,
      options: {
        ...baseOptions,
        scales: {
          x: { ticks: { autoSkip: false, maxRotation: 0 } },
          y: { beginAtZero: true },
        },
      },
    });

    createChart('insumo_stock', {
      elementId: 'chartInsumoStock',
      type: 'bar',
      label: 'Stock',
      labels: stockData.labels,
      data: stockData.values,
      backgroundColor: palette().map((color) => `${color}CC`),
      options: {
        ...baseOptions,
        scales: {
          x: { ticks: { autoSkip: false } },
          y: { beginAtZero: true },
        },
      },
    });
  }

  function refreshCharts(metrics) {
    updateChart('equipment_state', {
      elementId: 'chartEquipmentState',
      labels: metrics.charts.equipment_state.labels,
      data: metrics.charts.equipment_state.values,
    });

    updateChart('equipment_type', {
      elementId: 'chartEquipmentType',
      labels: metrics.charts.equipment_type.labels,
      data: metrics.charts.equipment_type.values,
    });

    updateChart('insumo_stock', {
      elementId: 'chartInsumoStock',
      labels: metrics.charts.insumo_stock.labels,
      data: metrics.charts.insumo_stock.values,
      backgroundColor: palette().map((color) => `${color}CC`),
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

  function updateDashboard(metrics) {
    if (!metrics) {
      return;
    }
    renderKpis(metrics.kpis || []);
    renderCritical(metrics.critical_supplies || []);
    updateUpdatedAt(metrics.generated_at_display || '—');
    if (!charts.equipment_state) {
      renderCharts(metrics);
    } else {
      refreshCharts(metrics);
    }
  }

  function init() {
    const initial = window.dashboardMetrics || {};
    if (Object.keys(initial).length) {
      renderKpis(initial.kpis || []);
      renderCritical(initial.critical_supplies || []);
      renderCharts(initial);
      updateUpdatedAt(initial.generated_at_display || '—');
    }
    refreshTimer = window.setInterval(fetchMetrics, REFRESH_INTERVAL);
    fetchMetrics();
  }

  document.addEventListener('DOMContentLoaded', init);

  window.addEventListener('beforeunload', () => {
    if (refreshTimer) {
      window.clearInterval(refreshTimer);
    }
  });
})();
