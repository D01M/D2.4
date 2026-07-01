/**
 * OpenSeismo 3D Globe View
 * Cesium-based globe layer manager with incremental marker updates.
 */

class OpenSeismoGlobeView {
  constructor(viewer) {
    this.viewer = viewer;
    this.mode = "globe";
    this.ready = false;
    this.destroyed = false;
    this.data = {
      stations: [],
      earthquakes: [],
      detections: [],
      alerts: [],
      boundaries: []
    };
    this.collections = {};
    this.indexes = {};
    this.hoverTooltip = null;
    this.lastClick = { id: null, time: 0 };
    this.syncPending = false;
    this.legacySets = {
      stations: () => typeof getStationEntities === "function" ? getStationEntities() : [],
      earthquakes: () => typeof getQuakeEntities === "function" ? getQuakeEntities() : []
    };
    this._onMove = this._onMove.bind(this);
    this._onClick = this._onClick.bind(this);
    this._onDoubleClick = this._onDoubleClick.bind(this);
  }

  init() {
    if (this.destroyed || !this.viewer) return;
    if (!window.WebGLRenderingContext) {
      const fallback = document.getElementById("globeFallback");
      if (fallback) fallback.style.display = "block";
      return;
    }

    this.createCollections();
    this.createTooltip();
    this.attachEvents();
    this._onLiveDetectionBound = event => {
      if (this.destroyed) return;
      const detection = event?.detail;
      if (!detection) return;
      this.data.detections = [detection];
      this.scheduleSync();
    };
    window.addEventListener('openseismo:live-detection', this._onLiveDetectionBound);
    this.setMode("globe");
    this.ready = true;
    console.log("OpenSeismoGlobeView initialized. mode=globe, ready=true, handler attached:", !!this.viewer.screenSpaceEventHandler);
    this.scheduleSync();
  }

  createCollections() {
    const scene = this.viewer.scene;
    this.collections.stations = new Cesium.PointPrimitiveCollection({ show: false });
    this.collections.earthquakes = new Cesium.PointPrimitiveCollection({ show: false });
    this.collections.detections = new Cesium.PointPrimitiveCollection({ show: false });
    this.collections.alerts = new Cesium.PointPrimitiveCollection({ show: false });
    this.collections.boundaries = new Cesium.PolylineCollection({ show: false });

    scene.primitives.add(this.collections.stations);
    scene.primitives.add(this.collections.earthquakes);
    scene.primitives.add(this.collections.detections);
    scene.primitives.add(this.collections.alerts);
    scene.primitives.add(this.collections.boundaries);

    this.indexes.stations = new Map();
    this.indexes.earthquakes = new Map();
    this.indexes.detections = new Map();
    this.indexes.alerts = new Map();
    this.indexes.boundaries = new Map();
  }

  createTooltip() {
    const tooltip = document.createElement("div");
    tooltip.id = "globe-tooltip";
    tooltip.style.cssText = [
      "position: fixed",
      "display: none",
      "z-index: 9998",
      "pointer-events: none",
      "max-width: 280px",
      "padding: 10px 12px",
      "border-radius: 8px",
      "background: rgba(8, 16, 28, 0.92)",
      "color: #e8f1ff",
      "border: 1px solid rgba(108, 198, 255, 0.35)",
      "box-shadow: 0 8px 24px rgba(0,0,0,0.35)",
      "font-size: 12px",
      "line-height: 1.4"
    ].join(";");
    document.body.appendChild(tooltip);
    this.hoverTooltip = tooltip;
  }

  attachEvents() {
    const handler = this.viewer.screenSpaceEventHandler;
    handler.setInputAction(this._onMove, Cesium.ScreenSpaceEventType.MOUSE_MOVE);
    handler.setInputAction(this._onClick, Cesium.ScreenSpaceEventType.LEFT_CLICK);
    handler.setInputAction(this._onDoubleClick, Cesium.ScreenSpaceEventType.LEFT_DOUBLE_CLICK);
    console.log("Events attached to viewer.screenSpaceEventHandler");
  }

  destroy() {
    this.destroyed = true;
    if (this.hoverTooltip) this.hoverTooltip.remove();
    this.hoverTooltip = null;
    if (this.viewer && this.viewer.screenSpaceEventHandler) {
      this.viewer.screenSpaceEventHandler.removeInputAction(Cesium.ScreenSpaceEventType.MOUSE_MOVE);
      this.viewer.screenSpaceEventHandler.removeInputAction(Cesium.ScreenSpaceEventType.LEFT_CLICK);
      this.viewer.screenSpaceEventHandler.removeInputAction(Cesium.ScreenSpaceEventType.LEFT_DOUBLE_CLICK);
    }
    if (this._onLiveDetectionBound) {
      window.removeEventListener('openseismo:live-detection', this._onLiveDetectionBound);
      this._onLiveDetectionBound = null;
    }
    Object.values(this.collections).forEach(collection => {
      try { this.viewer.scene.primitives.remove(collection); } catch (_) {}
    });
    this.collections = {};
    this.indexes = {};
  }

  setMode(mode) {
    this.mode = mode === "globe" ? "globe" : "map";
    const useGlobe = this.mode === "globe";
    const legacyVisible = !useGlobe;
    const modernVisible = useGlobe;

    this.collections.stations.show = modernVisible;
    this.collections.earthquakes.show = modernVisible;
    this.collections.detections.show = modernVisible;
    this.collections.alerts.show = modernVisible;
    this.collections.boundaries.show = modernVisible;

    console.log(`setMode(${this.mode}): earthquakes collection show=${modernVisible}, ready=${this.ready}`);

    setVisible(this.legacySets.stations(), legacyVisible);
    setVisible(this.legacySets.earthquakes(), legacyVisible);

    const globeFallback = document.getElementById("globeFallback");
    if (globeFallback) globeFallback.style.display = !window.WebGLRenderingContext && useGlobe ? "block" : "none";

    this.viewer.scene.requestRender();
  }

  setStations(stations) {
    this.data.stations = Array.isArray(stations) ? stations : [];
    this.scheduleSync();
  }

  setEarthquakes(earthquakes) {
    this.data.earthquakes = Array.isArray(earthquakes) ? earthquakes : [];
    console.log("setEarthquakes called with", this.data.earthquakes.length, "earthquakes");
    this.scheduleSync();
  }

  setDetections(detections) {
    this.data.detections = Array.isArray(detections) ? detections : [];
    this.scheduleSync();
  }

  setAlerts(alerts) {
    this.data.alerts = Array.isArray(alerts) ? alerts : [];
    this.scheduleSync();
  }

  setBoundaries(boundaries) {
    this.data.boundaries = Array.isArray(boundaries) ? boundaries : [];
    this.scheduleSync();
  }

  scheduleSync() {
    if (this.syncPending || !this.ready || this.destroyed) return;
    this.syncPending = true;
    requestAnimationFrame(() => {
      this.syncPending = false;
      this.sync();
    });
  }

  sync() {
    if (this.destroyed || this.mode !== "globe") return;
    console.log("sync() called in globe mode. earthquakes:", this.data.earthquakes.length);
    this.syncPointLayer("stations", this.getStationMarkers());
    this.syncPointLayer("earthquakes", this.getEarthquakeMarkers());
    this.syncPointLayer("detections", this.getDetectionMarkers());
    this.syncPointLayer("alerts", this.getAlertMarkers());
    this.syncBoundaryLayer(this.getBoundaryMarkers());
    this.viewer.scene.requestRender();
  }

  syncPointLayer(layerName, markers) {
    const collection = this.collections[layerName];
    const index = this.indexes[layerName];
    if (!collection || !index) return;

    const nextIds = new Set();
    for (const marker of markers) {
      nextIds.add(marker.id);
      const existing = index.get(marker.id);
      if (existing) {
        existing.position = Cesium.Cartesian3.fromDegrees(marker.longitude, marker.latitude, marker.height || 0);
        existing.pixelSize = marker.size;
        existing.color = marker.color;
        existing.outlineColor = marker.outlineColor || Cesium.Color.WHITE;
        existing.outlineWidth = marker.outlineWidth || 1;
        existing.show = marker.show !== false;
        existing._markerData = marker;
        continue;
      }

      const primitive = collection.add({
        id: marker.id,
        position: Cesium.Cartesian3.fromDegrees(marker.longitude, marker.latitude, marker.height || 0),
        color: marker.color,
        outlineColor: marker.outlineColor || Cesium.Color.WHITE,
        outlineWidth: marker.outlineWidth || 1,
        pixelSize: marker.size,
        show: marker.show !== false,
        disableDepthTestDistance: Number.POSITIVE_INFINITY
      });
      primitive._markerData = marker;
      index.set(marker.id, primitive);
      if (marker.type === "earthquake") console.log(`Created earthquake primitive: ${marker.id}, show=${marker.show}, markerData attached:`, !!primitive._markerData);
    }

    for (const [id, primitive] of index.entries()) {
      if (!nextIds.has(id)) {
        collection.remove(primitive);
        index.delete(id);
      }
    }
  }

  syncBoundaryLayer(markers) {
    const collection = this.collections.boundaries;
    const index = this.indexes.boundaries;
    if (!collection || !index) return;

    const nextIds = new Set();
    for (const marker of markers) {
      nextIds.add(marker.id);
      const existing = index.get(marker.id);
      if (existing) {
        existing.positions = Cesium.Cartesian3.fromDegreesArrayHeights(marker.positions);
        existing.material = marker.color.withAlpha(0.75);
        existing.width = marker.width || 2;
        existing.show = marker.show !== false;
        existing._markerData = marker;
        continue;
      }

      const primitive = collection.add({
        id: marker.id,
        positions: Cesium.Cartesian3.fromDegreesArrayHeights(marker.positions),
        material: marker.color.withAlpha(0.75),
        width: marker.width || 2,
        show: marker.show !== false
      });
      primitive._markerData = marker;
      index.set(marker.id, primitive);
    }

    for (const [id, primitive] of index.entries()) {
      if (!nextIds.has(id)) {
        collection.remove(primitive);
        index.delete(id);
      }
    }
  }

  getStationMarkers() {
    const show = document.getElementById("showStations")?.checked !== false;
    return this.data.stations.map(station => ({
      id: station.id || `station:${station.network || ""}:${station.code || station.id || station.name}`,
      type: "station",
      latitude: Number(station.latitude ?? station.lat ?? 0),
      longitude: Number(station.longitude ?? station.lon ?? 0),
      network: station.network,
      code: station.code,
      name: station.name,
      channels: Array.isArray(station.channels) ? station.channels : [],
      status: String(station.status || station.health || "unknown").toLowerCase(),
      confidence: station.priority,
      label: station.code,
      country: station.country,
      region: station.region,
      provider: station.provider || station.source,
      lastUpdated: station.last_seen || station.lastUpdated,
      noise_level: station.noise_level,
      size: this.stationSize(station),
      color: this.stationColor(station),
      outlineColor: Cesium.Color.WHITE,
      show
    }));
  }

  getEarthquakeMarkers() {
    const show = document.getElementById("showQuakes")?.checked !== false;
    const clusters = this.clusterEarthquakes(this.data.earthquakes);
    return clusters.map(item => ({
      id: item.id,
      type: "earthquake",
      latitude: item.latitude,
      longitude: item.longitude,
      magnitude: item.magnitude,
      intensity: item.intensity,
      status: item.status,
      confidence: item.confidence,
      label: item.label,
      lastUpdated: item.lastUpdated,
      size: item.size,
      color: item.color,
      outlineColor: Cesium.Color.WHITE,
      show
    }));
  }

  getDetectionMarkers() {
    const show = document.getElementById("showActiveDetections")?.checked !== false;
    return this.data.detections.map(detection => ({
      id: `detection:${detection.id || detection.event_id || detection.time}`,
      type: "alert",
      latitude: detection.latitude,
      longitude: detection.longitude,
      magnitude: detection.magnitude,
      intensity: detection.intensity,
      status: detection.status || "automatic",
      confidence: detection.confidence,
      label: detection.label || detection.region,
      lastUpdated: detection.lastUpdated || detection.time,
      size: 14,
      color: Cesium.Color.fromCssColorString("#ffcc66"),
      outlineColor: Cesium.Color.WHITE,
      show
    }));
  }

  getAlertMarkers() {
    const show = document.getElementById("showAlerts")?.checked !== false;
    return this.data.alerts.map(alert => ({
      id: `alert:${alert.id || alert.code || alert.label}`,
      type: "alert",
      latitude: alert.latitude,
      longitude: alert.longitude,
      magnitude: alert.magnitude,
      intensity: alert.intensity,
      status: alert.status,
      confidence: alert.confidence,
      label: alert.label,
      lastUpdated: alert.lastUpdated,
      size: 12,
      color: Cesium.Color.fromCssColorString("#ff6b42"),
      outlineColor: Cesium.Color.WHITE,
      show
    }));
  }

  getBoundaryMarkers() {
    const show = document.getElementById("showBoundaries")?.checked !== false;
    return this.data.boundaries.map((boundary, idx) => ({
      id: boundary.id || `boundary:${idx}`,
      positions: boundary.positions,
      color: boundary.color || Cesium.Color.fromCssColorString("#36ff72"),
      width: boundary.width || 2,
      show
    }));
  }

  clusterEarthquakes(earthquakes) {
    const showClustered = this.cameraHeight() > 9000000;
    if (!showClustered) {
      return earthquakes.map(eq => this.normalizeEarthquake(eq));
    }

    const buckets = new Map();
    const step = this.cameraHeight() > 18000000 ? 4 : 2;

    for (const earthquake of earthquakes) {
      const normalized = this.normalizeEarthquake(earthquake);
      const keyLat = Math.round(normalized.latitude / step) * step;
      const keyLon = Math.round(normalized.longitude / step) * step;
      const key = `${keyLat}:${keyLon}`;
      const bucket = buckets.get(key) || { count: 0, lat: 0, lon: 0, magnitude: 0, confidence: 0, items: [] };
      bucket.count += 1;
      bucket.lat += normalized.latitude;
      bucket.lon += normalized.longitude;
      bucket.magnitude = Math.max(bucket.magnitude, normalized.magnitude || 0);
      bucket.confidence = Math.max(bucket.confidence, normalized.confidence || 0);
      bucket.items.push(normalized);
      buckets.set(key, bucket);
    }

    return [...buckets.entries()].map(([key, bucket]) => {
      const latitude = bucket.lat / bucket.count;
      const longitude = bucket.lon / bucket.count;
      const magnitude = bucket.magnitude || 0;
      return {
        id: `quake-cluster:${key}`,
        type: "earthquake",
        latitude,
        longitude,
        magnitude,
        intensity: magnitude,
        status: "clustered",
        confidence: bucket.confidence,
        label: `${bucket.count} events`,
        lastUpdated: bucket.items[0]?.lastUpdated,
        size: Math.min(24, 8 + bucket.count * 1.8),
        color: this.earthquakeColor(magnitude),
        outlineColor: Cesium.Color.WHITE
      };
    });
  }

  normalizeEarthquake(eq) {
    const latitude = Number(eq.latitude ?? eq.lat ?? eq.geometry?.coordinates?.[1] ?? 0);
    const longitude = Number(eq.longitude ?? eq.lon ?? eq.geometry?.coordinates?.[0] ?? 0);
    const magnitude = Number(eq.magnitude ?? eq.mag ?? eq.properties?.mag ?? 0);
    const status = eq.status || eq.properties?.status || "unreviewed";
    const confidence = Number(eq.confidence ?? eq.properties?.confidence ?? 0);
    const depth = Number(eq.depth_km ?? eq.depth ?? eq.geometry?.coordinates?.[2] ?? 0);
    const time = eq.time_utc || eq.time || eq.properties?.time;
    return {
      id: eq.id || eq.event_id || `${latitude}:${longitude}:${time || magnitude}`,
      type: "earthquake",
      latitude,
      longitude,
      magnitude,
      intensity: eq.intensity,
      status,
      confidence,
      label: eq.region || eq.place || eq.location || "Unknown region",
      lastUpdated: time,
      depth,
      size: this.earthquakeSize(magnitude),
      color: this.earthquakeColor(magnitude),
      outlineColor: Cesium.Color.WHITE
    };
  }

  stationSize(station) {
    const status = String(station.status || station.health || "unknown").toLowerCase();
    const noise = Number(station.noise_level || 0);
    if (status === "triggering") return 13;
    if (status === "offline") return 7;
    if (status === "delayed") return 9;
    if (status === "unknown") return 8;
    if (noise >= 65) return 12;
    if (noise >= 40) return 10;
    return 9;
  }

  stationColor(station) {
    const status = String(station.status || station.health || "unknown").toLowerCase();
    if (status === "offline") return Cesium.Color.fromCssColorString("#8b949e").withAlpha(0.35);
    if (status === "delayed") return Cesium.Color.fromCssColorString("#ffb347").withAlpha(0.88);
    if (status === "triggering") return Cesium.Color.fromCssColorString("#ff6b42");
    if (status === "unknown") return Cesium.Color.fromCssColorString("#aeb8c2").withAlpha(0.7);
    const noise = Number(station.noise_level || 0);
    if (noise < 20) return Cesium.Color.fromCssColorString("#00ffd1");
    if (noise < 40) return Cesium.Color.fromCssColorString("#7dff5e");
    if (noise < 65) return Cesium.Color.fromCssColorString("#ffd45e");
    return Cesium.Color.fromCssColorString("#ff3d5e");
  }

  earthquakeSize(magnitude) {
    if (magnitude >= 7) return 24;
    if (magnitude >= 6) return 18;
    if (magnitude >= 5) return 14;
    return 10;
  }

  earthquakeColor(magnitude) {
    if (magnitude >= 7) return Cesium.Color.fromCssColorString("#ff3d5e");
    if (magnitude >= 6) return Cesium.Color.fromCssColorString("#ff8d3d");
    if (magnitude >= 5) return Cesium.Color.fromCssColorString("#ffd45e");
    return Cesium.Color.fromCssColorString("#28a7ff");
  }

  cameraHeight() {
    return this.viewer.camera.positionCartographic?.height || 0;
  }

  _onMove(movement) {
    const picked = this.viewer.scene.pick(movement.endPosition);
    const marker = picked && picked.primitive && picked.primitive._markerData ? picked.primitive._markerData : null;
    if (!marker) {
      if (this.hoverTooltip) this.hoverTooltip.style.display = "none";
      return;
    }

    if (this.hoverTooltip) {
      this.hoverTooltip.style.left = `${movement.endPosition.x + 16}px`;
      this.hoverTooltip.style.top = `${movement.endPosition.y + 16}px`;
      this.hoverTooltip.style.display = "block";
      this.hoverTooltip.innerHTML = this.tooltipHtml(marker);
    }
  }

  _onClick(click) {
    const picked = this.viewer.scene.pick(click.position);
    const primitiveMarker = picked && picked.primitive && picked.primitive._markerData ? picked.primitive._markerData : null;
    const entity = picked && picked.id ? picked.id : null;
    const entityEventData = entity && entity._eventData ? entity._eventData : null;
    const legacyMarker = entityEventData ? {
      id: entity.id || entityEventData.id || `quake:${entityEventData.lat}:${entityEventData.lon}`,
      type: "earthquake",
      latitude: entityEventData.lat ?? entityEventData.latitude,
      longitude: entityEventData.lon ?? entityEventData.longitude,
      magnitude: entityEventData.mag ?? entityEventData.magnitude,
      depth: entityEventData.depth ?? entityEventData.depth_km,
      status: entityEventData.status,
      confidence: entityEventData.confidence,
      label: entityEventData.label || entityEventData.place || "Earthquake",
      place: entityEventData.place || entityEventData.label || "Unknown region",
      source: entityEventData.source || entityEventData.sources || "USGS",
      intensity: entityEventData.intensity ?? entityEventData.mmi ?? entityEventData.cdi,
      lastUpdated: entityEventData.time || entityEventData.lastUpdated
    } : null;
    const marker = primitiveMarker || legacyMarker;
    if (!marker) {
      console.log("_onClick: no marker found. picked:", picked, "primitiveMarker:", primitiveMarker, "legacyMarker:", legacyMarker);
      return;
    }

    const now = Date.now();
    const isDouble = this.lastClick.id === marker.id && now - this.lastClick.time < 350;
    this.lastClick = { id: marker.id, time: now };

    const telemetry = document.getElementById("telemetry");
    const statusText = document.getElementById("statusText");
    const infoHtml = this.tooltipHtml(marker, true);
    console.log("_onClick: updating marker", marker.label, "telemetry:", !!telemetry, "statusText:", !!statusText);
    if (telemetry) telemetry.innerHTML = infoHtml;
    if (statusText) statusText.innerHTML = `<span class="ok">Earthquake</span> · ${infoHtml.replace(/<br>/g, ' · ')}`;

    if (marker.type === "earthquake" && typeof drawWaves === "function") {
      const event = this.data.earthquakes.find(item => (item.id || item.event_id) === marker.id) || marker;
      if (event) {
        selectedEventForWaves = {
          lat: event.latitude,
          lon: event.longitude,
          depth: event.depth || event.depth_km || 10,
          mag: event.magnitude || 0,
          place: event.label || event.region || event.place || "Unknown",
          time: event.lastUpdated || event.time || event.time_utc
        };
        drawWaves(selectedEventForWaves);
      }
    }

    if (isDouble && marker.type === "earthquake") {
      this.focusMarker(marker);
    }
  }

  _onDoubleClick(click) {
    const picked = this.viewer.scene.pick(click.position);
    const marker = picked && picked.primitive && picked.primitive._markerData ? picked.primitive._markerData : null;
    if (marker && marker.type === "earthquake") {
      this.focusMarker(marker);
    }
  }

  focusMarker(marker) {
    this.viewer.camera.flyTo({
      destination: Cesium.Cartesian3.fromDegrees(marker.longitude, marker.latitude, 2200000),
      duration: 1.1
    });
  }

  tooltipHtml(marker, full = false) {
    if (marker.type === "station") {
      const channels = Array.isArray(marker.channels) ? marker.channels.join(", ") : "N/A";
      return `<b>${marker.code || marker.label || "Station"}</b><br>Name: ${marker.name || "N/A"}<br>Network: ${marker.network || "N/A"}<br>Channels: ${channels}<br>Status: ${marker.status || "unknown"}<br>Last seen: ${marker.lastUpdated || "N/A"}<br>Noise: ${marker.noise_level ?? "N/A"}${full ? `<br>Country: ${marker.country || "N/A"}<br>Region: ${marker.region || "N/A"}<br>Provider: ${marker.provider || "N/A"}` : ""}`;
    }

    if (marker.type === "alert") {
      return `<b>${marker.label || "Alert"}</b><br>Status: ${marker.status || "automatic"}<br>Confidence: ${marker.confidence ?? "N/A"}`;
    }

    const place = marker.place || marker.label || "Unknown region";
    const source = marker.source || marker.sources || "USGS";
    const intensity = marker.intensity != null ? `Intensity: ${Number(marker.intensity).toFixed(1)}` : "";
    return `<b>${marker.label || "Earthquake"}</b><br>${place}<br>M${Number(marker.magnitude || 0).toFixed(1)} · Depth ${marker.depth ?? marker.depth_km ?? "N/A"} km<br>Status: ${marker.status || "unreviewed"}<br>Confidence: ${marker.confidence ?? "N/A"}${full ? `<br>Time: ${marker.lastUpdated || "N/A"}<br>Source: ${source}${intensity ? `<br>${intensity}` : ""}` : intensity ? `<br>${intensity}` : ""}`;
  }
}

window.OpenSeismoGlobeView = OpenSeismoGlobeView;