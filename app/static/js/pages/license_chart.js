(function () {
  function renderLicenseChart() {
    if (typeof Chart === 'undefined') {
      return;
    }
    const canvas = document.getElementById('licenseChart');
    if (!canvas) {
      return;
    }
    const ctx = canvas.getContext('2d');
    const dataset = window.licensesData || { labels: [], values: [] };

    new Chart(ctx, {
      type: 'bar',
      data: {
        labels: dataset.labels,
        datasets: [
          {
            label: 'Licencias aprobadas',
            data: dataset.values,
            backgroundColor: '#2563eb',
            borderRadius: 6,
          },
        ],
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        scales: {
          y: { beginAtZero: true },
        },
        plugins: {
          legend: { display: false },
        },
      },
    });
  }

  document.addEventListener('DOMContentLoaded', renderLicenseChart);
})();
