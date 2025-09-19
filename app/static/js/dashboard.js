(function () {
  function initChart() {
    var canvas = document.getElementById('inventoryChart');
    if (!canvas || !window.Chart) {
      return;
    }
    var payload = window.dashboardData || { labels: [], values: [] };
    new window.Chart(canvas, {
      type: 'doughnut',
      data: {
        labels: payload.labels,
        datasets: [
          {
            label: 'Registros',
            data: payload.values,
            backgroundColor: ['#0d6efd', '#198754', '#6f42c1', '#ffc107'],
          },
        ],
      },
      options: {
        plugins: {
          legend: {
            position: 'bottom',
          },
        },
      },
    });
  }

  if (document.readyState !== 'loading') {
    initChart();
  } else {
    document.addEventListener('DOMContentLoaded', initChart);
  }
})();
