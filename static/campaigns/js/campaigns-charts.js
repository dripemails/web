// Chart.js initialization for campaign analysis
document.addEventListener('DOMContentLoaded', function() {
  initializeMetricsChart();
  initializeMonthlyChart();
  initializePerEmailChart();
});

function initializeMetricsChart() {
  var canvas = document.getElementById('metricsChart');
  if (!canvas) return;

  var sent = parseInt(canvas.dataset.sent) || 0;
  var opens = parseInt(canvas.dataset.opens) || 0;
  var clicks = parseInt(canvas.dataset.clicks) || 0;

  var ctx = canvas.getContext('2d');
  new Chart(ctx, {
    type: 'doughnut',
    data: {
      labels: ['Sent', 'Opens', 'Clicks'],
      datasets: [
        {
          data: [sent, opens, clicks],
          backgroundColor: [
            'rgba(54, 162, 235, 0.8)',
            'rgba(75, 192, 75, 0.8)',
            'rgba(255, 159, 64, 0.8)'
          ],
          borderColor: [
            'rgba(54, 162, 235, 1)',
            'rgba(75, 192, 75, 1)',
            'rgba(255, 159, 64, 1)'
          ],
          borderWidth: 2
        }
      ]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: {
          position: 'bottom'
        }
      }
    }
  });
}

function initializeMonthlyChart() {
  var canvas = document.getElementById('monthlyChart');
  if (!canvas) return;

  var months = [];
  var sent = [];
  var opens = [];
  var clicks = [];

  try {
    months = JSON.parse(canvas.dataset.months || '[]');
    sent = JSON.parse(canvas.dataset.sent || '[]');
    opens = JSON.parse(canvas.dataset.opens || '[]');
    clicks = JSON.parse(canvas.dataset.clicks || '[]');
  } catch (e) {
    console.error('Error parsing monthly chart data:', e);
    return;
  }

  if (months.length === 0) {
    canvas.parentElement.innerHTML = '<p class="text-gray-600">No data available for this campaign.</p>';
    return;
  }

  var ctx = canvas.getContext('2d');
  new Chart(ctx, {
    type: 'line',
    data: {
      labels: months,
      datasets: [
        {
          label: 'Sent',
          data: sent,
          borderColor: 'rgba(54, 162, 235, 1)',
          backgroundColor: 'rgba(54, 162, 235, 0.1)',
          tension: 0.4,
          fill: true
        },
        {
          label: 'Opened',
          data: opens,
          borderColor: 'rgba(75, 192, 75, 1)',
          backgroundColor: 'rgba(75, 192, 75, 0.1)',
          tension: 0.4,
          fill: true
        },
        {
          label: 'Clicked',
          data: clicks,
          borderColor: 'rgba(255, 159, 64, 1)',
          backgroundColor: 'rgba(255, 159, 64, 0.1)',
          tension: 0.4,
          fill: true
        }
      ]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: {
          position: 'top'
        }
      },
      scales: {
        y: {
          beginAtZero: true,
          ticks: {
            stepSize: 1
          }
        }
      }
    }
  });
}

function initializePerEmailChart() {
  var canvas = document.getElementById('perEmailChart');
  if (!canvas) return;

  var labels = [];
  var sent = [];
  var opens = [];
  var clicks = [];

  try {
    labels = JSON.parse(canvas.dataset.labels || '[]');
    sent = JSON.parse(canvas.dataset.sent || '[]');
    opens = JSON.parse(canvas.dataset.opens || '[]');
    clicks = JSON.parse(canvas.dataset.clicks || '[]');
  } catch (e) {
    console.error('Error parsing per-email chart data:', e);
    return;
  }

  if (labels.length === 0) {
    canvas.parentElement.innerHTML = '<p class="text-gray-600">No emails found for this campaign.</p>';
    return;
  }

  var ctx = canvas.getContext('2d');
  new Chart(ctx, {
    type: 'bar',
    data: {
      labels: labels,
      datasets: [
        {
          label: 'Sent',
          data: sent,
          backgroundColor: 'rgba(54, 162, 235, 0.8)',
          borderColor: 'rgba(54, 162, 235, 1)',
          borderWidth: 1
        },
        {
          label: 'Opened',
          data: opens,
          backgroundColor: 'rgba(75, 192, 75, 0.8)',
          borderColor: 'rgba(75, 192, 75, 1)',
          borderWidth: 1
        },
        {
          label: 'Clicked',
          data: clicks,
          backgroundColor: 'rgba(255, 159, 64, 0.8)',
          borderColor: 'rgba(255, 159, 64, 1)',
          borderWidth: 1
        }
      ]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: {
          position: 'top'
        }
      },
      scales: {
        y: {
          beginAtZero: true,
          ticks: {
            stepSize: 1
          }
        }
      }
    }
  });
}
