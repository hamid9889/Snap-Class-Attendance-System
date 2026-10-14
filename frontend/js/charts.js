/**
 * ==============================================================================
 * SNAPCLASS CHARTS & VISUALIZATIONS (Chart.js Integration)
 * Renders modern, interactive analytics for teacher attendance monitoring.
 * ==============================================================================
 */

// Store active Chart instances to avoid canvas reuse errors
const activeCharts = {
  subjectBar: null,
  trendLine: null,
  distributionDoughnut: null
};

/**
 * Destroys existing charts if already initialized on canvas.
 */
function destroyExistingCharts() {
  if (activeCharts.subjectBar) {
    activeCharts.subjectBar.destroy();
    activeCharts.subjectBar = null;
  }
  if (activeCharts.trendLine) {
    activeCharts.trendLine.destroy();
    activeCharts.trendLine = null;
  }
  if (activeCharts.distributionDoughnut) {
    activeCharts.distributionDoughnut.destroy();
    activeCharts.distributionDoughnut = null;
  }
}

/**
 * Initializes and updates all analytics charts with data from Flask API.
 * @param {Object} analyticsData - The data payload from /api/teacher/<id>/analytics
 */
function renderAnalyticsCharts(analyticsData) {
  if (!window.Chart) {
    console.warn("Chart.js library is not loaded yet.");
    return;
  }

  destroyExistingCharts();

  // Common typography & color options for Chart.js
  const defaultFont = { family: "'Outfit', 'Inter', sans-serif", size: 12 };

  // 1. Subject Attendance Percentage (Bar Chart)
  const ctxBar = document.getElementById("chartSubjectAttendance");
  if (ctxBar && analyticsData.subject_chart) {
    activeCharts.subjectBar = new Chart(ctxBar, {
      type: "bar",
      data: {
        labels: analyticsData.subject_chart.labels.length > 0 ? analyticsData.subject_chart.labels : ["No Data"],
        datasets: [{
          label: "Attendance Rate (%)",
          data: analyticsData.subject_chart.values.length > 0 ? analyticsData.subject_chart.values : [0],
          backgroundColor: "rgba(88, 101, 242, 0.8)",
          borderColor: "#5865F2",
          borderWidth: 2,
          borderRadius: 8,
          maxBarThickness: 45
        }]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: { display: false },
          tooltip: {
            callbacks: {
              label: (ctx) => ` Attendance: ${ctx.raw}%`
            }
          }
        },
        scales: {
          y: {
            beginAtZero: true,
            max: 100,
            ticks: {
              callback: (v) => `${v}%`,
              font: defaultFont
            },
            grid: { color: "rgba(226, 232, 240, 0.6)" }
          },
          x: {
            ticks: { font: defaultFont },
            grid: { display: false }
          }
        }
      }
    });
  }

  // 2. Attendance Timeline Trend (Line Chart)
  const ctxLine = document.getElementById("chartAttendanceTrend");
  if (ctxLine && analyticsData.trend_chart) {
    activeCharts.trendLine = new Chart(ctxLine, {
      type: "line",
      data: {
        labels: analyticsData.trend_chart.labels.length > 0 ? analyticsData.trend_chart.labels : ["No Sessions"],
        datasets: [{
          label: "Daily Average (%)",
          data: analyticsData.trend_chart.values.length > 0 ? analyticsData.trend_chart.values : [0],
          borderColor: "#EB459E",
          backgroundColor: "rgba(235, 69, 158, 0.15)",
          borderWidth: 3,
          fill: true,
          tension: 0.35,
          pointBackgroundColor: "#EB459E",
          pointRadius: 5,
          pointHoverRadius: 7
        }]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: { display: false },
          tooltip: {
            callbacks: {
              label: (ctx) => ` Average: ${ctx.raw}%`
            }
          }
        },
        scales: {
          y: {
            beginAtZero: true,
            max: 100,
            ticks: {
              callback: (v) => `${v}%`,
              font: defaultFont
            },
            grid: { color: "rgba(226, 232, 240, 0.6)" }
          },
          x: {
            ticks: { font: defaultFont },
            grid: { display: false }
          }
        }
      }
    });
  }

  // 3. Present vs Absent Ratio (Doughnut Chart)
  const ctxDoughnut = document.getElementById("chartAttendanceRatio");
  if (ctxDoughnut && analyticsData.doughnut_chart) {
    const totalP = analyticsData.doughnut_chart.values[0] || 0;
    const totalA = analyticsData.doughnut_chart.values[1] || 0;
    const hasData = totalP + totalA > 0;

    activeCharts.distributionDoughnut = new Chart(ctxDoughnut, {
      type: "doughnut",
      data: {
        labels: ["Present", "Absent"],
        datasets: [{
          data: hasData ? [totalP, totalA] : [1, 0],
          backgroundColor: hasData ? ["#10B981", "#EF4444"] : ["#E2E8F0", "#E2E8F0"],
          borderWidth: 0,
          hoverOffset: 6
        }]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: {
            position: "bottom",
            labels: { font: defaultFont, boxWidth: 14 }
          },
          tooltip: {
            enabled: hasData,
            callbacks: {
              label: (ctx) => ` ${ctx.label}: ${ctx.raw} record(s)`
            }
          }
        },
        cutout: "65%"
      }
    });
  }
}
