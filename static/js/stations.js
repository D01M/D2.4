/**
 * Stations Module - Seismic station data fetching and visualization
 */

let stationEntities = [];

/**
 * Noise level color mapping
 * @param {number} n - Noise level
 */
function noiseColor(n) {
  if (n < 20) return Cesium.Color.fromCssColorString("#00ffd1");
  if (n < 40) return Cesium.Color.fromCssColorString("#7dff5e");
  if (n < 65) return Cesium.Color.fromCssColorString("#ffd45e");
  return Cesium.Color.fromCssColorString("#ff3d5e");
}

/**
 * Refresh station data from API
 */
async function refreshStations() {
  try {
    const data = await fetchJson("/api/stations");
    clearEntities(stationEntities);

    let total = 0;
    let rows = [];

    (data.stations || []).forEach(s => {
      const noise = Number(s.noise_level || 0);
      total += noise;

      const tel = `<b>${s.code}</b> · ${s.name}<br>Network: ${s.network}<br>Country: ${s.country}<br>Health: ${s.health}<br>Latency: ${s.latency_seconds}s<br>Noise: ${fmt(noise, 1)}/100 · ${s.signal_quality}<br>Coverage: ${s.coverage_radius_km} km<br>${
        s.arrival
          ? `Distance: ${s.arrival.distance_km} km (${s.arrival.distance_deg}°)<br>P: ${s.arrival.p_wave_seconds}s · S: ${s.arrival.s_wave_seconds}s · Surface: ${s.arrival.surface_wave_seconds}s`
          : "No linked M4.5+ event"
      }`;

      addPoint(
        s.lon,
        s.lat,
        125000,
        Math.max(7, Math.min(22, 6 + noise / 6)),
        noiseColor(noise).withAlpha(0.95),
        Cesium.Color.WHITE,
        tel,
        stationEntities,
        document.getElementById("showStations").checked
      );

      rows.push(
        `<div class="item"><b>${s.code}</b> ${s.name}<br>Noise ${fmt(noise, 1)} · ${s.signal_quality} · ${s.health}<br>${
          s.arrival
            ? `P ${s.arrival.p_wave_seconds}s / S ${s.arrival.s_wave_seconds}s`
            : "No linked event"
        }</div>`
      );
    });

    document.getElementById("stationCount").textContent = data.stations?.length || 0;
    document.getElementById("stationList").innerHTML = rows.join("") || "No stations.";
  } catch (e) {
    console.error(e);
    document.getElementById("stationList").innerHTML = `<span class="err">Station data failed: ${e.message}</span>`;
  }
}

/**
 * Get all station entities
 */
function getStationEntities() {
  return stationEntities;
}
