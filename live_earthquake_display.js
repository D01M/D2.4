/**
 * Live Earthquake Detection and ShakeMax Hexagon Visualization
 * Real-time earthquake monitoring with ShakeMax intensity hexagons
 * Similar to GlobalQuake but integrated into OpenSeismo Lite
 */

class LiveEarthquakeDisplay {
    constructor(map) {
        this.map = map;
        this.earthquakes = [];
        this.hexagonLayers = {}; // Store hexagon layers by earthquake ID
        this.earthquakeMarkers = {};
        this.selectedEarthquake = null;
        this.updateInterval = 10000; // Update every 10 seconds
        this.isRunning = false;
        
        // ShakeMax level definitions
        this.shakemaxLevels = [
            { min: 0, max: 1, color: "#ffffff", label: "No Damage" },
            { min: 1, max: 2, color: "#ccccff", label: "Very Light" },
            { min: 2, max: 3, color: "#99ccff", label: "Light" },
            { min: 3, max: 4, color: "#66ccff", label: "Moderate" },
            { min: 4, max: 5, color: "#00ccff", label: "Moderate-Strong" },
            { min: 5, max: 6, color: "#ffff00", label: "Strong" },
            { min: 6, max: 7, color: "#ffcc00", label: "Very Strong" },
            { min: 7, max: 8, color: "#ff9900", label: "Severe" },
            { min: 8, max: 9, color: "#ff6600", label: "Violent" },
            { min: 9, max: 10, color: "#ff3300", label: "Extreme" },
            { min: 10, max: 12, color: "#cc0000", label: "Catastrophic" },
        ];
    }

    /**
     * Start live earthquake monitoring
     */
    async start() {
        if (this.isRunning) return;
        this.isRunning = true;
        console.log("Live earthquake monitoring started");
        
        // Initial fetch
        await this.updateEarthquakes();
        
        // Continuous updates
        this.updateTimer = setInterval(() => this.updateEarthquakes(), this.updateInterval);
    }

    /**
     * Stop live earthquake monitoring
     */
    stop() {
        if (this.updateTimer) {
            clearInterval(this.updateTimer);
        }
        this.isRunning = false;
        console.log("Live earthquake monitoring stopped");
    }

    /**
     * Fetch and update live earthquakes
     */
    async updateEarthquakes() {
        try {
            const response = await fetch('/api/earthquakes/live?magnitude_filter=4.5&enrich=true');
            if (!response.ok) throw new Error(`HTTP ${response.status}`);
            
            const data = await response.json();
            if (data.status !== 'success') throw new Error(data.error);
            
            const newEarthquakes = data.earthquakes || [];
            
            // Check for new earthquakes (not in current list)
            const oldIds = new Set(this.earthquakes.map(e => e.id));
            const newIds = new Set(newEarthquakes.map(e => e.id));
            
            // New earthquakes detected
            for (const eq of newEarthquakes) {
                if (!oldIds.has(eq.id)) {
                    this.onEarthquakeDetected(eq);
                }
            }
            
            // Update the list
            this.earthquakes = newEarthquakes;
            this.updateEarthquakeList();
            
        } catch (error) {
            console.error("Error updating earthquakes:", error);
        }
    }

    /**
     * Called when a new earthquake is detected
     */
    onEarthquakeDetected(earthquake) {
        console.log(`🌍 NEW EARTHQUAKE DETECTED: M${earthquake.magnitude} at ${earthquake.place}`);
        
        // Play notification sound (if available)
        this.playNotificationSound();
        
        // Add visual alert
        this.showDetectionAlert(earthquake);
        
        // Display hexagons and marker
        this.displayEarthquake(earthquake);
    }

    /**
     * Display earthquake on map with marker and hexagons
     */
    displayEarthquake(earthquake) {
        const eqId = earthquake.id;
        
        // Create earthquake marker at epicenter
        const marker = L.circleMarker([earthquake.latitude, earthquake.longitude], {
            radius: Math.min(earthquake.magnitude * 2, 20),
            fillColor: earthquake.shakemax_color,
            color: '#ffffff',
            weight: 2,
            opacity: 0.9,
            fillOpacity: 0.8,
            className: 'earthquake-marker'
        }).addTo(this.map);
        
        // Popup with earthquake info
        marker.bindPopup(this.createEarthquakePopup(earthquake));
        marker.on('click', () => this.selectEarthquake(earthquake));
        
        this.earthquakeMarkers[eqId] = marker;
        
        // Add hexagon layer
        this.displayHexagons(earthquake);
    }

    /**
     * Display ShakeMax hexagons around epicenter
     */
    displayHexagons(earthquake) {
        const eqId = earthquake.id;
        
        // Remove old hexagons if they exist
        if (this.hexagonLayers[eqId]) {
            this.map.removeLayer(this.hexagonLayers[eqId]);
        }
        
        if (!earthquake.hexagons || earthquake.hexagons.length === 0) {
            return;
        }
        
        // Create feature group for hexagons
        const hexagons = L.featureGroup();
        
        // Add each hexagon
        for (const hex of earthquake.hexagons) {
            // Create hexagon polygon (approximate as circle for simplicity, could be improved)
            const hexRadius = hex.size_km / 111.0; // Convert km to degrees
            
            const circle = L.circleMarker([hex.latitude, hex.longitude], {
                radius: 6,
                fillColor: hex.color,
                color: 'rgba(0, 0, 0, 0.3)',
                weight: 1,
                opacity: 0.7,
                fillOpacity: 0.6,
                className: 'shakemax-hexagon'
            });
            
            // Add hover info
            circle.bindTooltip(
                `<strong>ShakeMax ${hex.shakemax}</strong><br/>` +
                `${hex.intensity_label}<br/>` +
                `Distance: ${hex.distance_km} km`,
                { permanent: false, sticky: true }
            );
            
            hexagons.addLayer(circle);
        }
        
        // Add to map and store reference
        hexagons.addTo(this.map);
        this.hexagonLayers[eqId] = hexagons;
    }

    /**
     * Create popup HTML for earthquake marker
     */
    createEarthquakePopup(earthquake) {
        const timeAgo = earthquake.time_ago || 'Unknown';
        const tsunami = earthquake.tsunami ? '⚠️ TSUNAMI THREAT' : 'No tsunami';
        const felt = earthquake.felt_reports > 0 ? 
            `<br/>👥 ${earthquake.felt_reports} felt reports` : '';
        
        return `
            <div style="font-size: 12px; min-width: 200px;">
                <strong style="font-size: 14px; color: #60a5fa;">M${earthquake.magnitude}</strong>
                <br/><strong>${earthquake.place}</strong>
                <hr style="margin: 8px 0; border: none; border-top: 1px solid #ccc;">
                <div style="font-size: 11px;">
                    <span>📍 ${earthquake.latitude.toFixed(2)}°, ${earthquake.longitude.toFixed(2)}°</span><br/>
                    <span>🔍 Depth: ${earthquake.depth_km.toFixed(1)} km</span><br/>
                    <span>⏱️ ${timeAgo}</span>
                    ${felt}
                    <br/><span style="color: ${earthquake.shakemax_color}; font-weight: bold;">
                        🌊 ShakeMax: ${earthquake.shakemax_epicenter} - ${earthquake.shakemax_level.label}
                    </span>
                    <br/><span style="color: ${tsunami === 'No tsunami' ? '#22c55e' : '#dc2626'};">
                        ${tsunami}
                    </span>
                </div>
            </div>
        `;
    }

    /**
     * Select an earthquake to highlight
     */
    selectEarthquake(earthquake) {
        this.selectedEarthquake = earthquake;
        
        // Highlight marker
        if (this.earthquakeMarkers[earthquake.id]) {
            const marker = this.earthquakeMarkers[earthquake.id];
            marker.setStyle({
                weight: 3,
                fillOpacity: 1
            });
        }
        
        // Center map on earthquake
        this.map.setView([earthquake.latitude, earthquake.longitude], 7);
        
        // Update detail panel
        this.showEarthquakeDetails(earthquake);
    }

    /**
     * Show detailed earthquake information
     */
    showEarthquakeDetails(earthquake) {
        const detailPanel = document.getElementById('detail-panel');
        if (!detailPanel) return;
        
        const faultType = earthquake.fault_type || 'Unknown';
        const tsunami = earthquake.tsunami ? 
            '<span style="color: #dc2626; font-weight: bold;">⚠️ TSUNAMI THREAT</span>' : 
            '<span style="color: #22c55e;">✓ No tsunami threat</span>';
        
        detailPanel.innerHTML = `
            <div style="padding: 14px; height: 100%; overflow-y: auto; background: #0b1627;">
                <div style="margin-bottom: 12px;">
                    <div style="font-size: 24px; font-weight: bold; color: ${earthquake.shakemax_color};">
                        M${earthquake.magnitude}
                    </div>
                    <div style="font-size: 12px; color: #94a3b8; margin-top: 4px;">
                        ${earthquake.place}
                    </div>
                </div>
                
                <hr style="border: none; border-top: 1px solid #1f334d; margin: 12px 0;">
                
                <div style="font-size: 11px; line-height: 1.8;">
                    <div><strong>Location:</strong></div>
                    <div style="color: #cbd5e1;">
                        ${earthquake.latitude.toFixed(3)}°, ${earthquake.longitude.toFixed(3)}°
                    </div>
                    
                    <div style="margin-top: 8px;"><strong>Depth:</strong></div>
                    <div style="color: #cbd5e1;">${earthquake.depth_km.toFixed(1)} km</div>
                    
                    <div style="margin-top: 8px;"><strong>Time:</strong></div>
                    <div style="color: #cbd5e1;">${earthquake.time_ago}</div>
                    
                    <div style="margin-top: 8px;"><strong>Fault Type:</strong></div>
                    <div style="color: #cbd5e1;">${faultType}</div>
                    
                    <div style="margin-top: 8px;"><strong>ShakeMax (Epicenter):</strong></div>
                    <div style="color: ${earthquake.shakemax_color}; font-weight: bold;">
                        ${earthquake.shakemax_epicenter} - ${earthquake.shakemax_level.label}
                    </div>
                    
                    <div style="margin-top: 8px;"><strong>Tsunami Risk:</strong></div>
                    <div style="margin-top: 4px;">${tsunami}</div>
                    
                    <div style="margin-top: 8px;"><strong>Hexagon Grid:</strong></div>
                    <div style="color: #cbd5e1;">${earthquake.hexagons ? earthquake.hexagons.length : 0} zones mapped</div>
                    
                    ${earthquake.felt_reports > 0 ? `
                        <div style="margin-top: 8px;"><strong>Felt Reports:</strong></div>
                        <div style="color: #cbd5e1;">👥 ${earthquake.felt_reports}</div>
                    ` : ''}
                </div>
                
                <button onclick="LiveEarthquakeDisplay.instance.copyEarthquakeData('${earthquake.id}')" 
                        style="width: 100%; margin-top: 12px; padding: 8px; background: #1f334d; border: 1px solid #334155; color: #e5eefc; border-radius: 6px; cursor: pointer; font-size: 11px;">
                    Copy Data
                </button>
            </div>
        `;
    }

    /**
     * Update the live earthquake list display
     */
    updateEarthquakeList() {
        const listPanel = document.getElementById('earthquake-list');
        if (!listPanel) return;
        
        if (this.earthquakes.length === 0) {
            listPanel.innerHTML = '<div style="padding: 14px; color: #94a3b8; font-size: 12px;">No earthquakes detected yet. Monitoring active...</div>';
            return;
        }
        
        let html = `<div style="padding: 14px;">
            <div style="font-size: 13px; font-weight: bold; margin-bottom: 12px; color: #60a5fa;">
                LIVE EARTHQUAKES (${this.earthquakes.length})
            </div>`;
        
        for (const eq of this.earthquakes.slice(0, 10)) { // Show top 10
            const isSelected = this.selectedEarthquake && this.selectedEarthquake.id === eq.id;
            const bgColor = isSelected ? '#1f334d' : 'transparent';
            
            html += `
                <div onclick="LiveEarthquakeDisplay.instance.selectEarthquake(this.dataset)" 
                     data-id="${eq.id}" 
                     data-latitude="${eq.latitude}"
                     data-longitude="${eq.longitude}"
                     data-magnitude="${eq.magnitude}"
                     data-depth_km="${eq.depth_km}"
                     data-place="${eq.place}"
                     data-time_utc="${eq.time_utc}"
                     data-time_ago="${eq.time_ago}"
                     data-shakemax_epicenter="${eq.shakemax_epicenter}"
                     data-shakemax_color="${eq.shakemax_color}"
                     data-tsunami="${eq.tsunami}"
                     data-felt_reports="${eq.felt_reports}"
                     style="background: ${bgColor}; padding: 10px; margin-bottom: 8px; border: 1px solid #334155; border-radius: 6px; cursor: pointer; transition: background 0.2s;"
                     onmouseover="this.style.background='#1f334d'" 
                     onmouseout="this.style.background='${bgColor}'">
                    <div style="display: flex; justify-content: space-between; align-items: center;">
                        <div style="flex: 1;">
                            <div style="font-weight: bold; color: ${eq.shakemax_color};">
                                M${eq.magnitude.toFixed(1)}
                            </div>
                            <div style="font-size: 11px; color: #cbd5e1; margin-top: 2px;">
                                ${eq.place}
                            </div>
                            <div style="font-size: 10px; color: #94a3b8; margin-top: 4px;">
                                ${eq.depth_km.toFixed(1)} km · ${eq.time_ago}
                            </div>
                        </div>
                        <div style="text-align: right; margin-left: 8px;">
                            <div style="background: ${eq.shakemax_color}; color: #000; padding: 4px 8px; border-radius: 4px; font-size: 11px; font-weight: bold;">
                                ${eq.shakemax_epicenter.toFixed(1)}
                            </div>
                            ${eq.tsunami ? '<div style="color: #dc2626; font-size: 10px; margin-top: 4px;">⚠️ TSUNAMI</div>' : ''}
                        </div>
                    </div>
                </div>
            `;
        }
        
        if (this.earthquakes.length > 10) {
            html += `<div style="color: #94a3b8; font-size: 11px; padding: 8px; text-align: center;">+${this.earthquakes.length - 10} more earthquakes</div>`;
        }
        
        html += '</div>';
        listPanel.innerHTML = html;
    }

    /**
     * Show a detection alert notification
     */
    showDetectionAlert(earthquake) {
        const alertDiv = document.createElement('div');
        alertDiv.style.cssText = `
            position: fixed;
            top: 80px;
            right: 20px;
            background: ${earthquake.shakemax_color};
            color: #000;
            padding: 16px 20px;
            border-radius: 8px;
            font-weight: bold;
            z-index: 10000;
            box-shadow: 0 10px 30px rgba(0, 0, 0, 0.5);
            animation: slideIn 0.3s ease-out;
        `;
        
        alertDiv.innerHTML = `
            🌍 EARTHQUAKE DETECTED<br/>
            M${earthquake.magnitude} - ${earthquake.place}
        `;
        
        document.body.appendChild(alertDiv);
        
        // Remove after 5 seconds
        setTimeout(() => {
            alertDiv.style.animation = 'slideOut 0.3s ease-in';
            setTimeout(() => alertDiv.remove(), 300);
        }, 5000);
    }

    /**
     * Play notification sound
     */
    playNotificationSound() {
        // Simple beep using Web Audio API
        try {
            const audioContext = new (window.AudioContext || window.webkitAudioContext)();
            const oscillator = audioContext.createOscillator();
            const gain = audioContext.createGain();
            
            oscillator.connect(gain);
            gain.connect(audioContext.destination);
            
            oscillator.frequency.value = 800;
            oscillator.type = 'sine';
            
            gain.gain.setValueAtTime(0.3, audioContext.currentTime);
            gain.gain.exponentialRampToValueAtTime(0.01, audioContext.currentTime + 0.3);
            
            oscillator.start(audioContext.currentTime);
            oscillator.stop(audioContext.currentTime + 0.3);
        } catch (e) {
            // Audio not available, silent fail
        }
    }

    /**
     * Copy earthquake data to clipboard
     */
    copyEarthquakeData(eqId) {
        const eq = this.earthquakes.find(e => e.id === eqId);
        if (!eq) return;
        
        const text = `M${eq.magnitude} | ${eq.place} | Depth: ${eq.depth_km} km | ShakeMax: ${eq.shakemax_epicenter}`;
        navigator.clipboard.writeText(text).then(() => {
            alert('Earthquake data copied to clipboard');
        }).catch(() => {
            alert('Failed to copy data');
        });
    }

    /**
     * Get ShakeMax legend HTML
     */
    getShakemaxLegendHTML() {
        let html = '<div style="font-size: 11px;"><strong>ShakeMax Scale</strong><hr style="margin: 8px 0; border: none; border-top: 1px solid #ccc;">';
        
        for (const level of this.shakemaxLevels) {
            const mid = (level.min + level.max) / 2;
            html += `
                <div style="display: flex; align-items: center; margin-bottom: 6px;">
                    <div style="width: 20px; height: 20px; background: ${level.color}; border: 1px solid #666; border-radius: 3px; margin-right: 8px;"></div>
                    <div>${level.min}-${level.max} ${level.label}</div>
                </div>
            `;
        }
        
        html += '</div>';
        return html;
    }
}

// CSS for animations
const style = document.createElement('style');
style.textContent = `
    @keyframes slideIn {
        from {
            transform: translateX(400px);
            opacity: 0;
        }
        to {
            transform: translateX(0);
            opacity: 1;
        }
    }
    
    @keyframes slideOut {
        from {
            transform: translateX(0);
            opacity: 1;
        }
        to {
            transform: translateX(400px);
            opacity: 0;
        }
    }
    
    .earthquake-marker {
        cursor: pointer;
        transition: all 0.2s;
    }
    
    .earthquake-marker:hover {
        filter: brightness(1.2);
    }
    
    .shakemax-hexagon {
        cursor: pointer;
        transition: all 0.1s;
    }
    
    .shakemax-hexagon:hover {
        filter: brightness(1.1);
    }
`;
document.head.appendChild(style);
