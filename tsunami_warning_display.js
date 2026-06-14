/**
 * Tsunami Warning System Frontend Module
 * Handles visualization and display of tsunami warnings
 */

class TsunamiWarningDisplay {
    constructor() {
        this.warnings = [];
        this.warningMarkers = [];
        this.warningLayers = null;
    }
    
    /**
     * Get warning level color
     */
    getWarningColor(level) {
        const colors = {
            'MAJOR_WARNING': '#DC2626',    // Red
            'WARNING': '#EA580C',          // Orange-red
            'ADVISORY': '#F59E0B',         // Amber
            'NO_WARNING': '#10B981'        // Green
        };
        return colors[level] || '#6B7280';
    }
    
    /**
     * Get warning level description and icon
     */
    getWarningDescription(level) {
        const descriptions = {
            'MAJOR_WARNING': '🚨 MAJOR TSUNAMI WARNING',
            'WARNING': '⚠️ TSUNAMI WARNING',
            'ADVISORY': 'ℹ️ TSUNAMI ADVISORY',
            'NO_WARNING': '✓ No tsunami threat'
        };
        return descriptions[level] || 'Unknown';
    }
    
    /**
     * Create warning severity indicator
     */
    createWarningIndicator(level, waveHeight) {
        const indicator = document.createElement('div');
        indicator.className = 'tsunami-indicator';
        indicator.style.borderColor = this.getWarningColor(level);
        indicator.style.backgroundColor = this.getWarningColor(level) + '20';
        
        const severity = {
            'MAJOR_WARNING': 4,
            'WARNING': 3,
            'ADVISORY': 2,
            'NO_WARNING': 1
        };
        
        let dots = '';
        for (let i = 0; i < severity[level]; i++) {
            dots += '●';
        }
        
        indicator.innerHTML = `
            <div class="indicator-dots" style="color: ${this.getWarningColor(level)}">${dots}</div>
            <div class="indicator-text">
                <strong>${this.getWarningDescription(level)}</strong>
                <div class="wave-height">Max waves: ${waveHeight}m</div>
            </div>
        `;
        
        return indicator;
    }
    
    /**
     * Format and display tsunami warning in panel
     */
    displayTsunamiWarning(quakeData, tsunamiData) {
        const panel = document.createElement('div');
        panel.className = 'tsunami-warning-panel';
        
        if (!tsunamiData.has_risk) {
            panel.innerHTML = `
                <div class="tsunami-header" style="border-color: ${this.getWarningColor('NO_WARNING')}">
                    <h3>Tsunami Assessment</h3>
                    <span style="color: ${this.getWarningColor('NO_WARNING')}">${this.getWarningDescription('NO_WARNING')}</span>
                </div>
                <div class="tsunami-info">
                    <p>Earthquake magnitude ${tsunamiData.magnitude} at ${tsunamiData.depth_km}km depth</p>
                    <p>No significant tsunami threat detected for monitored regions.</p>
                </div>
            `;
        } else {
            let warningsList = '';
            const highestLevel = Math.max(...tsunamiData.warnings.map(w => w.warning_level_value));
            
            for (const warning of tsunamiData.warnings) {
                const isHighest = warning.warning_level_value === highestLevel;
                warningsList += `
                    <div class="warning-entry ${isHighest ? 'highest' : ''}">
                        <div class="warning-region">
                            <strong>${warning.region}</strong>
                            <span class="warning-badge" style="background: ${this.getWarningColor(warning.warning_level)}">
                                ${warning.warning_level.replace(/_/g, ' ')}
                            </span>
                        </div>
                        <div class="warning-details">
                            <div>📏 Distance: ${warning.distance_km} km</div>
                            <div>🌊 Wave height: ${warning.wave_height_m}m</div>
                            <div>⏱️ Arrival: ${warning.arrival_time_formatted}</div>
                        </div>
                    </div>
                `;
            }
            
            const maxWarning = tsunamiData.warnings[0];
            panel.innerHTML = `
                <div class="tsunami-header" style="border-color: ${this.getWarningColor(maxWarning.warning_level)}; background: ${this.getWarningColor(maxWarning.warning_level)}15">
                    <h3>${this.getWarningDescription(maxWarning.warning_level)}</h3>
                </div>
                <div class="tsunami-info">
                    <p><strong>Earthquake:</strong> M${tsunamiData.magnitude} at ${tsunamiData.depth_km}km depth</p>
                    <p><strong>Affected Regions:</strong></p>
                    ${warningsList}
                </div>
            `;
        }
        
        return panel;
    }
    
    /**
     * Create tsunami warning markers on map
     */
    addTsunamiWarningMarkers(map, epicenter, warnings) {
        // Clear previous markers
        this.warningMarkers.forEach(marker => map.removeLayer(marker));
        this.warningMarkers = [];
        
        if (warnings.length === 0) return;
        
        // Add affected region circles
        for (const warning of warnings) {
            const circle = L.circle(
                [warning.lat, warning.lon] || [0, 0],  // Would need actual region coords
                {
                    radius: warning.distance_km * 1000, // Convert to meters
                    color: this.getWarningColor(warning.warning_level),
                    weight: 2,
                    opacity: 0.3,
                    fillColor: this.getWarningColor(warning.warning_level),
                    fillOpacity: 0.1
                }
            );
            
            circle.bindPopup(`
                <div style="font-size: 12px; color: white;">
                    <strong>${warning.region}</strong><br>
                    ${this.getWarningDescription(warning.warning_level)}<br>
                    Wave height: ${warning.wave_height_m}m<br>
                    Arrival: ${warning.arrival_time_formatted}
                </div>
            `);
            
            circle.addTo(map);
            this.warningMarkers.push(circle);
        }
        
        // Add tsunami wave propagation visualization
        this.addTsunamiPropagation(map, epicenter, warnings);
    }
    
    /**
     * Add animated tsunami wave propagation
     */
    addTsunamiPropagation(map, epicenter, warnings) {
        if (!epicenter) return;
        
        const maxDistance = Math.max(...warnings.map(w => w.distance_km), 500);
        
        // Add concentric circles showing wave travel
        for (let time = 0; time <= 6; time++) {
            const distance = (time * 133); // km (800 km/h tsunami speed / 6 circles)
            
            if (distance > maxDistance) break;
            
            const circle = L.circle(
                [epicenter.lat, epicenter.lon],
                {
                    radius: distance * 1000,
                    color: '#3B82F6',
                    weight: 1,
                    opacity: 0.2 - (time * 0.03),
                    fill: false,
                    dashArray: '5, 5'
                }
            );
            
            circle.addTo(map);
            this.warningMarkers.push(circle);
        }
    }
    
    /**
     * Add tsunami warning panel to page
     */
    showWarningPanel(tsunamiData, quakeData) {
        let panel = document.getElementById('tsunamiPanel');
        
        if (!panel) {
            panel = document.createElement('div');
            panel.id = 'tsunamiPanel';
            document.body.appendChild(panel);
        }
        
        panel.innerHTML = '';
        const warningPanel = this.displayTsunamiWarning(quakeData, tsunamiData);
        panel.appendChild(warningPanel);
        
        // Style the panel
        if (!panel.style.cssText) {
            panel.style.cssText = `
                position: fixed;
                top: 80px;
                right: 20px;
                width: 360px;
                max-width: calc(100vw - 40px);
                background: #0f172a;
                border: 2px solid #334155;
                border-radius: 12px;
                padding: 16px;
                z-index: 1001;
                box-shadow: 0 20px 50px rgba(0, 0, 0, 0.5);
                font-size: 13px;
                max-height: 60vh;
                overflow-y: auto;
            `;
        }
    }
    
    /**
     * Clear all tsunami warnings from display
     */
    clearWarnings(map) {
        this.warningMarkers.forEach(marker => map.removeLayer(marker));
        this.warningMarkers = [];
        
        const panel = document.getElementById('tsunamiPanel');
        if (panel) {
            panel.remove();
        }
    }
}

// Initialize global tsunami warning display
const tsunamiDisplay = new TsunamiWarningDisplay();
