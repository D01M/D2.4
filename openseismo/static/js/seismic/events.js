/**
 * Earthquake Monitor - Real-time earthquake monitoring and alerts (3D Globe Version)
 */

class EarthquakeMonitor {
  constructor(globe) {
    this.globe = globe || window.globe3d;
    this.earthquakes = [];
    this.updateInterval = 60000; // 1 minute
    this.updateTimer = null;
    this.minMagnitude = 4.0;
    this.selectedEarthquake = null;
    this.selectedEarthquakeId = null;
  }

  async init() {
    this.bindSelectionEvents();
    await this.update();
    this.startPolling();
    console.log('EarthquakeMonitor initialized with 3D Globe');
  }

  async update() {
    try {
      const data = await API.getEarthquakesCurrent();
      this.earthquakes = data.data || [];
      this.render();
    } catch (err) {
      console.error('Failed to fetch earthquakes:', err);
    }
  }

  render() {
    if (!this.globe) {
      console.warn('Globe not initialized');
      return;
    }

    // Clear previous markers
    this.globe.clear();
    
    // Add markers for each earthquake
    for (const eq of this.earthquakes) {
      if ((eq.magnitude || 0) >= this.minMagnitude) {
        this.globe.addEarthquakeMarker(eq.latitude, eq.longitude, eq.magnitude);
      }
    }

    // Update UI
    this.updateStats();
    this.updateList();
    this.updateLiveDetections();
    this.renderSelectedEarthquake();
  }

  updateStats() {
    const count = this.earthquakes.length;
    const highMag = this.earthquakes.filter(e => e.magnitude >= 6).length;
    
    const countEl = document.getElementById('eq-count');
    const alertEl = document.getElementById('eq-alert');
    
    if (countEl) countEl.textContent = count;
    if (alertEl) {
      if (highMag > 0) {
        alertEl.textContent = 'HIGH ACTIVITY';
        alertEl.style.color = '#ff6464';
      } else {
        alertEl.textContent = 'Normal';
        alertEl.style.color = '#00ff99';
      }
    }
  }

  updateList() {
    const listEl = document.getElementById('earthquake-list');
    if (!listEl) return;

    const filtered = this.earthquakes.filter(eq => (eq.magnitude || 0) >= this.minMagnitude);
    
    if (filtered.length === 0) {
      listEl.innerHTML = '<div class="empty-state">No earthquakes above threshold</div>';
      return;
    }

    const sorted = filtered.sort((a, b) => b.magnitude - a.magnitude);
    listEl.innerHTML = sorted.map((eq) => {
      const mag = (eq.magnitude || 0).toFixed(1);
      const location = eq.location || `${eq.latitude.toFixed(2)}°N, ${eq.longitude.toFixed(2)}°E`;
      const eventMeta = this.getEventStatusText(eq);
      const eqId = this.getEarthquakeIdentity(eq);
      const isSelected = this.isSelectedEarthquake(eq);
      let levelClass = 'low';
      if (eq.magnitude >= 7) levelClass = 'critical';
      else if (eq.magnitude >= 6) levelClass = 'high';
      else if (eq.magnitude >= 5) levelClass = 'moderate';
      
      return `<div class="earthquake-item ${levelClass}${isSelected ? ' selected' : ''}" data-eq-id="${eqId.replace(/"/g, '&quot;')}">
        <span class="magnitude">M${mag}</span> 
        <strong>${location}</strong>
        <div class="event-meta">${eventMeta}</div>
        <div class="meta">Depth: ${(eq.depth_km || 0).toFixed(1)} km</div>
      </div>`;
    }).join('');

    // Update last updated time
    const lastEl = document.getElementById('last-updated');
    if (lastEl) lastEl.textContent = new Date().toLocaleTimeString();
  }

  updateLiveDetections() {
    const listEl = document.getElementById('live-detection-list');
    if (!listEl) return;

    const detections = this.earthquakes
      .filter(eq => !this.isConfirmedEarthquake(eq))
      .sort((a, b) => this.getEventTimeValue(b) - this.getEventTimeValue(a));

    if (detections.length === 0) {
      listEl.innerHTML = '<div class="empty-state">No live detections.</div>';
      return;
    }

    listEl.innerHTML = detections.map(eq => {
      const station = this.getDetectionSourceName(eq);
      const detectionTime = this.getDetectionTimeText(eq);
      const signalStrength = this.getDetectionSignalText(eq);
      const status = this.getDetectionStatus(eq);
      const eqId = this.getEarthquakeIdentity(eq);
      const isSelected = this.isSelectedEarthquake(eq);

      return `<div class="earthquake-item moderate live-detection-item${isSelected ? ' selected' : ''}" data-eq-id="${eqId.replace(/"/g, '&quot;')}">
        <strong>${station}</strong>
        <div class="event-meta">${detectionTime}${signalStrength ? ` · ${signalStrength}` : ''} · Status: ${status}</div>
        <div class="warning-text">Automatic detection. Not an official earthquake report.</div>
      </div>`;
    }).join('');
  }

  bindSelectionEvents() {
    window.addEventListener('earthquakeSelected', (event) => {
      const selectedEvent = this.findEarthquakeByCoordinates(event.detail);
      if (selectedEvent) {
        this.selectEarthquake(selectedEvent);
      }
    });

    document.addEventListener('click', (event) => {
      const selectedItem = event.target.closest('.earthquake-item[data-eq-id]');
      if (!selectedItem) return;

      const eqId = selectedItem.getAttribute('data-eq-id');
      const eq = this.getEarthquakeById(eqId);
      if (eq) {
        this.selectEarthquake(eq);
      }
    });
  }

  selectEarthquake(event) {
    this.selectedEarthquake = event;
    this.selectedEarthquakeId = this.getEarthquakeIdentity(event);
    this.renderSelectedEarthquake();
    this.updateList();
    this.updateLiveDetections();
  }

  renderSelectedEarthquake() {
    const panel = document.getElementById('earthquake-detail-panel');
    const content = document.getElementById('earthquake-detail-content');
    if (!panel || !content) return;

    if (!this.selectedEarthquake) {
      panel.style.display = 'none';
      content.innerHTML = '<div class="empty-state">Select an earthquake to view details.</div>';
      return;
    }

    panel.style.display = 'block';
    const eq = this.selectedEarthquake;
    const mag = (eq.magnitude || 0).toFixed(1);
    const location = eq.location || `${eq.latitude.toFixed(2)}°N, ${eq.longitude.toFixed(2)}°E`;
    const timeText = this.getEventTimeText(eq);
    const statusText = this.getEventStatusText(eq);
    const depth = (eq.depth_km || 0).toFixed(1);
    const sourceCount = this.getEventSourceCount(eq);

    content.innerHTML = `
      <div class="detail-hero">
        <div class="detail-badge">M${mag}</div>
        <h3>${location}</h3>
      </div>
      <div class="detail-grid">
        <div class="detail-row"><span>Time</span><strong>${timeText}</strong></div>
        <div class="detail-row"><span>Status</span><strong>${statusText}</strong></div>
        <div class="detail-row"><span>Depth</span><strong>${depth} km</strong></div>
        <div class="detail-row"><span>Sources</span><strong>${sourceCount} source${sourceCount === 1 ? '' : 's'}</strong></div>
        <div class="detail-row"><span>Coordinates</span><strong>${eq.latitude.toFixed(2)}°, ${eq.longitude.toFixed(2)}°</strong></div>
      </div>
    `;
  }

  getEarthquakeById(eqId) {
    if (!eqId) return null;
    return this.earthquakes.find(eq => this.getEarthquakeIdentity(eq) === eqId) || null;
  }

  findEarthquakeByCoordinates(detail) {
    if (!detail) return null;

    const targetLat = Number(detail.latitude);
    const targetLon = Number(detail.longitude);
    const targetMag = Number(detail.magnitude);

    return this.earthquakes.find(eq => {
      const eqLat = Number(eq.latitude);
      const eqLon = Number(eq.longitude);
      const eqMag = Number(eq.magnitude);
      return eqLat.toFixed(2) === targetLat.toFixed(2)
        && eqLon.toFixed(2) === targetLon.toFixed(2)
        && eqMag.toFixed(1) === targetMag.toFixed(1);
    }) || null;
  }

  getEarthquakeIdentity(event) {
    const id = event?.id || event?.event_id || event?.code || event?.publicid || event?.public_id;
    if (id) return String(id);

    const latitude = Number(event?.latitude || 0).toFixed(2);
    const longitude = Number(event?.longitude || 0).toFixed(2);
    const magnitude = Number(event?.magnitude || 0).toFixed(1);
    const location = String(event?.location || '').trim();
    return `${latitude}:${longitude}:${magnitude}:${location}`;
  }

  isSelectedEarthquake(event) {
    return this.selectedEarthquakeId && this.getEarthquakeIdentity(event) === this.selectedEarthquakeId;
  }

  getEventTimeText(event) {
    const value = event?.time_utc || event?.updated || event?.updated_at || event?.last_updated || event?.lastUpdate;
    if (!value) return 'Time unknown';

    const date = new Date(value);
    if (Number.isNaN(date.getTime())) return 'Time unknown';

    return date.toLocaleString([], {
      month: 'short',
      day: 'numeric',
      hour: 'numeric',
      minute: '2-digit'
    });
  }

  isConfirmedEarthquake(event) {
    return event?.reviewed === true || String(event?.status || '').toLowerCase().includes('reviewed') || String(event?.status || '').toLowerCase().includes('confirmed');
  }

  getDetectionSourceName(event) {
    return event?.station_name || event?.station || event?.source_name || event?.source || 'Automatic detector';
  }

  getDetectionTimeText(event) {
    const value = event?.time_utc || event?.updated || event?.updated_at || event?.last_updated || event?.lastUpdate;
    if (!value) return 'Time unknown';

    const date = new Date(value);
    if (Number.isNaN(date.getTime())) return 'Time unknown';

    return date.toLocaleTimeString([], { hour: 'numeric', minute: '2-digit' });
  }

  getDetectionSignalText(event) {
    const signal = event?.signal_strength ?? event?.signal ?? event?.amplitude ?? event?.magnitude;
    if (signal === undefined || signal === null || signal === '') return '';

    const numeric = Number(signal);
    if (Number.isFinite(numeric)) {
      return `Signal ${numeric.toFixed(1)}`;
    }

    return `Signal ${signal}`;
  }

  getDetectionStatus(event) {
    const status = String(event?.status || '').toLowerCase();

    if (event?.reviewed === true || status.includes('confirmed') || status.includes('reviewed')) {
      return 'Confirmed';
    }

    if (status.includes('dismiss')) {
      return 'Dismissed';
    }

    const sourceCount = this.getEventSourceCount(event);
    if (sourceCount >= 2 || Array.isArray(event?.sources) && event.sources.length >= 2) {
      return 'Reviewing';
    }

    return 'Detecting';
  }

  getEventTimeValue(event) {
    const value = event?.time_utc || event?.updated || event?.updated_at || event?.last_updated || event?.lastUpdate;
    const timestamp = new Date(value || 0).getTime();
    return Number.isFinite(timestamp) ? timestamp : 0;
  }

  getEventStatusText(event) {
    const reviewed = event?.reviewed === true || String(event?.status || '').toLowerCase().includes('reviewed');
    const sourceCount = this.getEventSourceCount(event);
    const updatedText = this.getEventUpdatedText(event);

    let status = '🔴 Automatic / single-source';
    if (reviewed) {
      status = '🟢 Reviewed';
    } else if (sourceCount >= 2) {
      status = '🟡 Multi-source preliminary';
    }

    const parts = [status, `${sourceCount} source${sourceCount === 1 ? '' : 's'}`];
    if (updatedText) {
      parts.push(`Updated ${updatedText}`);
    }

    return parts.join(' · ');
  }

  getEventSourceCount(event) {
    const sourceCount = Number(event?.source_count);
    if (Number.isFinite(sourceCount) && sourceCount > 0) {
      return sourceCount;
    }

    if (Array.isArray(event?.sources)) {
      return event.sources.length;
    }

    return 1;
  }

  getEventUpdatedText(event) {
    const updatedAt = event?.updated || event?.updated_at || event?.last_updated || event?.lastUpdate;
    if (!updatedAt) return '';

    const date = new Date(updatedAt);
    if (Number.isNaN(date.getTime())) return '';

    return date.toLocaleTimeString([], { hour: 'numeric', minute: '2-digit' });
  }

  startPolling() {
    this.updateTimer = setInterval(() => this.update(), this.updateInterval);
  }

  stopPolling() {
    if (this.updateTimer) {
      clearInterval(this.updateTimer);
      this.updateTimer = null;
    }
  }

  setMinMagnitude(value) {
    this.minMagnitude = parseFloat(value);
    this.render();
  }

  getSignificantEarthquakes() {
    return this.earthquakes.filter(eq => eq.magnitude >= 4.0);
  }

  getAlerts() {
    return this.earthquakes.filter(eq => eq.magnitude >= 5.0);
  }
}
