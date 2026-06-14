/**
 * Intensity Viewer System - Simple Working Version
 */

class IntensityViewer {
    static MMI_COLORS = {
        1: "#ffffff", 2: "#ccccff", 3: "#99ccff", 4: "#66ccff", 5: "#00ccff",
        6: "#ffff00", 7: "#ffcc00", 8: "#ff9900", 9: "#ff6600", 10: "#ff3300",
        11: "#ff0000", 12: "#cc0000"
    };

    static async displayIntensity(quake) {
        const mag = quake.properties.mag || 0;
        const depth = quake.geometry.coordinates[2] || 0;
        const lat = quake.geometry.coordinates[1];
        const lon = quake.geometry.coordinates[0];

        try {
            const response = await fetch('/api/intensity/mmi-shindo', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ magnitude: mag, depth_km: depth, latitude: lat, longitude: lon, distance_km: 0.1 })
            });

            if (!response.ok) return;
            const data = await response.json();

            const panel = document.getElementById('tsunamiPanelContent');
            if (!panel) return;

            const mmiColor = this.MMI_COLORS[Math.round(data.mmi.value)] || '#ffffff';
            const html = `
                <div style="background: #111827; border-left: 4px solid ${mmiColor}; padding: 12px; border-radius: 8px; margin-bottom: 12px;">
                    <div style="color: ${mmiColor}; font-weight: bold; margin-bottom: 8px;">📊 Intensity Analysis</div>
                    <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 10px; font-size: 12px; margin-bottom: 8px;">
                        <div><strong>MMI:</strong> ${data.mmi.value} (${data.mmi.scale})</div>
                        <div><strong>Shindo:</strong> ${data.shindo.value} (${data.shindo.scale})</div>
                    </div>
                    <div style="font-size: 11px; color: #94a3b8;">Fault: ${data.fault_type}</div>
                </div>
            `;
            panel.innerHTML = html + panel.innerHTML;
        } catch (err) {
            console.log('Intensity fetch error:', err);
        }
    }
}

// Expose globally
window.IntensityViewer = IntensityViewer;
