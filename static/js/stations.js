/**
 * Stations Module - Seismic station data fetching and visualization
 */

let stationEntities = [];

function formatStationTime(value) {
  if (!value) return "Unknown";
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return "Unknown";
  return date.toLocaleString();
}

function getStationFilters() {
  const network = document.getElementById("stationNetworkFilter")?.value.trim();
  const status = document.getElementById("stationStatusFilter")?.value.trim();
  const channel = document.getElementById("stationChannelFilter")?.value.trim();
  const geo = document.getElementById("stationGeoFilter")?.value.trim();
  const tag = document.getElementById("stationTagFilter")?.value.trim();
  const activeRecent = document.getElementById("stationActiveRecentFilter")?.checked;
  const recentMinutes = Number(document.getElementById("stationRecentMinutesFilter")?.value || 30);

  const params = new URLSearchParams();
  if (network) params.set("network", network);
  if (status) params.set("status", status);
  if (channel) params.set("channel", channel);
  if (geo) {
    params.set("country", geo);
    params.set("region", geo);
  }
  if (tag) params.set("tag", tag);
  if (activeRecent) {
    params.set("active_recent", "1");
    params.set("recent_minutes", String(Number.isFinite(recentMinutes) && recentMinutes > 0 ? recentMinutes : 30));
  }

  const query = params.toString();
  return query ? `?${query}` : "";
}

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
    const data = await fetchJson(`/api/stations${getStationFilters()}`);
    clearEntities(stationEntities);

    let total = 0;
    let rows = [];

    (data.stations || []).forEach(s => {
      const noise = Number(s.noise_level || 0);
      const status = String(s.status || s.health || "unknown").toLowerCase();
      const channels = Array.isArray(s.channels) ? s.channels.join(", ") : String(s.channels || "N/A");
      total += noise;

      const tel = `<b>${s.code}</b> · ${s.name}<br>Network: ${s.network}<br>Status: ${status}<br>Country: ${s.country || "N/A"}<br>Region: ${s.region || "N/A"}<br>Channels: ${channels}<br>Last seen: ${formatStationTime(s.last_seen)}<br>Noise: ${fmt(noise, 1)}/100 · ${s.signal_quality}<br>Provider: ${s.provider || s.source || "N/A"}<br>Coverage: ${s.coverage_radius_km || "N/A"} km<br>${
        s.arrival
          ? `Distance: ${s.arrival.distance_km} km (${s.arrival.distance_deg}°)<br>P: ${s.arrival.p_wave_seconds}s · S: ${s.arrival.s_wave_seconds}s · Surface: ${s.arrival.surface_wave_seconds}s`
          : "No linked M4.5+ event"
      }`;

      addPoint(
        s.lon,
        s.lat,
        125000,
        Math.max(7, Math.min(22, 6 + noise / 6)),
        stationColor(s, noise),
        Cesium.Color.WHITE,
        tel,
        stationEntities,
        document.getElementById("showStations").checked
      );

      rows.push(
        `<div class="item"><b>${s.code}</b> ${s.name}<br>Status ${status} · Noise ${fmt(noise, 1)} · ${s.signal_quality}<br>${
          s.arrival
            ? `P ${s.arrival.p_wave_seconds}s / S ${s.arrival.s_wave_seconds}s`
            : "No linked event"
        }<br>Channels: ${channels}<br>Last seen: ${formatStationTime(s.last_seen)}</div>`
      );
    });

    if (window.openSeismoGlobeView) {
      window.openSeismoGlobeView.setStations((data.stations || []).map(s => ({
        id: s.code,
        code: s.code,
        name: s.name,
        network: s.network,
        country: s.country,
        health: s.health,
        noise_level: s.noise_level,
        signal_quality: s.signal_quality,
        lat: s.lat,
        lon: s.lon,
        lastUpdated: s.lastUpdated || null
      })));
    }

    document.getElementById("stationCount").textContent = data.stations?.length || 0;
    document.getElementById("stationList").innerHTML = rows.join("") || "No stations.";
  } catch (e) {
    console.error(e);
    document.getElementById("stationList").innerHTML = `<span class="err">Station data failed: ${e.message}</span>`;
  }
}

function stationColor(station, noise) {
  const status = String(station.status || station.health || "unknown").toLowerCase();
  if (status === "offline") return Cesium.Color.fromCssColorString("#8b949e").withAlpha(0.35);
  if (status === "delayed") return Cesium.Color.fromCssColorString("#ffb347").withAlpha(0.88);
  if (status === "triggering") return Cesium.Color.fromCssColorString("#ff6b42").withAlpha(1.0);
  if (status === "unknown") return Cesium.Color.fromCssColorString("#aeb8c2").withAlpha(0.7);
  return noiseColor(noise).withAlpha(0.95);
}

/**
 * Get all station entities
 */
function getStationEntities() {
  return stationEntities;
}
