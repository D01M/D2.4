/**
 * Earthquakes Module - Earthquake data fetching and visualization
 * Optimized with caching and lazy rendering
 */

let quakeEntities = [];
let selectedEventForWaves = null;

/**
 * Color helper for magnitude
 * @param {number} m - Magnitude
 */
function colorForMag(m) {
  if (m < 3) return Cesium.Color.fromCssColorString("#28a7ff");
  if (m < 5) return Cesium.Color.fromCssColorString("#ffe45e");
  if (m < 7) return Cesium.Color.fromCssColorString("#ff6b42");
  return Cesium.Color.BLACK;
}

/**
 * Refresh earthquake data from API with caching
 */
async function refreshQuakes() {
  try {
    const startTime = performance.now();
    const mag = parseFloat(document.getElementById("magFilter").value);
    const cacheKey = `earthquakes_${mag}`;

    // Check cache first
    let data = CacheManager.get(cacheKey);
    
    if (!data) {
      // Fetch from API if not cached
      const response = await Promise.race([
        fetch(`/api/earthquakes?mag_filter=${mag}`),
        new Promise((_, reject) => 
          setTimeout(() => reject(new Error('API timeout')), 10000)
        )
      ]);
      data = await response.json();
      
      // Cache the result (2 minute TTL for earthquake data)
      CacheManager.set(cacheKey, data, 120000);
    }

    // Track API performance
    const loadTime = performance.now() - startTime;
    PerformanceMonitor.trackApiCall('earthquakes', loadTime);
    
    clearEntities(quakeEntities);
    let strong = 0;

    (data.features || []).forEach(f => {
      const p = f.properties || {};
      const c = f.geometry?.coordinates || [0, 0, 0];
      const m = Number(p.mag || 0);
      const risk = p.risk_assessment || {};

      if (m >= 5) strong++;

      const tel = `<b>Earthquake</b> ${badge(risk.level)}<br><b>M${fmt(m, 1)}</b> · ${p.place || "Unknown"}<br>Time: ${fmtTime(p.time)}<br>Depth: ${fmt(c[2], 1)} km<br>Coordinates: ${fmt(c[1], 4)}, ${fmt(c[0], 4)}<br>Felt: ${p.felt ?? "N/A"} · MMI: ${p.mmi ?? "N/A"} · CDI: ${p.cdi ?? "N/A"}<br>USGS alert: ${p.alert || "none"} · Status: ${p.status || "unknown"}<br>Risk score: ${risk.score ?? "N/A"}<br>${p.url ? `<a href="${p.url}" target="_blank">USGS page</a>` : ""}`;

      const e = addPoint(
        c[0], c[1], 70000,
        Math.max(6, Math.min(32, 5 + m * 3)),
        colorForMag(m).withAlpha(0.92),
        Cesium.Color.WHITE,
        tel,
        quakeEntities,
        document.getElementById("showQuakes").checked
      );

      e._eventData = {
        lat: c[1],
        lon: c[0],
        depth: c[2] || 10,
        mag: m,
        place: p.place || "Unknown",
        time: p.time,
        reviewed: p.reviewed,
        status: p.status,
        confidence: p.confidence,
        label: p.place || "Unknown"
      };
    });

    if (window.openSeismoGlobeView) {
      window.openSeismoGlobeView.setEarthquakes((data.features || []).map(f => {
        const p = f.properties || {};
        const c = f.geometry?.coordinates || [0, 0, 0];
        return {
          id: p.id || f.id || `${c[1]}:${c[0]}:${p.time}`,
          latitude: c[1],
          longitude: c[0],
          magnitude: Number(p.mag || 0),
          depth_km: c[2] || 10,
          region: p.place || "Unknown",
          time_utc: p.time,
          status: p.status || "unreviewed",
          confidence: p.confidence,
          reviewed: p.reviewed,
          lastUpdated: p.time,
          label: p.place || "Unknown"
        };
      }));
    }

    document.getElementById("quakeCount").textContent = data.features?.length || 0;
    document.getElementById("strongCount").textContent = strong;

    // Select biggest earthquake for waves
    const biggest = (data.features || [])
      .slice()
      .sort((a, b) => (b.properties.mag || 0) - (a.properties.mag || 0))[0];

    if (biggest) {
      const c = biggest.geometry.coordinates;
      const p = biggest.properties;
      selectedEventForWaves = {
        lat: c[1],
        lon: c[0],
        depth: c[2] || 10,
        mag: p.mag || 0,
        place: p.place || "Unknown",
        time: p.time
      };
    }
  } catch (e) {
    console.error(e);
    updateStatus("Earthquake feed failed: " + e.message, true);
  }
}

/**
 * Get selected earthquake for wave animation
 */
function getSelectedEvent() {
  return selectedEventForWaves;
}

/**
 * Set selected earthquake for wave animation
 */
function setSelectedEvent(event) {
  selectedEventForWaves = event;
}

/**
 * Get all earthquake entities
 */
function getQuakeEntities() {
  return quakeEntities;
}
