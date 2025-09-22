(function () {
  function renderCharts() {
    if (window.Chart) {
      var inventoryCanvas = document.getElementById('inventoryChart');
      if (inventoryCanvas) {
        var payload = window.dashboardData || { labels: [], values: [] };
        new window.Chart(inventoryCanvas, {
          type: 'doughnut',
          data: {
            labels: payload.labels,
            datasets: [
              {
                label: 'Equipos',
                data: payload.values,
                backgroundColor: ['#0d6efd', '#198754', '#6f42c1', '#ffc107'],
              },
            ],
          },
          options: {
            plugins: { legend: { position: 'bottom' } },
          },
        });
      }
      var licenseCanvas = document.getElementById('licenseChart');
      if (licenseCanvas) {
        var licensePayload = window.licensesData || { labels: [], values: [] };
        new window.Chart(licenseCanvas, {
          type: 'bar',
          data: {
            labels: licensePayload.labels,
            datasets: [
              {
                label: 'Licencias aprobadas',
                data: licensePayload.values,
                backgroundColor: '#0d6efd',
              },
            ],
          },
          options: {
            scales: { y: { beginAtZero: true } },
            plugins: { legend: { display: false } },
          },
        });
      }
    }
  }

  if (document.readyState !== 'loading') {
    renderCharts();
  } else {
    document.addEventListener('DOMContentLoaded', renderCharts);
  }
})();
