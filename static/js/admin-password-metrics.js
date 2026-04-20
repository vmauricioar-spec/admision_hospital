(function () {
  var dataScript = document.getElementById("passwordMetricsAnalyticsData");
  if (!dataScript || typeof Chart === "undefined") return;

  var raw = [];
  try {
    raw = JSON.parse(dataScript.textContent || "[]");
  } catch (err) {
    raw = [];
  }

  var metrics = raw
    .map(function (item) {
      var createdAt = item && item.created_at ? new Date(item.created_at) : null;
      return {
        createdAt: createdAt instanceof Date && !isNaN(createdAt) ? createdAt : null,
        username: (item && item.username) || "Sin usuario",
        passwordLength: Number((item && item.password_length) || 0),
        generationMs: Number((item && item.generation_time_ms) || 0),
        strengthLabel: (item && item.strength_label) || "Fragil",
      };
    })
    .filter(function (item) {
      return item.createdAt;
    })
    .sort(function (a, b) {
      return a.createdAt - b.createdAt;
    });

  var cards = document.querySelectorAll(".metric-card-btn[data-metric-target]");
  var modalEl = document.getElementById("metricsChartModal");
  if (!cards.length || !modalEl) return;

  var modalTitleEl = document.getElementById("metricsChartModalTitle");
  var chartOneTitleEl = document.getElementById("metricsChartOneTitle");
  var chartTwoTitleEl = document.getElementById("metricsChartTwoTitle");
  var insightEl = document.getElementById("metricsChartInsight");
  var chartOneCanvas = document.getElementById("metricsChartOne");
  var chartTwoCanvas = document.getElementById("metricsChartTwo");
  var rangeButtons = modalEl.querySelectorAll("[data-range-days]");
  var modal = bootstrap.Modal.getOrCreateInstance(modalEl);

  var state = {
    metric: "generated",
    rangeDays: 7,
  };

  var chartOne = null;
  var chartTwo = null;

  function formatDateKey(date) {
    var y = date.getFullYear();
    var m = String(date.getMonth() + 1).padStart(2, "0");
    var d = String(date.getDate()).padStart(2, "0");
    return y + "-" + m + "-" + d;
  }

  function formatDateLabel(key) {
    var parts = key.split("-");
    if (parts.length !== 3) return key;
    return parts[2] + "/" + parts[1];
  }

  function filterByRange(items, days) {
    if (!days || days <= 0) return items.slice();
    var now = new Date();
    now.setHours(23, 59, 59, 999);
    var start = new Date(now);
    start.setDate(start.getDate() - (days - 1));
    start.setHours(0, 0, 0, 0);
    return items.filter(function (item) {
      return item.createdAt >= start && item.createdAt <= now;
    });
  }

  function aggregateByDay(items, valueGetter, avgMode) {
    var map = {};
    items.forEach(function (item) {
      var key = formatDateKey(item.createdAt);
      if (!map[key]) {
        map[key] = { sum: 0, count: 0 };
      }
      map[key].sum += valueGetter(item);
      map[key].count += 1;
    });
    var keys = Object.keys(map).sort();
    var values = keys.map(function (key) {
      if (avgMode) {
        return map[key].count ? map[key].sum / map[key].count : 0;
      }
      return map[key].sum;
    });
    return {
      labels: keys.map(formatDateLabel),
      values: values,
      sourceKeys: keys,
    };
  }

  function topUsers(items, valueGetter, avgMode, limit) {
    var map = {};
    items.forEach(function (item) {
      var key = item.username || "Sin usuario";
      if (!map[key]) {
        map[key] = { sum: 0, count: 0 };
      }
      map[key].sum += valueGetter(item);
      map[key].count += 1;
    });
    var rows = Object.keys(map).map(function (name) {
      var obj = map[name];
      return {
        name: name,
        value: avgMode ? (obj.count ? obj.sum / obj.count : 0) : obj.sum,
        count: obj.count,
      };
    });
    rows.sort(function (a, b) {
      return b.value - a.value;
    });
    rows = rows.slice(0, limit || 8);
    return {
      labels: rows.map(function (r) {
        return r.name;
      }),
      values: rows.map(function (r) {
        return r.value;
      }),
      rows: rows,
    };
  }

  function lengthDistribution(items) {
    var bins = {
      "8": 0,
      "9": 0,
      "10": 0,
      "11": 0,
      "12": 0,
      "13+": 0,
    };
    items.forEach(function (item) {
      var n = item.passwordLength;
      if (n >= 13) bins["13+"] += 1;
      else if (n >= 8 && n <= 12) bins[String(n)] += 1;
    });
    return {
      labels: Object.keys(bins),
      values: Object.keys(bins).map(function (key) {
        return bins[key];
      }),
    };
  }

  function destroyCharts() {
    if (chartOne) {
      chartOne.destroy();
      chartOne = null;
    }
    if (chartTwo) {
      chartTwo.destroy();
      chartTwo = null;
    }
  }

  function createChart(canvas, type, labels, values, label, color) {
    return new Chart(canvas, {
      type: type,
      data: {
        labels: labels.length ? labels : ["Sin datos"],
        datasets: [
          {
            label: label,
            data: values.length ? values : [0],
            borderColor: color,
            backgroundColor: type === "line" ? "rgba(13,110,253,0.15)" : color,
            fill: type === "line",
            tension: 0.28,
            borderWidth: 2,
            maxBarThickness: 42,
          },
        ],
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: {
            display: false,
          },
        },
        scales: {
          y: {
            beginAtZero: true,
            ticks: {
              precision: 0,
            },
          },
        },
      },
    });
  }

  function setInsight(text) {
    insightEl.textContent = text;
  }

  function renderGenerated(filtered) {
    modalTitleEl.textContent = "Analítica: Contraseñas generadas";
    chartOneTitleEl.textContent = "Generación diaria";
    chartTwoTitleEl.textContent = "Top usuarios por volumen";

    var daily = aggregateByDay(
      filtered,
      function () {
        return 1;
      },
      false
    );
    var users = topUsers(
      filtered,
      function () {
        return 1;
      },
      false,
      6
    );

    destroyCharts();
    chartOne = createChart(
      chartOneCanvas,
      "line",
      daily.labels,
      daily.values,
      "Contraseñas",
      "#2563eb"
    );
    chartTwo = createChart(
      chartTwoCanvas,
      "bar",
      users.labels,
      users.values,
      "Cantidad",
      "#0ea5e9"
    );

    var total = filtered.length;
    var maxDaily = 0;
    daily.values.forEach(function (v) {
      if (v > maxDaily) maxDaily = v;
    });
    setInsight(
      total
        ? "Se registraron " +
            total +
            " contraseñas en el rango. El pico diario fue de " +
            maxDaily +
            " registros."
        : "No hay contraseñas registradas para el rango seleccionado."
    );
  }

  function renderLength(filtered) {
    modalTitleEl.textContent = "Analítica: Longitud promedio";
    chartOneTitleEl.textContent = "Distribución de longitudes";
    chartTwoTitleEl.textContent = "Promedio diario de caracteres";

    var dist = lengthDistribution(filtered);
    var dailyAvg = aggregateByDay(
      filtered,
      function (item) {
        return item.passwordLength;
      },
      true
    );

    destroyCharts();
    chartOne = createChart(
      chartOneCanvas,
      "bar",
      dist.labels,
      dist.values,
      "Frecuencia",
      "#8b5cf6"
    );
    chartTwo = createChart(
      chartTwoCanvas,
      "line",
      dailyAvg.labels,
      dailyAvg.values,
      "Promedio",
      "#a855f7"
    );

    var avg = filtered.length
      ? filtered.reduce(function (acc, item) {
          return acc + item.passwordLength;
        }, 0) / filtered.length
      : 0;
    setInsight(
      filtered.length
        ? "La longitud promedio del periodo es " + avg.toFixed(1) + " caracteres."
        : "No hay datos de longitud para el rango seleccionado."
    );
  }

  function renderTime(filtered) {
    modalTitleEl.textContent = "Analítica: Tiempo promedio de creación";
    chartOneTitleEl.textContent = "Tiempo promedio diario (segundos)";
    chartTwoTitleEl.textContent = "Tiempo promedio por usuario";

    var dailyAvgSec = aggregateByDay(
      filtered,
      function (item) {
        return item.generationMs / 1000;
      },
      true
    );
    var byUserAvgSec = topUsers(
      filtered,
      function (item) {
        return item.generationMs / 1000;
      },
      true,
      6
    );

    destroyCharts();
    chartOne = createChart(
      chartOneCanvas,
      "line",
      dailyAvgSec.labels,
      dailyAvgSec.values,
      "Segundos",
      "#f59e0b"
    );
    chartTwo = createChart(
      chartTwoCanvas,
      "bar",
      byUserAvgSec.labels,
      byUserAvgSec.values,
      "Segundos",
      "#f97316"
    );

    var avgSec = filtered.length
      ? filtered.reduce(function (acc, item) {
          return acc + item.generationMs / 1000;
        }, 0) / filtered.length
      : 0;
    setInsight(
      filtered.length
        ? "El tiempo promedio de creación es " +
            avgSec.toFixed(1) +
            " s. Úsalo para detectar fricción en el proceso."
        : "No hay datos de tiempo para el rango seleccionado."
    );
  }

  function renderCurrent() {
    var filtered = filterByRange(metrics, state.rangeDays);
    if (state.metric === "generated") renderGenerated(filtered);
    else if (state.metric === "length") renderLength(filtered);
    else renderTime(filtered);
  }

  cards.forEach(function (card) {
    card.addEventListener("click", function () {
      state.metric = card.getAttribute("data-metric-target") || "generated";
      renderCurrent();
      modal.show();
    });
  });

  rangeButtons.forEach(function (btn) {
    btn.addEventListener("click", function () {
      var days = parseInt(btn.getAttribute("data-range-days") || "0", 10);
      state.rangeDays = isNaN(days) ? 0 : days;
      rangeButtons.forEach(function (it) {
        it.classList.toggle("active", it === btn);
        if (it === btn) return;
        it.classList.remove("btn-outline-secondary");
      });
      renderCurrent();
    });
  });

  modalEl.addEventListener("hidden.bs.modal", function () {
    destroyCharts();
  });
})();
