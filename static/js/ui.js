/**
 * UI Module - User interface controls, event handling, and data display
 */

let volcanoEntities = [];
let faultEntities = [];
let riskEntities = [];
let placeEntities = [];

function setViewMode(mode) {
  if (window.openSeismoGlobeView) {
    window.openSeismoGlobeView.setMode(mode);
  }
}

const PLACES = [
  ["Georgia", 42.1, 43.5, "country"],
  ["Tbilisi", 41.7151, 44.8271, "city"],
  ["Kutaisi", 42.2679, 42.6946, "city"],
  ["Batumi", 41.6168, 41.6367, "city"],
  ["Turkey", 39, 35, "country"],
  ["Istanbul", 41.0082, 28.9784, "city"],
  ["Ankara", 39.9334, 32.8597, "city"],
  ["Greece", 39, 22, "country"],
  ["Athens", 37.9838, 23.7275, "city"],
  ["Japan", 37.5, 138, "country"],
  ["Tokyo", 35.6762, 139.6503, "city"],
  ["Sapporo", 43.0618, 141.3545, "city"],
  ["Taipei", 25.033, 121.5654, "city"],
  ["Indonesia", -2.5, 118, "country"],
  ["Jakarta", -6.2088, 106.8456, "city"],
  ["Chile", -30, -71, "country"],
  ["Santiago", -33.4489, -70.6693, "city"],
  ["USA", 39.5, -98.35, "country"],
  ["San Francisco", 37.7749, -122.4194, "city"],
  ["Los Angeles", 34.0522, -118.2437, "city"],
  ["Mexico City", 19.4326, -99.1332, "city"],
  ["Italy", 42.8, 12.5, "country"],
  ["Rome", 41.9028, 12.4964, "city"],
  ["New Zealand", -41, 173, "country"],
  ["Wellington", -41.2865, 174.7762, "city"]
];

/**
 * Update status message in footer
 * @param {string} msg - Message text
 * @param {boolean} bad - Whether to show as error
 */
function updateStatus(msg, bad = false) {
  document.getElementById("statusText").innerHTML = bad ? `<span class="err">${msg}</span>` : msg;
}

/**
 * Clear entities from array and Cesium viewer
 * @param {Array} arr - Array of entities
 */
function clearEntities(arr) {
  arr.forEach(e => {
    try {
      viewer.entities.remove(e);
    } catch (_) {}
  });
  arr.length = 0;
}

/**
 * Set visibility of entities
 * @param {Array} arr - Array of entities
 * @param {boolean} val - Visibility flag
 */
function setVisible(arr, val) {
  arr.forEach(e => (e.show = val));
}

/**
 * Get risk class name
 * @param {string} level - Risk level
 */
function riskClass(level) {
  return String(level || "low").toLowerCase().replace(" ", "-");
}

/**
 * Create risk level badge HTML
 * @param {string} level - Risk level
 */
function badge(level) {
  return `<span class="badge ${riskClass(level)}">${level || "low"}</span>`;
}

/**
 * Get color for risk level
 * @param {string} level - Risk level
 */
function colorForRisk(level) {
  level = String(level || "low").toLowerCase();
  if (level === "extreme") return Cesium.Color.BLACK;
  if (level === "very high") return Cesium.Color.fromCssColorString("#ff4d6d");
  if (level === "high") return Cesium.Color.fromCssColorString("#ff8d3d");
  if (level === "moderate") return Cesium.Color.fromCssColorString("#ffd66b");
  return Cesium.Color.fromCssColorString("#28a7ff");
}

/**
 * Format number to fixed decimal places
 * @param {number} v - Value
 * @param {number} d - Decimal places
 */
function fmt(v, d = 2) {
  let n = Number(v);
  return Number.isFinite(n) ? n.toFixed(d) : "N/A";
}

/**
 * Format timestamp to locale string
 * @param {number} ms - Milliseconds since epoch
 */
function fmtTime(ms) {
  return ms ? new Date(ms).toLocaleString() : "Unknown";
}

/**
 * Fetch JSON from API
 * @param {string} url - URL to fetch
 */
async function fetchJson(url) {
  const r = await fetch(url);
  if (!r.ok) throw new Error(`${url} failed ${r.status}`);
  return await r.json();
}

/**
 * Wire up UI event listeners
 */
function wire() {
  // Magnitude filter
  document.getElementById("magFilter").addEventListener("input", e =>
    (document.getElementById("magValue").textContent = parseFloat(e.target.value).toFixed(1))
  );
  document.getElementById("magFilter").addEventListener("change", refreshQuakes);

  // Layer visibility toggles
  [
    ["showQuakes", quakeEntities],
    ["showStations", stationEntities],
    ["showActiveDetections", []],
    ["showAlerts", []],
    ["showBoundaries", []],
    ["showVolcanoes", volcanoEntities],
    ["showFaults", faultEntities],
    ["showRisks", riskEntities],
    ["showPlaces", placeEntities]
  ].forEach(([id, arr]) => {
    document.getElementById(id).addEventListener("change", e => {
      setVisible(arr, e.target.checked);
      if (window.openSeismoGlobeView) {
        window.openSeismoGlobeView.scheduleSync();
      }
    });
  });

  // Wave visibility toggle
  document.getElementById("showWaves").addEventListener("change", e => {
    if (!e.target.checked) {
      clearWaveAnimations();
    } else if (selectedEventForWaves) {
      drawWaves(selectedEventForWaves);
    }
  });

  [
    "stationNetworkFilter",
    "stationStatusFilter",
    "stationChannelFilter",
    "stationGeoFilter",
    "stationTagFilter",
    "stationActiveRecentFilter",
    "stationRecentMinutesFilter"
  ].forEach(id => {
    const element = document.getElementById(id);
    if (element) {
      element.addEventListener("change", () => refreshStations());
    }
  });
}

/**
 * Add geographic places (cities, countries) to the map
 */
function addPlaces() {
  clearEntities(placeEntities);

  PLACES.forEach(([name, lat, lon, type]) => {
    const isCity = type === "city";
    const color = isCity ? Cesium.Color.WHITE : Cesium.Color.fromCssColorString("#8ab7ff");

    addPoint(
      lon,
      lat,
      isCity ? 85000 : 160000,
      isCity ? 5 : 7,
      color,
      Cesium.Color.BLACK,
      `<b>${name}</b><br>${isCity ? "City" : "Country"}<br>${fmt(lat, 4)}, ${fmt(lon, 4)}`,
      placeEntities,
      document.getElementById("showPlaces").checked
    );
  });
}

/**
 * Refresh all data sources
 */
async function refreshAll() {
  updateStatus("Loading data...");
  await Promise.allSettled([
    refreshQuakes(),
    refreshStations(),
    refreshVolcanoes(),
    refreshFaults(),
    refreshRisks(),
    refreshSummary()
  ]);
  updateStatus("Live · refreshed " + new Date().toLocaleTimeString());
}

/**
 * Refresh volcano data from API
 */
async function refreshVolcanoes() {
  try {
    const data = await fetchJson("/api/volcanoes");
    clearEntities(volcanoEntities);

    (data.volcanoes || []).forEach(v =>
      addPoint(
        v.lon,
        v.lat,
        95000,
        11,
        Cesium.Color.fromCssColorString("#ff2ea6"),
        Cesium.Color.WHITE,
        `<b>Volcano</b><br>${v.name}<br>${v.region}<br>Status: ${v.status}<br>Elevation: ${v.elevation || "?"} m`,
        volcanoEntities,
        document.getElementById("showVolcanoes").checked
      )
    );
  } catch (e) {
    console.error(e);
  }
}

/**
 * Refresh fault data from API
 */
async function refreshFaults() {
  try {
    const data = await fetchJson("/api/faults");
    clearEntities(faultEntities);

    const rows = [];

    (data.faults || []).forEach(f => {
      rows.push(
        `<div class="item"><b>${f.name}</b> ${badge(f.risk_level)}<br>${f.type} · ${f.classification || ""}<br>${(f.primary_hazards || []).join(", ")}</div>`
      );

      (f.points || []).forEach((p, i) =>
        addPoint(
          p[1],
          p[0],
          65000,
          f.risk_level === "extreme" ? 7 : 5,
          colorForRisk(f.risk_level),
          Cesium.Color.WHITE,
          `<b>${f.name}</b> ${badge(f.risk_level)}<br>Type: ${f.type}<br>${f.classification || ""}<br>Hazards: ${(f.primary_hazards || []).join(", ")}<br>Exposure: ${f.exposure || "N/A"}<br>Preparedness: ${f.preparedness || "N/A"}<br>Point ${i + 1}`,
          faultEntities,
          document.getElementById("showFaults").checked
        )
      );
    });

    if (window.openSeismoGlobeView) {
      const boundaryLines = (data.faults || [])
        .filter(f => Array.isArray(f.points) && f.points.length > 1)
        .map((f, idx) => ({
          id: f.id || f.name || `fault-${idx}`,
          positions: f.points.flatMap(p => [p[1], p[0], 0]),
          color: colorForRisk(f.risk_level),
          width: f.risk_level === "extreme" ? 3 : 2
        }));
      window.openSeismoGlobeView.setBoundaries(boundaryLines);
    }

    document.getElementById("faultList").innerHTML = rows.join("") || "No faults.";
  } catch (e) {
    console.error(e);
  }
}

/**
 * Refresh risk zones from API
 */
async function refreshRisks() {
  try {
    const data = await fetchJson("/api/disaster-risks");
    clearEntities(riskEntities);

    (data.risks || []).forEach(r => {
      const tel = `<b>${r.name}</b> ${badge(r.risk_level)}<br>Hazard: ${r.hazard}<br>Region: ${r.region}<br>Trigger: ${r.trigger}<br><br><b>Safety</b><br>${(r.safety || []).map(x => "• " + x).join("<br>")}`;

      addRing(r.lon, r.lat, r.radius_km, colorForRisk(r.risk_level), tel, riskEntities, document.getElementById("showRisks").checked);
      addPoint(r.lon, r.lat, 110000, 8, colorForRisk(r.risk_level), Cesium.Color.WHITE, tel, riskEntities, document.getElementById("showRisks").checked);
    });

    document.getElementById("riskCount").textContent = data.risks?.length || 0;

    if (window.openSeismoGlobeView) {
      window.openSeismoGlobeView.setAlerts((data.risks || []).map((r, idx) => ({
        id: r.id || r.name || `risk-${idx}`,
        latitude: r.lat,
        longitude: r.lon,
        label: r.name,
        status: r.risk_level,
        confidence: r.score,
        lastUpdated: r.trigger,
        intensity: r.risk_level,
        magnitude: r.score
      })));
    }
  } catch (e) {
    console.error(e);
  }
}

/**
 * Refresh priority safety summary from API
 */
async function refreshSummary() {
  try {
    const data = await fetchJson("/api/safety-summary");
    document.getElementById("summaryList").innerHTML =
      (data.summary || [])
        .map(
          x =>
            `<div class="item"><b>${x.kind}</b> ${badge(x.risk_level)}<br>${x.name}<br>Score: ${x.score}<br>${(x.safety || [])
              .slice(0, 2)
              .map(s => "• " + s)
              .join("<br>")}</div>`
        )
        .join("") || "No priority items.";
  } catch (e) {
    console.error(e);
    document.getElementById("summaryList").innerHTML = `<span class="err">Summary failed: ${e.message}</span>`;
  }
}

/**
 * Initialize the application
 */
async function init() {
  try {
    await initMap();
    if (typeof OpenSeismoGlobeView === "function") {
      window.openSeismoGlobeView = new OpenSeismoGlobeView(getViewer());
      window.openSeismoGlobeView.init();
    }
    setGlobeMode("osm"); // Load OpenStreetMap tiles by default
    wire();
    addPlaces();
    await refreshAll();
  } catch (e) {
    console.error(e);
    updateStatus("Boot failed: " + e.message, true);
  }
}

// Auto-init on page load
window.addEventListener("load", init);
